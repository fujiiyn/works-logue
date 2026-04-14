import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.log import Log
from app.models.planter import Planter
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.log_repository import LogRepository
from app.repositories.planter_repository import PlanterRepository
from app.repositories.score_repository import ScoreRepository
from app.schemas.log import (
    LogCreate,
    LogCreateResponse,
    LogResponse,
    LogWithRepliesResponse,
)
from app.schemas.score import PlanterScoreResponse, StructurePartsResponse
from app.schemas.user import UserPublicResponse

router = APIRouter(tags=["logs"])


def _build_log_response(log: Log, user: User | None) -> LogResponse:
    user_resp = UserPublicResponse.model_validate(user) if user else None
    return LogResponse(
        id=log.id,
        planter_id=log.planter_id,
        user=user_resp,
        body=log.body,
        parent_log_id=log.parent_log_id,
        is_ai_generated=log.is_ai_generated,
        created_at=log.created_at,
    )


def _build_planter_score_response(
    planter: Planter,
    structure_parts: dict | None,
) -> PlanterScoreResponse:
    parts_resp = None
    if structure_parts:
        parts_resp = StructurePartsResponse(
            context=structure_parts.get("context", False),
            problem=structure_parts.get("problem", False),
            solution=structure_parts.get("solution", False),
            name=structure_parts.get("name", False),
        )
    return PlanterScoreResponse(
        id=planter.id,
        status=planter.status,
        log_count=planter.log_count,
        contributor_count=planter.contributor_count,
        progress=planter.progress,
        structure_fulfillment=planter.structure_fulfillment,
        maturity_score=planter.maturity_score,
        structure_parts=parts_resp,
    )


@router.post(
    "/planters/{planter_id}/logs",
    response_model=LogCreateResponse,
    status_code=201,
)
async def create_log(
    planter_id: uuid.UUID,
    body: LogCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogCreateResponse:
    planter_repo = PlanterRepository(db)
    planter = await planter_repo.get_by_id(planter_id)
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")

    if planter.status == "louge":
        raise HTTPException(status_code=400, detail="planter_already_bloomed")

    # Validate parent_log_id
    log_repo = LogRepository(db)
    if body.parent_log_id is not None:
        parent_log = await log_repo.get_by_id(body.parent_log_id)
        if parent_log is None or parent_log.planter_id != planter_id:
            raise HTTPException(status_code=400, detail="invalid_parent_log")
        if parent_log.parent_log_id is not None:
            raise HTTPException(status_code=400, detail="nested_reply_not_allowed")

    # Create log
    log = Log(
        planter_id=planter_id,
        user_id=current_user.id,
        body=body.body.strip(),
        parent_log_id=body.parent_log_id,
        is_ai_generated=False,
    )
    log = await log_repo.create(log)

    # Update planter stats
    await planter_repo.increment_log_count(planter_id)
    contributor_count = await log_repo.count_contributors(planter_id)
    await planter_repo.update_contributor_count(planter_id, contributor_count)

    # Transition seed -> sprout on first log
    if planter.status == "seed":
        from sqlalchemy import update as sa_update

        await db.execute(
            sa_update(Planter)
            .where(Planter.id == planter_id)
            .values(status="sprout")
        )
        await db.flush()

    await db.commit()

    # Refresh planter to get updated stats
    await db.refresh(planter)

    # Get latest snapshot for structure_parts
    score_repo = ScoreRepository(db)
    snapshot = await score_repo.get_latest_snapshot(planter_id)
    structure_parts = snapshot.structure_parts if snapshot else None

    # Auto-follow
    follow_repo = FollowRepository(db)
    await follow_repo.follow_planter(current_user.id, planter_id)
    await db.commit()

    # Schedule background score pipeline
    background_tasks.add_task(_run_score_pipeline, planter_id, log.id)

    log_resp = _build_log_response(log, current_user)
    planter_score = _build_planter_score_response(planter, structure_parts)

    return LogCreateResponse(
        log=log_resp,
        planter=planter_score,
        score_pending=True,
    )


async def _run_score_pipeline(planter_id: uuid.UUID, trigger_log_id: uuid.UUID) -> None:
    from app.database import async_session
    from app.pipelines.score_pipeline import ScorePipeline

    pipeline = ScorePipeline()
    async with async_session() as db:
        await pipeline.execute(planter_id, trigger_log_id, db)


@router.get(
    "/planters/{planter_id}/logs",
    response_model=dict,
)
async def list_logs(
    planter_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
) -> dict:
    # Verify planter exists
    planter_repo = PlanterRepository(db)
    planter = await planter_repo.get_by_id(planter_id)
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")

    log_repo = LogRepository(db)

    from app.schemas.planter import CursorPaginatedResponse

    cursor_created_at = None
    cursor_id = None
    if cursor:
        cursor_created_at, cursor_id = CursorPaginatedResponse.decode_cursor(cursor)

    top_logs = await log_repo.list_by_planter(
        planter_id,
        limit=limit + 1,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )

    has_next = len(top_logs) > limit
    if has_next:
        top_logs = top_logs[:limit]

    # Load replies for top-level logs
    top_log_ids = [log.id for log in top_logs]
    replies = await log_repo.list_replies(top_log_ids)

    # Load users
    all_logs = top_logs + replies
    user_ids = list({log.user_id for log in all_logs if log.user_id})
    users_map: dict[uuid.UUID, User] = {}
    if user_ids:
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u for u in result.scalars().all()}

    # Group replies by parent
    replies_map: dict[uuid.UUID, list[LogResponse]] = {}
    for reply in replies:
        parent_id = reply.parent_log_id
        if parent_id not in replies_map:
            replies_map[parent_id] = []
        replies_map[parent_id].append(
            _build_log_response(reply, users_map.get(reply.user_id))
        )

    items = [
        LogWithRepliesResponse(
            id=log.id,
            planter_id=log.planter_id,
            user=UserPublicResponse.model_validate(users_map[log.user_id])
            if log.user_id and log.user_id in users_map
            else None,
            body=log.body,
            is_ai_generated=log.is_ai_generated,
            created_at=log.created_at,
            replies=replies_map.get(log.id, []),
        )
        for log in top_logs
    ]

    next_cursor = None
    if has_next and top_logs:
        last = top_logs[-1]
        next_cursor = CursorPaginatedResponse.encode_cursor(last.created_at, last.id)

    return {"items": items, "next_cursor": next_cursor, "has_next": has_next}
