"""U7 Step 5: AdminRepository.

Thin wrapper over UserRepository / PlanterRepository, with admin-only
aggregation and search. SQL is portable across PostgreSQL and the SQLite
test backend; JST "today" is computed in Python rather than via
`func.timezone(...)` because SQLite has no equivalent.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User

JST = timezone(timedelta(hours=9))
MAX_PER_PAGE = 100


def _q_pattern(q: str) -> str:
    """Build an ILIKE pattern from a raw user query, trimmed and lowercased."""
    return f"%{q.strip().lower()}%"


def _today_start_utc_jst(now: datetime | None = None) -> datetime:
    """Today-00:00 (JST) as a UTC-aware datetime.

    Used to build the "new_planters_today" window without relying on
    PostgreSQL-specific timezone functions, so the same code runs on the
    SQLite test backend. `now` is injectable for deterministic tests.
    """
    base = (now or datetime.now(JST)).astimezone(JST)
    sod_jst = base.replace(hour=0, minute=0, second=0, microsecond=0)
    return sod_jst.astimezone(UTC)


class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Dashboard stats ----------------------------------------------------

    async def get_dashboard_stats(
        self, *, now: datetime | None = None
    ) -> dict[str, int]:
        # `now` is injectable so tests can pin the JST window without flake.
        today_start = _today_start_utc_jst(now)

        total_users_q = select(func.count()).select_from(User).where(
            User.deleted_at.is_(None)
        )
        total_planters_q = select(func.count()).select_from(Planter).where(
            Planter.deleted_at.is_(None)
        )
        new_today_q = (
            select(func.count())
            .select_from(Planter)
            .where(
                Planter.deleted_at.is_(None),
                Planter.created_at >= today_start,
            )
        )
        # MVP: pending_louge_count := all sprouts (ignoring U4 maturity threshold).
        pending_q = (
            select(func.count())
            .select_from(Planter)
            .where(
                Planter.deleted_at.is_(None),
                Planter.status == "sprout",
            )
        )

        total_users = (await self.db.execute(total_users_q)).scalar_one()
        total_planters = (await self.db.execute(total_planters_q)).scalar_one()
        new_today = (await self.db.execute(new_today_q)).scalar_one()
        pending = (await self.db.execute(pending_q)).scalar_one()

        return {
            "total_users": int(total_users),
            "total_planters": int(total_planters),
            "new_planters_today": int(new_today),
            "pending_louge_count": int(pending),
        }

    # ---- Users --------------------------------------------------------------

    async def list_users(
        self,
        q: str | None,
        status: str,
        page: int,
        per_page: int,
    ) -> tuple[list[dict[str, Any]], int]:
        per_page = max(1, min(per_page, MAX_PER_PAGE))
        page = max(1, page)
        offset = (page - 1) * per_page

        base = select(User).where(User.deleted_at.is_(None))
        if status == "normal":
            base = base.where(User.is_banned == False)  # noqa: E712
        elif status == "banned":
            base = base.where(User.is_banned == True)  # noqa: E712

        if q is not None and q.strip():
            base = base.where(User.display_name.ilike(_q_pattern(q)))

        total_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(total_q)).scalar_one())

        page_q = (
            base.order_by(User.created_at.desc(), User.id.desc())
            .limit(per_page)
            .offset(offset)
        )
        rows = (await self.db.execute(page_q)).scalars().all()
        if not rows:
            return [], total

        ids = [u.id for u in rows]

        # Aggregate planter_count and log_count in two queries (N+1 avoidance).
        planter_counts_q = (
            select(Planter.user_id, func.count().label("cnt"))
            .where(
                Planter.user_id.in_(ids),
                Planter.deleted_at.is_(None),
            )
            .group_by(Planter.user_id)
        )
        log_counts_q = (
            select(Log.user_id, func.count().label("cnt"))
            .where(
                Log.user_id.in_(ids),
                Log.deleted_at.is_(None),
            )
            .group_by(Log.user_id)
        )

        planter_counts = {
            r.user_id: int(r.cnt)
            for r in (await self.db.execute(planter_counts_q)).all()
        }
        log_counts = {
            r.user_id: int(r.cnt)
            for r in (await self.db.execute(log_counts_q)).all()
        }

        items = [
            {
                "id": u.id,
                "display_name": u.display_name,
                "avatar_url": u.avatar_url,
                "role": u.role,
                "is_banned": u.is_banned,
                "banned_at": u.banned_at,
                "ban_reason": u.ban_reason,
                "planter_count": planter_counts.get(u.id, 0),
                "log_count": log_counts.get(u.id, 0),
                "created_at": u.created_at,
            }
            for u in rows
        ]
        return items, total

    async def ban_user(self, user: User, reason: str | None) -> None:
        if user.is_banned:
            return  # idempotent
        user.is_banned = True
        user.banned_at = datetime.now(UTC)
        user.ban_reason = reason
        await self.db.flush()

    async def unban_user(self, user: User) -> None:
        if not user.is_banned and user.banned_at is None and user.ban_reason is None:
            return  # idempotent
        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None
        await self.db.flush()

    # ---- Planters -----------------------------------------------------------

    async def list_planters(
        self,
        q: str | None,
        status: str,
        page: int,
        per_page: int,
    ) -> tuple[list[dict[str, Any]], int]:
        per_page = max(1, min(per_page, MAX_PER_PAGE))
        page = max(1, page)
        offset = (page - 1) * per_page

        base = select(Planter)
        if status == "all":
            base = base.where(
                Planter.deleted_at.is_(None),
                Planter.status.in_(["seed", "sprout", "louge"]),
            )
        elif status == "deleted":
            base = base.where(Planter.deleted_at.is_not(None))
        elif status == "archived":
            base = base.where(
                Planter.deleted_at.is_(None),
                Planter.status == "archived",
            )
        else:
            # 'seed' / 'sprout' / 'louge'
            base = base.where(
                Planter.deleted_at.is_(None),
                Planter.status == status,
            )

        if q is not None and q.strip():
            base = base.where(Planter.title.ilike(_q_pattern(q)))

        total_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(total_q)).scalar_one())

        if status == "deleted":
            order = (Planter.deleted_at.desc(), Planter.id.desc())
        else:
            order = (Planter.updated_at.desc(), Planter.id.desc())

        page_q = base.order_by(*order).limit(per_page).offset(offset)
        rows = (await self.db.execute(page_q)).scalars().all()
        if not rows:
            return [], total

        author_ids = list({p.user_id for p in rows})
        seed_type_ids = list({p.seed_type_id for p in rows})

        authors_q = select(User).where(User.id.in_(author_ids))
        authors = {
            u.id: u for u in (await self.db.execute(authors_q)).scalars().all()
        }
        seed_types_q = select(SeedType).where(SeedType.id.in_(seed_type_ids))
        st_names = {
            st.id: st.name
            for st in (await self.db.execute(seed_types_q)).scalars().all()
        }

        items: list[dict[str, Any]] = []
        for p in rows:
            author = authors[p.user_id]
            items.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                    "seed_type_name": st_names[p.seed_type_id],
                    "author": {
                        "id": author.id,
                        "display_name": author.display_name,
                        "avatar_url": author.avatar_url,
                    },
                    "log_count": p.log_count,
                    "contributor_count": p.contributor_count,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                    "deleted_at": p.deleted_at,
                }
            )
        return items, total

    async def archive_planter(self, planter: Planter) -> None:
        if planter.status == "archived":
            return  # idempotent
        planter.status = "archived"
        planter.updated_at = datetime.now(UTC)
        await self.db.flush()

    async def restore_planter(self, planter: Planter) -> None:
        if planter.status != "archived":
            raise ValueError("Planter is not archived")
        # MVP: restore always lands on 'seed'; subsequent Logs auto-promote to sprout.
        planter.status = "seed"
        planter.updated_at = datetime.now(UTC)
        await self.db.flush()

    async def soft_delete_planter(self, planter: Planter) -> None:
        planter.deleted_at = datetime.now(UTC)
        await self.db.flush()

    # ---- SeedTypes ----------------------------------------------------------

    async def list_seed_types(self, status: str) -> list[SeedType]:
        stmt = select(SeedType)
        if status == "active":
            stmt = stmt.where(SeedType.is_active == True)  # noqa: E712
        elif status == "inactive":
            stmt = stmt.where(SeedType.is_active == False)  # noqa: E712
        stmt = stmt.order_by(SeedType.sort_order.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_seed_type_description(
        self, seed_type: SeedType, description: str
    ) -> None:
        seed_type.description = description
        await self.db.flush()

    async def toggle_seed_type_active(self, seed_type: SeedType) -> None:
        seed_type.is_active = not seed_type.is_active
        await self.db.flush()
