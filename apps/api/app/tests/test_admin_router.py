"""U7 Phase 6: Admin router endpoint tests.

Each endpoint is implemented in TDD: tests live here, the router is at
`app/routers/admin.py`. Authentication is mocked via the standard `client`
fixture; admin authority is established by manually inserting a User row
with `role='admin'` and the test's `mock_auth_user_sub` as `auth_id`.

Failure-mode contract for every admin endpoint:
  - non-admin / banned admin / unauthenticated → 404 (admin existence is secret)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


# ---- structlog capture helper ------------------------------------------------


@pytest.fixture
def capture_structlog():
    """Reconfigure structlog to capture events in a list, restore on teardown."""
    captured: list[dict] = []

    def _capture(_logger, _method_name, event_dict):
        captured.append(dict(event_dict))
        raise structlog.DropEvent

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _capture,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        cache_logger_on_first_use=False,
    )
    yield captured
    structlog.reset_defaults()


# ---- DB fixtures -------------------------------------------------------------


@pytest.fixture
async def admin_self(db_session: AsyncSession, mock_auth_user_sub: uuid.UUID) -> User:
    """Insert the calling admin user so require_admin passes."""
    u = User(
        auth_id=mock_auth_user_sub,
        display_name="Admin Self",
        role="admin",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def regular_self(db_session: AsyncSession, mock_auth_user_sub: uuid.UUID) -> User:
    """Insert the calling user as a regular (non-admin) user."""
    u = User(
        auth_id=mock_auth_user_sub,
        display_name="Regular Self",
        role="user",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query", name="疑問", description="desc", sort_order=1, is_active=True
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


# ---- GET /admin/stats --------------------------------------------------------


class TestGetStats:
    async def test_unauthenticated_returns_404(self, client):
        resp = await client.get("/api/v1/admin/stats")
        assert resp.status_code == 404

    async def test_regular_user_returns_404(self, client, regular_self):
        resp = await client.get("/api/v1/admin/stats", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    async def test_admin_returns_four_fields(self, client, admin_self):
        resp = await client.get("/api/v1/admin/stats", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {
            "total_users",
            "total_planters",
            "new_planters_today",
            "pending_louge_count",
        }
        assert isinstance(data["total_users"], int)

    async def test_admin_self_is_counted(self, client, admin_self):
        resp = await client.get("/api/v1/admin/stats", headers=AUTH_HEADERS)
        data = resp.json()
        # Only the admin row exists
        assert data["total_users"] == 1
        assert data["total_planters"] == 0
        assert data["pending_louge_count"] == 0

    async def test_pending_louge_count_excludes_deleted(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Author")
        db_session.add(author)
        await db_session.commit()
        db_session.add_all(
            [
                Planter(
                    user_id=author.id,
                    title="x",
                    body="b",
                    seed_type_id=seed_type.id,
                    status="sprout",
                ),
                Planter(
                    user_id=author.id,
                    title="y",
                    body="b",
                    seed_type_id=seed_type.id,
                    status="sprout",
                ),
                Planter(
                    user_id=author.id,
                    title="z",
                    body="b",
                    seed_type_id=seed_type.id,
                    status="sprout",
                    deleted_at=datetime.now(UTC),
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get("/api/v1/admin/stats", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["pending_louge_count"] == 2


# ---- GET /admin/users --------------------------------------------------------


class TestListUsers:
    async def test_unauthenticated_returns_404(self, client):
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 404

    async def test_regular_user_returns_404(self, client, regular_self):
        resp = await client.get("/api/v1/admin/users", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    async def test_admin_lists_all_users(self, client, admin_self, db_session):
        db_session.add_all(
            [
                User(auth_id=uuid.uuid4(), display_name="Tanaka"),
                User(auth_id=uuid.uuid4(), display_name="Sato"),
            ]
        )
        await db_session.commit()
        resp = await client.get("/api/v1/admin/users", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3  # 2 + admin_self
        assert data["page"] == 1
        assert data["per_page"] == 20  # default
        assert len(data["items"]) == 3

    async def test_q_partial_match_case_insensitive(
        self, client, admin_self, db_session
    ):
        db_session.add_all(
            [
                User(auth_id=uuid.uuid4(), display_name="Tanaka Tarou"),
                User(auth_id=uuid.uuid4(), display_name="Suzuki Hanako"),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/users?q=TANAKA", headers=AUTH_HEADERS
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["display_name"] == "Tanaka Tarou"

    async def test_status_banned_filter(self, client, admin_self, db_session):
        db_session.add_all(
            [
                User(auth_id=uuid.uuid4(), display_name="Banned", is_banned=True),
                User(auth_id=uuid.uuid4(), display_name="Normal"),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/users?status=banned", headers=AUTH_HEADERS
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["display_name"] == "Banned"

    async def test_status_normal_filter(self, client, admin_self, db_session):
        db_session.add_all(
            [
                User(auth_id=uuid.uuid4(), display_name="Banned", is_banned=True),
                User(auth_id=uuid.uuid4(), display_name="Normal"),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/users?status=normal", headers=AUTH_HEADERS
        )
        data = resp.json()
        # admin_self + Normal (Banned excluded)
        assert data["total"] == 2

    async def test_pagination_per_page_clamped(self, client, admin_self):
        resp = await client.get(
            "/api/v1/admin/users?per_page=999", headers=AUTH_HEADERS
        )
        data = resp.json()
        assert data["per_page"] == 100  # clamped

    async def test_is_self_flag(self, client, admin_self, db_session):
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        resp = await client.get("/api/v1/admin/users", headers=AUTH_HEADERS)
        items = resp.json()["items"]
        for it in items:
            if it["id"] == str(admin_self.id):
                assert it["is_self"] is True
            else:
                assert it["is_self"] is False

    async def test_deleted_users_excluded(self, client, admin_self, db_session):
        db_session.add(
            User(
                auth_id=uuid.uuid4(),
                display_name="Gone",
                deleted_at=datetime.now(UTC),
            )
        )
        await db_session.commit()
        resp = await client.get("/api/v1/admin/users", headers=AUTH_HEADERS)
        data = resp.json()
        names = [it["display_name"] for it in data["items"]]
        assert "Gone" not in names

    async def test_planter_and_log_counts_present(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Author")
        db_session.add(author)
        await db_session.commit()
        host = Planter(
            user_id=author.id,
            title="P",
            body="b",
            seed_type_id=seed_type.id,
            status="seed",
        )
        db_session.add(host)
        await db_session.commit()
        db_session.add(Log(planter_id=host.id, user_id=author.id, body="l"))
        await db_session.commit()

        resp = await client.get(
            "/api/v1/admin/users?q=Author", headers=AUTH_HEADERS
        )
        item = resp.json()["items"][0]
        assert item["planter_count"] == 1
        assert item["log_count"] == 1


# ---- POST /admin/users/{id}/ban ---------------------------------------------


class TestBanUser:
    async def test_unauthenticated_returns_404(self, client):
        target_id = uuid.uuid4()
        resp = await client.post(f"/api/v1/admin/users/{target_id}/ban", json={})
        assert resp.status_code == 404

    async def test_regular_user_returns_404(self, client, regular_self):
        target_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/ban",
            headers=AUTH_HEADERS,
            json={},
        )
        assert resp.status_code == 404

    async def test_ban_success(self, client, admin_self, db_session, capture_structlog):
        target = User(auth_id=uuid.uuid4(), display_name="Target")
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/ban",
            headers=AUTH_HEADERS,
            json={"reason": "spam"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_banned"] is True
        assert data["banned_at"] is not None
        assert data["ban_reason"] == "spam"

        events = [e for e in capture_structlog if e.get("event") == "admin.user.ban"]
        assert len(events) == 1
        assert events[0]["target_user_id"] == str(target.id)
        assert events[0]["actor_user_id"] == str(admin_self.id)
        assert events[0]["ban_reason"] == "spam"

    async def test_ban_without_reason(self, client, admin_self, db_session):
        target = User(auth_id=uuid.uuid4(), display_name="Target")
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/ban",
            headers=AUTH_HEADERS,
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["ban_reason"] is None

    async def test_reason_too_long_returns_422(
        self, client, admin_self, db_session
    ):
        target = User(auth_id=uuid.uuid4(), display_name="Target")
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/ban",
            headers=AUTH_HEADERS,
            json={"reason": "x" * 501},
        )
        assert resp.status_code == 422

    async def test_self_ban_rejected(self, client, admin_self):
        resp = await client.post(
            f"/api/v1/admin/users/{admin_self.id}/ban",
            headers=AUTH_HEADERS,
            json={},
        )
        assert resp.status_code == 400

    async def test_admin_target_rejected(
        self, client, admin_self, db_session
    ):
        other_admin = User(
            auth_id=uuid.uuid4(), display_name="Other Admin", role="admin"
        )
        db_session.add(other_admin)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{other_admin.id}/ban",
            headers=AUTH_HEADERS,
            json={},
        )
        assert resp.status_code == 400

    async def test_ban_idempotent(self, client, admin_self, db_session):
        original_at = datetime.now(UTC) - timedelta(days=1)
        target = User(
            auth_id=uuid.uuid4(),
            display_name="Already Banned",
            is_banned=True,
            banned_at=original_at,
            ban_reason="old",
        )
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/ban",
            headers=AUTH_HEADERS,
            json={"reason": "new"},
        )
        assert resp.status_code == 200
        # Returned values reflect the unchanged record
        assert resp.json()["ban_reason"] == "old"

    async def test_nonexistent_user_returns_404(
        self, client, admin_self
    ):
        resp = await client.post(
            f"/api/v1/admin/users/{uuid.uuid4()}/ban",
            headers=AUTH_HEADERS,
            json={},
        )
        assert resp.status_code == 404


# ---- POST /admin/users/{id}/unban -------------------------------------------


class TestUnbanUser:
    async def test_unban_success(
        self, client, admin_self, db_session, capture_structlog
    ):
        target = User(
            auth_id=uuid.uuid4(),
            display_name="Banned",
            is_banned=True,
            banned_at=datetime.now(UTC),
            ban_reason="spam",
        )
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/unban", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_banned"] is False
        assert data["banned_at"] is None
        assert data["ban_reason"] is None

        events = [
            e for e in capture_structlog if e.get("event") == "admin.user.unban"
        ]
        assert len(events) == 1
        assert events[0]["target_user_id"] == str(target.id)
        assert events[0]["actor_user_id"] == str(admin_self.id)

    async def test_unban_idempotent(self, client, admin_self, db_session):
        target = User(auth_id=uuid.uuid4(), display_name="NotBanned")
        db_session.add(target)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/unban", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["is_banned"] is False

    async def test_nonexistent_user_returns_404(self, client, admin_self):
        resp = await client.post(
            f"/api/v1/admin/users/{uuid.uuid4()}/unban", headers=AUTH_HEADERS
        )
        assert resp.status_code == 404

    async def test_regular_user_returns_404(self, client, regular_self):
        resp = await client.post(
            f"/api/v1/admin/users/{uuid.uuid4()}/unban", headers=AUTH_HEADERS
        )
        assert resp.status_code == 404


# ---- GET /admin/planters ----------------------------------------------------


def _new_planter(
    user_id: uuid.UUID,
    seed_type_id: uuid.UUID,
    *,
    title: str = "P",
    status: str = "seed",
    deleted_at: datetime | None = None,
) -> Planter:
    return Planter(
        user_id=user_id,
        title=title,
        body="b",
        seed_type_id=seed_type_id,
        status=status,
        deleted_at=deleted_at,
    )


class TestListPlanters:
    async def test_unauthenticated_returns_404(self, client):
        resp = await client.get("/api/v1/admin/planters")
        assert resp.status_code == 404

    async def test_status_all_excludes_archived_and_deleted(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        db_session.add_all(
            [
                _new_planter(author.id, seed_type.id, title="A", status="seed"),
                _new_planter(author.id, seed_type.id, title="B", status="sprout"),
                _new_planter(author.id, seed_type.id, title="C", status="louge"),
                _new_planter(
                    author.id, seed_type.id, title="D", status="archived"
                ),
                _new_planter(
                    author.id,
                    seed_type.id,
                    title="E",
                    deleted_at=datetime.now(UTC),
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/planters?status=all", headers=AUTH_HEADERS
        )
        data = resp.json()
        assert data["total"] == 3
        titles = {it["title"] for it in data["items"]}
        assert titles == {"A", "B", "C"}

    async def test_status_archived(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        db_session.add_all(
            [
                _new_planter(author.id, seed_type.id, title="A", status="seed"),
                _new_planter(
                    author.id, seed_type.id, title="B", status="archived"
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/planters?status=archived", headers=AUTH_HEADERS
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "B"
        assert data["items"][0]["status"] == "archived"

    async def test_status_deleted_sorted_by_deleted_at_desc(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        older = _new_planter(
            author.id,
            seed_type.id,
            title="older",
            deleted_at=datetime.now(UTC) - timedelta(days=2),
        )
        newer = _new_planter(
            author.id,
            seed_type.id,
            title="newer",
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([older, newer])
        await db_session.commit()

        resp = await client.get(
            "/api/v1/admin/planters?status=deleted", headers=AUTH_HEADERS
        )
        items = resp.json()["items"]
        assert items[0]["title"] == "newer"
        assert items[1]["title"] == "older"

    async def test_q_filters_title(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        db_session.add_all(
            [
                _new_planter(
                    author.id, seed_type.id, title="営業の悩み", status="seed"
                ),
                _new_planter(
                    author.id, seed_type.id, title="マーケ", status="seed"
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/planters?q=営業", headers=AUTH_HEADERS
        )
        assert resp.json()["total"] == 1

    async def test_includes_author_and_seed_type_name(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Author X")
        db_session.add(author)
        await db_session.commit()
        db_session.add(
            _new_planter(author.id, seed_type.id, title="A", status="seed")
        )
        await db_session.commit()

        resp = await client.get(
            "/api/v1/admin/planters?status=all", headers=AUTH_HEADERS
        )
        item = resp.json()["items"][0]
        assert item["author"]["display_name"] == "Author X"
        assert item["seed_type_name"] == seed_type.name


# ---- POST /admin/planters/{id}/archive --------------------------------------


class TestArchivePlanter:
    async def test_archive_success(
        self, client, admin_self, db_session, seed_type, capture_structlog
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, status="seed")
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/archive", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

        events = [
            e for e in capture_structlog if e.get("event") == "admin.planter.archive"
        ]
        assert len(events) == 1

    async def test_archive_already_archived_idempotent(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, status="archived")
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/archive", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    async def test_archive_deleted_returns_404(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(
            author.id, seed_type.id, deleted_at=datetime.now(UTC)
        )
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/archive", headers=AUTH_HEADERS
        )
        assert resp.status_code == 404

    async def test_archive_nonexistent_returns_404(self, client, admin_self):
        resp = await client.post(
            f"/api/v1/admin/planters/{uuid.uuid4()}/archive",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404


# ---- POST /admin/planters/{id}/restore --------------------------------------


class TestRestorePlanter:
    async def test_restore_archived_to_seed(
        self, client, admin_self, db_session, seed_type, capture_structlog
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, status="archived")
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/restore", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "seed"

        events = [
            e for e in capture_structlog if e.get("event") == "admin.planter.restore"
        ]
        assert len(events) == 1

    async def test_restore_non_archived_returns_400(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, status="seed")
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/restore", headers=AUTH_HEADERS
        )
        assert resp.status_code == 400

    async def test_restore_deleted_returns_404(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(
            author.id, seed_type.id, deleted_at=datetime.now(UTC)
        )
        db_session.add(p)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/admin/planters/{p.id}/restore", headers=AUTH_HEADERS
        )
        assert resp.status_code == 404

    async def test_restore_nonexistent_returns_404(self, client, admin_self):
        resp = await client.post(
            f"/api/v1/admin/planters/{uuid.uuid4()}/restore",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404


# ---- DELETE /admin/planters/{id} --------------------------------------------


class TestDeletePlanter:
    async def test_delete_with_matching_title_succeeds(
        self, client, admin_self, db_session, seed_type, capture_structlog
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, title="営業の悩み")
        db_session.add(p)
        await db_session.commit()

        resp = await client.request(
            "DELETE",
            f"/api/v1/admin/planters/{p.id}",
            headers=AUTH_HEADERS,
            json={"confirm_title": "営業の悩み"},
        )
        assert resp.status_code == 204

        await db_session.refresh(p)
        assert p.deleted_at is not None

        events = [
            e for e in capture_structlog if e.get("event") == "admin.planter.delete"
        ]
        assert len(events) == 1
        assert events[0].get("title") == "営業の悩み"

    async def test_delete_with_completely_different_title_returns_400(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, title="本当のタイトル")
        db_session.add(p)
        await db_session.commit()

        resp = await client.request(
            "DELETE",
            f"/api/v1/admin/planters/{p.id}",
            headers=AUTH_HEADERS,
            json={"confirm_title": "全然違う"},
        )
        assert resp.status_code == 400

    async def test_delete_with_surrounding_whitespace_matches(
        self, client, admin_self, db_session, seed_type
    ):
        # BR-A12 D7: trim both sides, then strict equality.
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, title="営業")
        db_session.add(p)
        await db_session.commit()

        resp = await client.request(
            "DELETE",
            f"/api/v1/admin/planters/{p.id}",
            headers=AUTH_HEADERS,
            json={"confirm_title": "  営業  "},
        )
        assert resp.status_code == 204

    async def test_delete_with_case_difference_returns_400(
        self, client, admin_self, db_session, seed_type
    ):
        author = User(auth_id=uuid.uuid4(), display_name="Au")
        db_session.add(author)
        await db_session.commit()
        p = _new_planter(author.id, seed_type.id, title="MyTitle")
        db_session.add(p)
        await db_session.commit()

        resp = await client.request(
            "DELETE",
            f"/api/v1/admin/planters/{p.id}",
            headers=AUTH_HEADERS,
            json={"confirm_title": "mytitle"},
        )
        assert resp.status_code == 400

    async def test_delete_nonexistent_returns_404(self, client, admin_self):
        resp = await client.request(
            "DELETE",
            f"/api/v1/admin/planters/{uuid.uuid4()}",
            headers=AUTH_HEADERS,
            json={"confirm_title": "x"},
        )
        assert resp.status_code == 404


# ---- GET /admin/seed-types --------------------------------------------------


class TestListSeedTypes:
    async def test_unauthenticated_returns_404(self, client):
        resp = await client.get("/api/v1/admin/seed-types")
        assert resp.status_code == 404

    async def test_status_all_orders_by_sort_order(
        self, client, admin_self, db_session
    ):
        db_session.add_all(
            [
                SeedType(slug="a", name="A", description="d", sort_order=3),
                SeedType(slug="b", name="B", description="d", sort_order=1),
                SeedType(
                    slug="c", name="C", description="d", sort_order=2, is_active=False
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/seed-types?status=all", headers=AUTH_HEADERS
        )
        assert resp.status_code == 200
        items = resp.json()
        assert [it["slug"] for it in items] == ["b", "c", "a"]

    async def test_status_active_returns_only_active(
        self, client, admin_self, db_session
    ):
        db_session.add_all(
            [
                SeedType(slug="x", name="X", description="d", sort_order=1),
                SeedType(
                    slug="y", name="Y", description="d", sort_order=2, is_active=False
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/seed-types?status=active", headers=AUTH_HEADERS
        )
        items = resp.json()
        assert len(items) == 1
        assert items[0]["slug"] == "x"

    async def test_status_inactive_returns_only_inactive(
        self, client, admin_self, db_session
    ):
        db_session.add_all(
            [
                SeedType(slug="x", name="X", description="d", sort_order=1),
                SeedType(
                    slug="y", name="Y", description="d", sort_order=2, is_active=False
                ),
            ]
        )
        await db_session.commit()
        resp = await client.get(
            "/api/v1/admin/seed-types?status=inactive", headers=AUTH_HEADERS
        )
        items = resp.json()
        assert len(items) == 1
        assert items[0]["slug"] == "y"


# ---- PATCH /admin/seed-types/{id} -------------------------------------------


class TestUpdateSeedTypeDescription:
    async def test_update_succeeds(
        self, client, admin_self, db_session, seed_type, capture_structlog
    ):
        original = seed_type.description
        resp = await client.patch(
            f"/api/v1/admin/seed-types/{seed_type.id}",
            headers=AUTH_HEADERS,
            json={"description": "新しい説明文"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "新しい説明文"

        events = [
            e
            for e in capture_structlog
            if e.get("event") == "admin.seed_type.update"
        ]
        assert len(events) == 1
        assert events[0]["before_description"] == original
        assert events[0]["after_description"] == "新しい説明文"

    async def test_empty_description_returns_422(
        self, client, admin_self, seed_type
    ):
        resp = await client.patch(
            f"/api/v1/admin/seed-types/{seed_type.id}",
            headers=AUTH_HEADERS,
            json={"description": "   "},
        )
        assert resp.status_code == 422

    async def test_too_long_description_returns_422(
        self, client, admin_self, seed_type
    ):
        resp = await client.patch(
            f"/api/v1/admin/seed-types/{seed_type.id}",
            headers=AUTH_HEADERS,
            json={"description": "x" * 1001},
        )
        assert resp.status_code == 422

    async def test_nonexistent_returns_404(self, client, admin_self):
        resp = await client.patch(
            f"/api/v1/admin/seed-types/{uuid.uuid4()}",
            headers=AUTH_HEADERS,
            json={"description": "新説明"},
        )
        assert resp.status_code == 404


# ---- POST /admin/seed-types/{id}/toggle-active ------------------------------


class TestToggleSeedTypeActive:
    async def test_toggle_flips_value(
        self, client, admin_self, db_session, seed_type, capture_structlog
    ):
        assert seed_type.is_active is True
        resp = await client.post(
            f"/api/v1/admin/seed-types/{seed_type.id}/toggle-active",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        events = [
            e
            for e in capture_structlog
            if e.get("event") == "admin.seed_type.update"
        ]
        assert len(events) == 1
        assert events[0]["before_is_active"] is True
        assert events[0]["after_is_active"] is False

        resp2 = await client.post(
            f"/api/v1/admin/seed-types/{seed_type.id}/toggle-active",
            headers=AUTH_HEADERS,
        )
        assert resp2.json()["is_active"] is True

    async def test_nonexistent_returns_404(self, client, admin_self):
        resp = await client.post(
            f"/api/v1/admin/seed-types/{uuid.uuid4()}/toggle-active",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404
