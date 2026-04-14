import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter


class PlanterRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, planter: Planter) -> Planter:
        self.db.add(planter)
        await self.db.flush()
        await self.db.refresh(planter)
        return planter

    async def get_by_id(self, planter_id: uuid.UUID) -> Planter | None:
        result = await self.db.execute(
            select(Planter).where(
                Planter.id == planter_id,
                Planter.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_recent(
        self,
        limit: int = 20,
        cursor_created_at: datetime | None = None,
        cursor_id: uuid.UUID | None = None,
    ) -> list[Planter]:
        stmt = (
            select(Planter)
            .where(
                Planter.deleted_at.is_(None),
                Planter.status != "archived",
            )
            .order_by(Planter.created_at.desc(), Planter.id.desc())
            .limit(limit)
        )

        if cursor_created_at is not None and cursor_id is not None:
            # Use native UUID comparison (works for both PostgreSQL and SQLite)
            # Both store UUIDs as binary, and binary comparison preserves order
            stmt = stmt.where(
                or_(
                    Planter.created_at < cursor_created_at,
                    and_(
                        Planter.created_at == cursor_created_at,
                        Planter.id < cursor_id,
                    ),
                )
            )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_scores(
        self,
        planter_id: uuid.UUID,
        *,
        structure_fulfillment: float,
        maturity_score: float | None,
        progress: float,
        status: str,
    ) -> None:
        await self.db.execute(
            update(Planter)
            .where(Planter.id == planter_id)
            .values(
                structure_fulfillment=structure_fulfillment,
                maturity_score=maturity_score,
                progress=progress,
                status=status,
            )
        )
        await self.db.flush()

    async def increment_log_count(self, planter_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Planter)
            .where(Planter.id == planter_id)
            .values(log_count=Planter.log_count + 1)
        )
        await self.db.flush()

    async def update_contributor_count(self, planter_id: uuid.UUID, count: int) -> None:
        await self.db.execute(
            update(Planter)
            .where(Planter.id == planter_id)
            .values(contributor_count=count)
        )
        await self.db.flush()
