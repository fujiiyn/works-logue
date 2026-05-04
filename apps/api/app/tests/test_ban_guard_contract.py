"""U7 Step 18: BAN guard contract tests.

These tests pin Functional Design §7 as a contract: the BAN gate lives in
`get_current_user` (`apps/api/app/dependencies.py`), so individual handlers
MUST NOT add their own per-handler ban checks. Adding redundant checks
breaks the single-source-of-truth invariant and risks divergent error codes
across endpoints.

Contract:
  - Mutating verbs (POST / PATCH / DELETE) by a banned user → 403
  - Read verbs (GET / HEAD / OPTIONS) by a banned user → 200 (existing
    visibility is preserved; banning hides the user from posting, not from
    browsing)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


@pytest.fixture
async def banned_self(
    db_session: AsyncSession, mock_auth_user_sub: uuid.UUID
) -> User:
    """The calling user, pre-banned."""
    u = User(
        auth_id=mock_auth_user_sub,
        display_name="Banned Self",
        is_banned=True,
        banned_at=datetime.now(UTC),
        ban_reason="contract test",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    u = User(auth_id=uuid.uuid4(), display_name="Other")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query", name="疑問", description="d", sort_order=1, is_active=True
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def existing_planter(
    db_session: AsyncSession, other_user: User, seed_type: SeedType
) -> Planter:
    p = Planter(
        user_id=other_user.id,
        title="P",
        body="b",
        seed_type_id=seed_type.id,
        status="seed",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


# ---- Mutating endpoints must 403 --------------------------------------------


class TestBannedMutationsReturn403:
    async def test_post_planters(self, client, banned_self, seed_type):
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "x",
                "body": "y",
                "seed_type_id": str(seed_type.id),
                "tag_ids": [],
            },
        )
        assert resp.status_code == 403

    async def test_post_planter_logs(self, client, banned_self, existing_planter):
        resp = await client.post(
            f"/api/v1/planters/{existing_planter.id}/logs",
            headers=AUTH_HEADERS,
            json={"body": "log body"},
        )
        assert resp.status_code == 403

    async def test_patch_users_me(self, client, banned_self):
        resp = await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={"display_name": "Renamed"},
        )
        assert resp.status_code == 403

    async def test_post_users_me_avatar(self, client, banned_self):
        # Empty body is enough to reach the BAN gate before validation.
        resp = await client.post(
            "/api/v1/users/me/avatar",
            headers=AUTH_HEADERS,
            files={"file": ("avatar.png", b"\x89PNG\r\n", "image/png")},
        )
        assert resp.status_code == 403

    async def test_post_user_follow(self, client, banned_self, other_user):
        resp = await client.post(
            f"/api/v1/users/{other_user.id}/follow", headers=AUTH_HEADERS
        )
        assert resp.status_code == 403

    async def test_delete_user_follow(self, client, banned_self, other_user):
        resp = await client.delete(
            f"/api/v1/users/{other_user.id}/follow", headers=AUTH_HEADERS
        )
        assert resp.status_code == 403

    async def test_post_planter_follow(self, client, banned_self, existing_planter):
        resp = await client.post(
            f"/api/v1/planters/{existing_planter.id}/follow",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 403

    async def test_delete_planter_follow(
        self, client, banned_self, existing_planter
    ):
        resp = await client.delete(
            f"/api/v1/planters/{existing_planter.id}/follow",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 403


# ---- Read endpoints stay 200 ------------------------------------------------


class TestBannedReadsStay200:
    async def test_get_planters_feed(self, client, banned_self):
        resp = await client.get("/api/v1/planters", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    async def test_get_users_me(self, client, banned_self):
        resp = await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["is_banned"] is True
