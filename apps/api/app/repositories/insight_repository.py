import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import InsightScoreEvent
from app.models.user import User


class InsightScoreRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_events(self, events: list[InsightScoreEvent]) -> None:
        for event in events:
            self.db.add(event)
        await self.db.flush()

    async def get_by_planter(self, planter_id: uuid.UUID) -> list[InsightScoreEvent]:
        result = await self.db.execute(
            select(InsightScoreEvent)
            .where(InsightScoreEvent.planter_id == planter_id)
            .order_by(InsightScoreEvent.score_delta.desc())
        )
        return list(result.scalars().all())

    async def update_user_scores(
        self, user_deltas: dict[uuid.UUID, float]
    ) -> None:
        for user_id, delta in user_deltas.items():
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(insight_score=User.insight_score + delta)
            )
        await self.db.flush()
