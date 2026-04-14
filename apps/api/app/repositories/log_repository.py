import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log


class LogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, log: Log) -> Log:
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> Log | None:
        result = await self.db.execute(
            select(Log).where(Log.id == log_id, Log.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_by_planter(
        self,
        planter_id: uuid.UUID,
        limit: int = 20,
        cursor_created_at: datetime | None = None,
        cursor_id: uuid.UUID | None = None,
    ) -> list[Log]:
        stmt = (
            select(Log)
            .where(
                Log.planter_id == planter_id,
                Log.deleted_at.is_(None),
                Log.parent_log_id.is_(None),
            )
            .order_by(Log.created_at.asc(), Log.id.asc())
            .limit(limit)
        )

        if cursor_created_at is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    Log.created_at > cursor_created_at,
                    and_(
                        Log.created_at == cursor_created_at,
                        Log.id > cursor_id,
                    ),
                )
            )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_replies(self, parent_log_ids: list[uuid.UUID]) -> list[Log]:
        if not parent_log_ids:
            return []
        result = await self.db.execute(
            select(Log)
            .where(
                Log.parent_log_id.in_(parent_log_ids),
                Log.deleted_at.is_(None),
            )
            .order_by(Log.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_by_planter(self, planter_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Log)
            .where(Log.planter_id == planter_id, Log.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def count_contributors(self, planter_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Log.user_id)))
            .select_from(Log)
            .where(
                Log.planter_id == planter_id,
                Log.deleted_at.is_(None),
                Log.user_id.is_not(None),
            )
        )
        return result.scalar_one()

    async def count_user_logs_since(
        self, planter_id: uuid.UUID, since_log_id: uuid.UUID
    ) -> int:
        # Get the created_at of the reference log
        ref_result = await self.db.execute(
            select(Log.created_at).where(Log.id == since_log_id)
        )
        ref_created_at = ref_result.scalar_one_or_none()
        if ref_created_at is None:
            return 0

        result = await self.db.execute(
            select(func.count())
            .select_from(Log)
            .where(
                Log.planter_id == planter_id,
                Log.deleted_at.is_(None),
                Log.user_id.is_not(None),
                Log.is_ai_generated.is_(False),
                Log.created_at > ref_created_at,
            )
        )
        return result.scalar_one()

    async def get_all_by_planter(self, planter_id: uuid.UUID) -> list[Log]:
        result = await self.db.execute(
            select(Log)
            .where(Log.planter_id == planter_id, Log.deleted_at.is_(None))
            .order_by(Log.created_at.asc())
        )
        return list(result.scalars().all())
