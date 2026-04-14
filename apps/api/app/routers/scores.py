import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.user import User
from app.repositories.log_repository import LogRepository
from app.repositories.planter_repository import PlanterRepository
from app.repositories.score_repository import ScoreRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.score import (
    PlanterScoreResponse,
    PlanterScoreWithPendingResponse,
    ScoreSettingsResponse,
    StructurePartsResponse,
)

router = APIRouter(tags=["scores"])


@router.get(
    "/planters/{planter_id}/score",
    response_model=PlanterScoreWithPendingResponse,
)
async def get_planter_score(
    planter_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
) -> PlanterScoreWithPendingResponse:
    planter_repo = PlanterRepository(db)
    planter = await planter_repo.get_by_id(planter_id)
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")

    score_repo = ScoreRepository(db)
    snapshot = await score_repo.get_latest_snapshot(planter_id)

    # Determine score_pending
    log_repo = LogRepository(db)
    log_count = await log_repo.count_by_planter(planter_id)

    if snapshot is None:
        score_pending = log_count > 0
        last_scored_at = None
    else:
        last_scored_at = snapshot.created_at
        if snapshot.trigger_log_id is not None:
            user_logs_since = await log_repo.count_user_logs_since(
                planter_id, snapshot.trigger_log_id
            )
            score_pending = user_logs_since > 0
        else:
            score_pending = log_count > 0

    # Build structure_parts
    structure_parts = None
    if snapshot and snapshot.structure_parts:
        structure_parts = StructurePartsResponse(
            context=snapshot.structure_parts.get("context", False),
            problem=snapshot.structure_parts.get("problem", False),
            solution=snapshot.structure_parts.get("solution", False),
            name=snapshot.structure_parts.get("name", False),
        )

    score_resp = PlanterScoreResponse(
        id=planter.id,
        status=planter.status,
        log_count=planter.log_count,
        contributor_count=planter.contributor_count,
        progress=planter.progress,
        structure_fulfillment=planter.structure_fulfillment,
        maturity_score=planter.maturity_score,
        structure_parts=structure_parts,
    )

    return PlanterScoreWithPendingResponse(
        score=score_resp,
        score_pending=score_pending,
        last_scored_at=last_scored_at,
    )


@router.get(
    "/settings/score",
    response_model=ScoreSettingsResponse,
)
async def get_score_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScoreSettingsResponse:
    settings_repo = SettingsRepository(db)
    settings = await settings_repo.get_score_settings()
    return ScoreSettingsResponse(
        min_contributors=int(settings["min_contributors"]),
        min_logs=int(settings["min_logs"]),
        bloom_threshold=float(settings["bloom_threshold"]),
        bud_threshold=float(settings["bud_threshold"]),
    )
