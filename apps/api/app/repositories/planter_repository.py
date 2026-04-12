import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
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
