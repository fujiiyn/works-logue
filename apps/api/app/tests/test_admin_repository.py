"""U7 Step 4: AdminRepository tests (TDD Red).

Covers:
  - get_dashboard_stats (4 COUNTs, JST boundary)
  - list_users (q / status / pagination / counts merge)
  - ban_user / unban_user (idempotent atomic UPDATE)
  - list_planters (status='all'/'archived'/'deleted'/seed/sprout/louge, sort,
    title q, author + seed_type_name JOIN)
  - archive_planter / restore_planter / soft_delete_planter
  - list_seed_types / update_seed_type_description / toggle_seed_type_active
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.admin_repository import AdminRepository

JST = timezone(timedelta(hours=9))


# ---- Fixtures ----------------------------------------------------------------


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query", name="疑問", description="desc", sort_order=1, is_active=True
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    u = User(
        auth_id=uuid.uuid4(),
        display_name="Admin Tarou",
        role="admin",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


def _make_user(
    display_name: str,
    *,
    role: str = "user",
    is_banned: bool = False,
    deleted_at: datetime | None = None,
) -> User:
    return User(
        auth_id=uuid.uuid4(),
        display_name=display_name,
        role=role,
        is_banned=is_banned,
        deleted_at=deleted_at,
    )


def _make_planter(
    user_id: uuid.UUID,
    seed_type_id: uuid.UUID,
    *,
    title: str = "悩みのSeed",
    status: str = "seed",
    deleted_at: datetime | None = None,
) -> Planter:
    return Planter(
        user_id=user_id,
        title=title,
        body="本文",
        seed_type_id=seed_type_id,
        status=status,
        deleted_at=deleted_at,
    )


# ---- get_dashboard_stats -----------------------------------------------------


class TestGetDashboardStats:
    async def test_counts_only_non_deleted_users_and_planters(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u_active = _make_user("active")
        u_deleted = _make_user(
            "gone", deleted_at=datetime.now(UTC) - timedelta(days=1)
        )
        db_session.add_all([u_active, u_deleted])
        await db_session.commit()

        p_active = _make_planter(u_active.id, seed_type.id, status="seed")
        p_deleted = _make_planter(
            u_active.id,
            seed_type.id,
            title="trashed",
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([p_active, p_deleted])
        await db_session.commit()

        repo = AdminRepository(db_session)
        stats = await repo.get_dashboard_stats()

        assert stats["total_users"] == 1
        assert stats["total_planters"] == 1

    async def test_pending_louge_count_is_sprout_only_and_excludes_deleted(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()

        db_session.add_all(
            [
                _make_planter(u.id, seed_type.id, status="seed"),
                _make_planter(u.id, seed_type.id, status="sprout"),
                _make_planter(u.id, seed_type.id, status="sprout"),
                _make_planter(u.id, seed_type.id, status="louge"),
                _make_planter(u.id, seed_type.id, status="archived"),
                _make_planter(
                    u.id,
                    seed_type.id,
                    status="sprout",
                    deleted_at=datetime.now(UTC),
                ),
            ]
        )
        await db_session.commit()

        repo = AdminRepository(db_session)
        stats = await repo.get_dashboard_stats()
        assert stats["pending_louge_count"] == 2

    async def test_new_planters_today_uses_jst_window(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()

        # Pin "now" to JST 12:00 on a deterministic date so the test is not
        # sensitive to JST-midnight boundaries during real wall-clock runs.
        fixed_now_jst = datetime(2026, 5, 4, 12, 0, 0, tzinfo=JST)
        today_start_utc = (
            fixed_now_jst.replace(hour=0).astimezone(UTC)
        )

        recent = _make_planter(u.id, seed_type.id, title="today")
        recent.created_at = today_start_utc + timedelta(hours=2)  # 02:00 UTC = 11:00 JST
        old = _make_planter(u.id, seed_type.id, title="old")
        old.created_at = today_start_utc - timedelta(days=2)
        db_session.add_all([recent, old])
        await db_session.commit()

        repo = AdminRepository(db_session)
        stats = await repo.get_dashboard_stats(now=fixed_now_jst)
        assert stats["new_planters_today"] == 1


# ---- list_users --------------------------------------------------------------


class TestListUsers:
    async def test_status_all_returns_normal_and_banned_excludes_deleted(
        self, db_session: AsyncSession
    ):
        normal = _make_user("Tanaka")
        banned = _make_user("Sato", is_banned=True)
        deleted = _make_user("Gone", deleted_at=datetime.now(UTC))
        db_session.add_all([normal, banned, deleted])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_users(
            q=None, status="all", page=1, per_page=50
        )
        ids = {item["id"] for item in items}
        assert normal.id in ids
        assert banned.id in ids
        assert deleted.id not in ids
        assert total == 2

    async def test_status_normal_filters_banned_out(self, db_session: AsyncSession):
        normal = _make_user("Tanaka")
        banned = _make_user("Sato", is_banned=True)
        db_session.add_all([normal, banned])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_users(
            q=None, status="normal", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == normal.id

    async def test_status_banned_returns_only_banned(self, db_session: AsyncSession):
        normal = _make_user("Tanaka")
        banned = _make_user("Sato", is_banned=True)
        db_session.add_all([normal, banned])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_users(
            q=None, status="banned", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == banned.id

    async def test_q_partial_match_case_insensitive_with_trim(
        self, db_session: AsyncSession
    ):
        u1 = _make_user("Tanaka Tarou")
        u2 = _make_user("Suzuki Hanako")
        db_session.add_all([u1, u2])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_users(
            q="  TANAKA  ", status="all", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == u1.id

    async def test_orders_by_created_at_desc(self, db_session: AsyncSession):
        old = _make_user("Old")
        old.created_at = datetime.now(UTC) - timedelta(days=10)
        new = _make_user("New")
        new.created_at = datetime.now(UTC)
        db_session.add_all([old, new])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _total = await repo.list_users(
            q=None, status="all", page=1, per_page=50
        )
        # newest first
        assert items[0]["id"] == new.id
        assert items[1]["id"] == old.id

    async def test_pagination(self, db_session: AsyncSession):
        users = [_make_user(f"U{i:02d}") for i in range(5)]
        # stagger created_at so order is stable
        base = datetime.now(UTC)
        for i, u in enumerate(users):
            u.created_at = base - timedelta(seconds=i)
        db_session.add_all(users)
        await db_session.commit()

        repo = AdminRepository(db_session)
        items_p1, total = await repo.list_users(
            q=None, status="all", page=1, per_page=2
        )
        items_p2, _ = await repo.list_users(
            q=None, status="all", page=2, per_page=2
        )
        assert total == 5
        assert len(items_p1) == 2
        assert len(items_p2) == 2
        assert {i["id"] for i in items_p1}.isdisjoint({i["id"] for i in items_p2})

    async def test_per_page_clamped_to_100(self, db_session: AsyncSession):
        u = _make_user("Solo")
        db_session.add(u)
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _ = await repo.list_users(q=None, status="all", page=1, per_page=999)
        assert len(items) == 1  # No error, just clamped

    async def test_planter_and_log_counts_merged(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("Author")
        other = _make_user("Other")
        db_session.add_all([u, other])
        await db_session.commit()

        # 2 planters and 3 logs by u; deleted ones must not count
        db_session.add_all(
            [
                _make_planter(u.id, seed_type.id, title="P1"),
                _make_planter(u.id, seed_type.id, title="P2"),
                _make_planter(
                    u.id,
                    seed_type.id,
                    title="P-deleted",
                    deleted_at=datetime.now(UTC),
                ),
                _make_planter(other.id, seed_type.id, title="P-other"),
            ]
        )
        await db_session.commit()

        # Need a planter to attach logs to
        host = _make_planter(other.id, seed_type.id, title="Host")
        db_session.add(host)
        await db_session.commit()

        db_session.add_all(
            [
                Log(planter_id=host.id, user_id=u.id, body="l1"),
                Log(planter_id=host.id, user_id=u.id, body="l2"),
                Log(planter_id=host.id, user_id=u.id, body="l3"),
                Log(
                    planter_id=host.id,
                    user_id=u.id,
                    body="l-deleted",
                    deleted_at=datetime.now(UTC),
                ),
            ]
        )
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _ = await repo.list_users(q="Author", status="all", page=1, per_page=50)
        item = next(i for i in items if i["id"] == u.id)
        assert item["planter_count"] == 2
        assert item["log_count"] == 3


# ---- ban_user / unban_user ---------------------------------------------------


class TestBanUnban:
    async def test_ban_sets_three_columns_atomically(
        self, db_session: AsyncSession
    ):
        u = _make_user("Target")
        db_session.add(u)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.ban_user(u, reason="spam")
        await db_session.refresh(u)
        assert u.is_banned is True
        assert u.banned_at is not None
        assert u.ban_reason == "spam"

    async def test_ban_with_no_reason(self, db_session: AsyncSession):
        u = _make_user("Target")
        db_session.add(u)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.ban_user(u, reason=None)
        await db_session.refresh(u)
        assert u.is_banned is True
        assert u.ban_reason is None

    async def test_ban_is_idempotent(self, db_session: AsyncSession):
        u = _make_user("Target", is_banned=True)
        u.banned_at = datetime.now(UTC) - timedelta(days=1)
        u.ban_reason = "old reason"
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        original_banned_at = u.banned_at
        original_reason = u.ban_reason

        repo = AdminRepository(db_session)
        await repo.ban_user(u, reason="new reason")
        await db_session.refresh(u)
        # Existing values preserved (idempotent)
        assert u.is_banned is True
        assert u.banned_at == original_banned_at
        assert u.ban_reason == original_reason

    async def test_unban_clears_three_columns(self, db_session: AsyncSession):
        u = _make_user("Target", is_banned=True)
        u.banned_at = datetime.now(UTC)
        u.ban_reason = "spam"
        db_session.add(u)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.unban_user(u)
        await db_session.refresh(u)
        assert u.is_banned is False
        assert u.banned_at is None
        assert u.ban_reason is None

    async def test_unban_is_idempotent(self, db_session: AsyncSession):
        u = _make_user("Target")  # not banned
        db_session.add(u)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.unban_user(u)
        await db_session.refresh(u)
        assert u.is_banned is False
        assert u.banned_at is None
        assert u.ban_reason is None


# ---- list_planters -----------------------------------------------------------


class TestListPlanters:
    async def test_status_all_excludes_archived_and_deleted(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()

        seed_p = _make_planter(u.id, seed_type.id, status="seed", title="A")
        sprout_p = _make_planter(u.id, seed_type.id, status="sprout", title="B")
        louge_p = _make_planter(u.id, seed_type.id, status="louge", title="C")
        archived_p = _make_planter(u.id, seed_type.id, status="archived", title="D")
        deleted_p = _make_planter(
            u.id, seed_type.id, title="E", deleted_at=datetime.now(UTC)
        )
        db_session.add_all([seed_p, sprout_p, louge_p, archived_p, deleted_p])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_planters(
            q=None, status="all", page=1, per_page=50
        )
        ids = {it["id"] for it in items}
        assert seed_p.id in ids
        assert sprout_p.id in ids
        assert louge_p.id in ids
        assert archived_p.id not in ids
        assert deleted_p.id not in ids
        assert total == 3

    async def test_status_archived_returns_archived_only(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        a = _make_planter(u.id, seed_type.id, status="archived", title="A")
        s = _make_planter(u.id, seed_type.id, status="seed", title="S")
        db_session.add_all([a, s])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_planters(
            q=None, status="archived", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == a.id

    async def test_status_deleted_returns_only_soft_deleted(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        d = _make_planter(
            u.id, seed_type.id, title="D", deleted_at=datetime.now(UTC)
        )
        s = _make_planter(u.id, seed_type.id, status="seed", title="S")
        db_session.add_all([d, s])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_planters(
            q=None, status="deleted", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == d.id

    async def test_status_seed_returns_only_seed(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        s = _make_planter(u.id, seed_type.id, status="seed", title="S")
        sp = _make_planter(u.id, seed_type.id, status="sprout", title="P")
        db_session.add_all([s, sp])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_planters(
            q=None, status="seed", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == s.id

    async def test_q_filters_by_title_partial_match(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        a = _make_planter(u.id, seed_type.id, title="営業の悩み", status="seed")
        b = _make_planter(u.id, seed_type.id, title="マーケティング", status="seed")
        db_session.add_all([a, b])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, total = await repo.list_planters(
            q="営業", status="all", page=1, per_page=50
        )
        assert total == 1
        assert items[0]["id"] == a.id

    async def test_default_sort_by_updated_at_desc(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        old = _make_planter(u.id, seed_type.id, status="seed", title="old")
        old.updated_at = datetime.now(UTC) - timedelta(days=3)
        old.created_at = old.updated_at
        new = _make_planter(u.id, seed_type.id, status="seed", title="new")
        new.updated_at = datetime.now(UTC)
        new.created_at = new.updated_at
        db_session.add_all([old, new])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _ = await repo.list_planters(
            q=None, status="all", page=1, per_page=50
        )
        assert items[0]["id"] == new.id

    async def test_deleted_status_sorts_by_deleted_at_desc(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        older = _make_planter(
            u.id,
            seed_type.id,
            title="older",
            deleted_at=datetime.now(UTC) - timedelta(days=5),
        )
        newer = _make_planter(
            u.id,
            seed_type.id,
            title="newer",
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([older, newer])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _ = await repo.list_planters(
            q=None, status="deleted", page=1, per_page=50
        )
        assert items[0]["id"] == newer.id
        assert items[1]["id"] == older.id

    async def test_includes_author_and_seed_type_name(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("Author")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="seed", title="S")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        items, _ = await repo.list_planters(
            q=None, status="all", page=1, per_page=50
        )
        item = items[0]
        assert item["author"]["id"] == u.id
        assert item["author"]["display_name"] == "Author"
        assert item["seed_type_name"] == seed_type.name


# ---- archive / restore / soft-delete planter --------------------------------


class TestPlanterStateMutations:
    async def test_archive_sets_status_archived(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="seed")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.archive_planter(p)
        await db_session.refresh(p)
        assert p.status == "archived"

    async def test_archive_is_idempotent(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="archived")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.archive_planter(p)
        await db_session.refresh(p)
        assert p.status == "archived"

    async def test_restore_from_archived_returns_to_seed(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="archived")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.restore_planter(p)
        await db_session.refresh(p)
        assert p.status == "seed"

    async def test_restore_raises_when_not_archived(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="seed")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        with pytest.raises(ValueError):
            await repo.restore_planter(p)

    async def test_soft_delete_sets_deleted_at(
        self, db_session: AsyncSession, seed_type: SeedType
    ):
        u = _make_user("u")
        db_session.add(u)
        await db_session.commit()
        p = _make_planter(u.id, seed_type.id, status="seed")
        db_session.add(p)
        await db_session.commit()

        repo = AdminRepository(db_session)
        await repo.soft_delete_planter(p)
        await db_session.refresh(p)
        assert p.deleted_at is not None


# ---- seed_types --------------------------------------------------------------


class TestSeedTypes:
    async def test_list_seed_types_orders_by_sort_order_asc(
        self, db_session: AsyncSession
    ):
        st1 = SeedType(slug="a", name="A", description="d", sort_order=3, is_active=True)
        st2 = SeedType(slug="b", name="B", description="d", sort_order=1, is_active=True)
        st3 = SeedType(slug="c", name="C", description="d", sort_order=2, is_active=False)
        db_session.add_all([st1, st2, st3])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items = await repo.list_seed_types(status="all")
        assert [i.id for i in items] == [st2.id, st3.id, st1.id]

    async def test_list_seed_types_status_active(self, db_session: AsyncSession):
        st1 = SeedType(slug="a", name="A", description="d", sort_order=1, is_active=True)
        st2 = SeedType(slug="b", name="B", description="d", sort_order=2, is_active=False)
        db_session.add_all([st1, st2])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items = await repo.list_seed_types(status="active")
        assert len(items) == 1
        assert items[0].id == st1.id

    async def test_list_seed_types_status_inactive(self, db_session: AsyncSession):
        st1 = SeedType(slug="a", name="A", description="d", sort_order=1, is_active=True)
        st2 = SeedType(slug="b", name="B", description="d", sort_order=2, is_active=False)
        db_session.add_all([st1, st2])
        await db_session.commit()

        repo = AdminRepository(db_session)
        items = await repo.list_seed_types(status="inactive")
        assert len(items) == 1
        assert items[0].id == st2.id

    async def test_update_description_only(self, db_session: AsyncSession, seed_type: SeedType):
        repo = AdminRepository(db_session)
        original_slug = seed_type.slug
        original_name = seed_type.name
        await repo.update_seed_type_description(seed_type, "新しい説明")
        await db_session.refresh(seed_type)
        assert seed_type.description == "新しい説明"
        assert seed_type.slug == original_slug
        assert seed_type.name == original_name

    async def test_toggle_active_flips_value(self, db_session: AsyncSession, seed_type: SeedType):
        assert seed_type.is_active is True
        repo = AdminRepository(db_session)
        await repo.toggle_seed_type_active(seed_type)
        await db_session.refresh(seed_type)
        assert seed_type.is_active is False
        await repo.toggle_seed_type_active(seed_type)
        await db_session.refresh(seed_type)
        assert seed_type.is_active is True
