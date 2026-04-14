import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import LougeScoreSnapshot


class ScoreRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_snapshot(self, snapshot: LougeScoreSnapshot) -> LougeScoreSnapshot:
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(self, planter_id: uuid.UUID) -> LougeScoreSnapshot | None:
        result = await self.db.execute(
            select(LougeScoreSnapshot)
            .where(LougeScoreSnapshot.planter_id == planter_id)
            .order_by(LougeScoreSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
