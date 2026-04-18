import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.planter_view import PlanterView
from app.models.tag import PlanterTag


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

    async def update_louge_content(
        self, planter_id: uuid.UUID, content: str, generated_at: datetime
    ) -> None:
        await self.db.execute(
            update(Planter)
            .where(Planter.id == planter_id)
            .values(louge_content=content, louge_generated_at=generated_at)
        )
        await self.db.flush()

    async def list_trending_candidates(
        self, window_days: int = 7, limit: int = 50
    ) -> list[Planter]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Planters created recently OR that have recent log activity
        recent_log_planter_ids = (
            select(Log.planter_id)
            .where(Log.created_at >= cutoff, Log.deleted_at.is_(None))
            .distinct()
            .scalar_subquery()
        )

        stmt = (
            select(Planter)
            .where(
                Planter.deleted_at.is_(None),
                Planter.status != "archived",
                or_(
                    Planter.created_at >= cutoff,
                    Planter.id.in_(recent_log_planter_ids),
                ),
            )
            .order_by(Planter.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_bloomed(
        self,
        limit: int = 20,
        cursor_louge_generated_at: datetime | None = None,
        cursor_id: uuid.UUID | None = None,
    ) -> list[Planter]:
        stmt = (
            select(Planter)
            .where(
                Planter.deleted_at.is_(None),
                Planter.status == "louge",
                Planter.louge_generated_at.is_not(None),
            )
            .order_by(Planter.louge_generated_at.desc(), Planter.id.desc())
            .limit(limit)
        )

        if cursor_louge_generated_at is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    Planter.louge_generated_at < cursor_louge_generated_at,
                    and_(
                        Planter.louge_generated_at == cursor_louge_generated_at,
                        Planter.id < cursor_id,
                    ),
                )
            )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        keyword: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        status: str | None = None,
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
        )

        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    Planter.title.ilike(pattern),
                    Planter.body.ilike(pattern),
                )
            )

        if tag_ids:
            stmt = (
                stmt.join(PlanterTag, PlanterTag.planter_id == Planter.id)
                .where(PlanterTag.tag_id.in_(tag_ids))
                .group_by(Planter.id)
                .having(func.count(func.distinct(PlanterTag.tag_id)) == len(tag_ids))
            )

        if status:
            stmt = stmt.where(Planter.status == status)

        stmt = stmt.order_by(Planter.created_at.desc(), Planter.id.desc()).limit(limit)

        if cursor_created_at is not None and cursor_id is not None:
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

    async def get_view_counts(
        self, planter_ids: list[uuid.UUID], since: datetime
    ) -> dict[uuid.UUID, int]:
        if not planter_ids:
            return {}

        stmt = (
            select(PlanterView.planter_id, func.count().label("cnt"))
            .where(
                PlanterView.planter_id.in_(planter_ids),
                PlanterView.viewed_at >= since,
            )
            .group_by(PlanterView.planter_id)
        )

        result = await self.db.execute(stmt)
        return {row.planter_id: row.cnt for row in result.all()}

    VIEW_DEDUP_MINUTES = 10

    async def record_view(
        self,
        planter_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)

        if user_id:
            # Logged-in: UPSERT by (user_id, planter_id)
            stmt = select(PlanterView).where(
                PlanterView.planter_id == planter_id,
                PlanterView.user_id == user_id,
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.viewed_at = now
            else:
                self.db.add(PlanterView(
                    planter_id=planter_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    viewed_at=now,
                ))
        elif ip_address:
            # Anonymous: deduplicate by IP within time window
            cutoff = now - timedelta(minutes=self.VIEW_DEDUP_MINUTES)
            stmt = select(PlanterView).where(
                PlanterView.planter_id == planter_id,
                PlanterView.ip_address == ip_address,
                PlanterView.user_id.is_(None),
                PlanterView.viewed_at >= cutoff,
            )
            result = await self.db.execute(stmt)
            recent = result.scalar_one_or_none()

            if not recent:
                self.db.add(PlanterView(
                    planter_id=planter_id,
                    ip_address=ip_address,
                    viewed_at=now,
                ))

        await self.db.flush()
