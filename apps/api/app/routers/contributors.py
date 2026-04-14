import uuid
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.log import Log
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.user import User
from app.schemas.contributor import ContributorResponse, ContributorsListResponse

router = APIRouter(tags=["contributors"])


@router.get(
    "/planters/{planter_id}/contributors",
    response_model=ContributorsListResponse,
)
async def get_contributors(
    planter_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
) -> ContributorsListResponse:
    # Get planter and verify it's bloomed
    result = await db.execute(
        select(Planter).where(
            Planter.id == planter_id,
            Planter.deleted_at.is_(None),
        )
    )
    planter = result.scalar_one_or_none()
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")
    if planter.status != "louge":
        raise HTTPException(status_code=404, detail="planter_not_bloomed")

    # Get insight score events for this planter
    events_result = await db.execute(
        select(InsightScoreEvent).where(
            InsightScoreEvent.planter_id == planter_id
        )
    )
    events = list(events_result.scalars().all())

    if not events:
        return ContributorsListResponse(contributors=[])

    # Aggregate scores per user
    user_scores: dict[uuid.UUID, float] = defaultdict(float)
    user_is_seed_author: dict[uuid.UUID, bool] = defaultdict(lambda: False)
    for event in events:
        user_scores[event.user_id] += event.score_delta
        if event.reason == "seed_author":
            user_is_seed_author[event.user_id] = True

    # Get user details
    user_ids = list(user_scores.keys())
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    # Get log counts per user for this planter
    log_counts_result = await db.execute(
        select(Log.user_id, func.count(Log.id))
        .where(
            Log.planter_id == planter_id,
            Log.deleted_at.is_(None),
            Log.is_ai_generated.is_(False),
        )
        .group_by(Log.user_id)
    )
    log_counts: dict[uuid.UUID, int] = {
        row[0]: row[1] for row in log_counts_result.all() if row[0] is not None
    }

    # Build response sorted by score descending
    contributors = []
    for user_id in sorted(user_scores, key=lambda uid: user_scores[uid], reverse=True):
        user = users_map.get(user_id)
        if user is None:
            continue
        contributors.append(
            ContributorResponse(
                user_id=user.id,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                insight_score_earned=user_scores[user_id],
                log_count=log_counts.get(user_id, 0),
                is_seed_author=user_is_seed_author[user_id],
            )
        )

    return ContributorsListResponse(contributors=contributors)
