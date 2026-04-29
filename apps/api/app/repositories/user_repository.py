import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, and_, case, cast, distinct, func, literal_column, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.tag import Tag, UserTag
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID, excluding deleted/banned users (BR-U08)."""
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None),
                User.is_banned == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_louge_count(self, user_id: uuid.UUID) -> int:
        """Count distinct louges where user has insight_score > 0 (D9)."""
        # Distinct planter_ids from insight_score_events
        # where score_delta > 0 and planter status = 'louge'
        subq = (
            select(distinct(InsightScoreEvent.planter_id))
            .join(Planter, InsightScoreEvent.planter_id == Planter.id)
            .where(
                InsightScoreEvent.user_id == user_id,
                InsightScoreEvent.score_delta > 0,
                Planter.status == "louge",
                Planter.deleted_at.is_(None),
            )
        ).subquery()

        result = await self.db.execute(
            select(func.count()).select_from(subq)
        )
        return result.scalar_one()

    async def get_featured_contribution(
        self, user_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get the planter with highest total insight score for this user."""
        result = await self.db.execute(
            select(
                InsightScoreEvent.planter_id,
                Planter.title.label("planter_title"),
                Planter.status.label("planter_status"),
                func.sum(InsightScoreEvent.score_delta).label("total_score"),
            )
            .join(Planter, InsightScoreEvent.planter_id == Planter.id)
            .where(
                InsightScoreEvent.user_id == user_id,
                Planter.status == "louge",
                Planter.deleted_at.is_(None),
            )
            .group_by(InsightScoreEvent.planter_id, Planter.title, Planter.status)
            .order_by(func.sum(InsightScoreEvent.score_delta).desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        return {
            "planter_id": row.planter_id,
            "planter_title": row.planter_title,
            "planter_status": row.planter_status,
            "total_score": row.total_score,
        }

    async def get_contribution_graph(
        self, user_id: uuid.UUID, tz: str = "UTC"
    ) -> list[dict[str, Any]]:
        """Get daily contribution counts (seeds + logs) for past 365 days (D8)."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=365)

        # For SQLite compatibility, use date() directly; PostgreSQL would use AT TIME ZONE
        seed_dates = (
            select(
                func.date(Planter.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(
                Planter.user_id == user_id,
                Planter.created_at >= start_date,
                Planter.deleted_at.is_(None),
            )
            .group_by(func.date(Planter.created_at))
        )

        log_dates = (
            select(
                func.date(Log.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(
                Log.user_id == user_id,
                Log.created_at >= start_date,
                Log.deleted_at.is_(None),
            )
            .group_by(func.date(Log.created_at))
        )

        # Union and aggregate
        combined = union_all(seed_dates, log_dates).subquery()
        result = await self.db.execute(
            select(
                combined.c.day,
                func.sum(combined.c.cnt).label("count"),
            )
            .group_by(combined.c.day)
            .order_by(combined.c.day)
        )

        return [
            {"date": _parse_date(row.day), "count": int(row.count)}
            for row in result.all()
        ]

    async def get_user_planters(
        self,
        user_id: uuid.UUID,
        tab: str = "seeds",
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Planter], str | None]:
        """Get planters for user profile tabs."""
        if tab == "louges":
            return await self._get_user_louge_planters(user_id, limit, cursor)

        # tab=seeds: all planters authored by user
        query = (
            select(Planter)
            .where(
                Planter.user_id == user_id,
                Planter.deleted_at.is_(None),
            )
            .order_by(Planter.created_at.desc())
        )

        if cursor:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Planter.created_at < cursor_dt)

        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        planters = list(result.scalars().all())

        next_cursor = None
        if len(planters) > limit:
            planters = planters[:limit]
            next_cursor = planters[-1].created_at.isoformat()

        return planters, next_cursor

    async def _get_user_louge_planters(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Planter], str | None]:
        """Get louges where user contributed with insight_score > 0 (D9)."""
        # Get planter IDs from insight_score_events
        planter_ids_subq = (
            select(distinct(InsightScoreEvent.planter_id))
            .join(Planter, InsightScoreEvent.planter_id == Planter.id)
            .where(
                InsightScoreEvent.user_id == user_id,
                InsightScoreEvent.score_delta > 0,
                Planter.status == "louge",
                Planter.deleted_at.is_(None),
            )
        ).subquery()

        query = (
            select(Planter)
            .where(Planter.id.in_(select(planter_ids_subq)))
            .order_by(Planter.created_at.desc())
        )

        if cursor:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Planter.created_at < cursor_dt)

        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        planters = list(result.scalars().all())

        next_cursor = None
        if len(planters) > limit:
            planters = planters[:limit]
            next_cursor = planters[-1].created_at.isoformat()

        return planters, next_cursor

    async def get_user_logs(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Get logs authored by user with planter info."""
        query = (
            select(
                Log.id,
                Log.body,
                Log.created_at,
                Log.planter_id,
                Planter.title.label("planter_title"),
                Planter.status.label("planter_status"),
            )
            .join(Planter, Log.planter_id == Planter.id)
            .where(
                Log.user_id == user_id,
                Log.deleted_at.is_(None),
            )
            .order_by(Log.created_at.desc())
        )

        if cursor:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Log.created_at < cursor_dt)

        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        rows = result.all()

        logs = [
            {
                "id": row.id,
                "body": row.body,
                "created_at": row.created_at,
                "planter_id": row.planter_id,
                "planter_title": row.planter_title,
                "planter_status": row.planter_status,
            }
            for row in rows[:limit]
        ]

        next_cursor = None
        if len(rows) > limit:
            next_cursor = logs[-1]["created_at"].isoformat()

        return logs, next_cursor

    async def get_similar_users(
        self,
        user_id: uuid.UUID,
        exclude_user_ids: list[uuid.UUID],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get users with common tags, sorted by shared tag count (D11)."""
        # Get tags for the target user
        user_tags_subq = (
            select(UserTag.tag_id)
            .where(UserTag.user_id == user_id)
        ).subquery()

        # Find other users who share these tags
        exclude_ids = [user_id] + exclude_user_ids
        query = (
            select(
                UserTag.user_id,
                func.count(UserTag.tag_id).label("common_tag_count"),
            )
            .where(
                UserTag.tag_id.in_(select(user_tags_subq)),
                UserTag.user_id.not_in(exclude_ids),
            )
            .join(User, UserTag.user_id == User.id)
            .where(
                User.is_banned == False,  # noqa: E712
                User.deleted_at.is_(None),
            )
            .group_by(UserTag.user_id)
            .order_by(func.count(UserTag.tag_id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        similar = []
        for row in rows:
            user_result = await self.db.execute(
                select(User).where(User.id == row.user_id)
            )
            user = user_result.scalar_one()
            similar.append({
                "user_id": user.id,
                "display_name": user.display_name,
                "headline": user.headline,
                "avatar_url": user.avatar_url,
                "insight_score": user.insight_score,
                "common_tag_count": row.common_tag_count,
            })

        return similar


def _parse_date(value: Any) -> date:
    """Parse a date from various formats (SQLite returns string, PG returns date)."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value
