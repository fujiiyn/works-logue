import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import PlanterFollow


class FollowRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def follow_planter(self, user_id: uuid.UUID, planter_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == user_id,
                PlanterFollow.planter_id == planter_id,
            )
        )
        if result.scalar_one_or_none() is not None:
            return
        self.db.add(PlanterFollow(user_id=user_id, planter_id=planter_id))
        await self.db.flush()
