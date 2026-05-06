"""Public platform stats for the right-sidebar About card.

Exposes aggregate counts of seeds (planters), louges (bloomed planters),
and contributors (distinct users who have authored at least one planter
or non-hidden log). No authentication required.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.log import Log
from app.models.planter import Planter

router = APIRouter(tags=["stats"])


class PublicStatsResponse(BaseModel):
    seeds: int
    louges: int
    contributors: int


@router.get("/stats", response_model=PublicStatsResponse)
async def get_public_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicStatsResponse:
    seeds_q = (
        select(func.count())
        .select_from(Planter)
        .where(Planter.deleted_at.is_(None))
    )
    louges_q = (
        select(func.count())
        .select_from(Planter)
        .where(Planter.deleted_at.is_(None), Planter.status == "louge")
    )

    planter_authors = select(Planter.user_id).where(Planter.deleted_at.is_(None))
    log_authors = select(Log.user_id).where(
        Log.deleted_at.is_(None),
        Log.is_hidden.is_(False),
        Log.user_id.is_not(None),
    )
    contributors_subq = union(planter_authors, log_authors).subquery()
    contributors_q = select(func.count()).select_from(contributors_subq)

    seeds = (await db.execute(seeds_q)).scalar_one()
    louges = (await db.execute(louges_q)).scalar_one()
    contributors = (await db.execute(contributors_q)).scalar_one()

    return PublicStatsResponse(
        seeds=int(seeds),
        louges=int(louges),
        contributors=int(contributors),
    )
