import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import PlanterFollow
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import Tag
from app.models.user import User


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="疑問を投稿", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def inactive_seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="inactive", name="非表示", description="非表示", sort_order=99, is_active=False)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def leaf_tag(db_session: AsyncSession) -> Tag:
    t = Tag(name="SaaS", category="industry", is_leaf=True, sort_order=1)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def non_leaf_tag(db_session: AsyncSession) -> Tag:
    t = Tag(name="IT", category="industry", is_leaf=False, sort_order=1)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def inactive_tag(db_session: AsyncSession) -> Tag:
    t = Tag(name="Dead", category="industry", is_leaf=True, is_active=False, sort_order=1)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


class TestCreatePlanter:
    async def test_create_success(self, client, seed_type, leaf_tag):
        """POST /api/v1/planters should create a planter with 201."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Test Seed",
                "body": "This is a test seed body",
                "seed_type_id": str(seed_type.id),
                "tag_ids": [str(leaf_tag.id)],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Seed"
        assert data["status"] == "seed"
        assert data["log_count"] == 0
        assert data["seed_type"]["slug"] == "query"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "SaaS"

    async def test_unauthenticated_returns_401(self, client, seed_type):
        """POST /api/v1/planters without auth should return 401."""
        resp = await client.post(
            "/api/v1/planters",
            json={
                "title": "Test",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
            },
        )
        assert resp.status_code == 401

    async def test_invalid_seed_type_returns_400(self, client):
        """POST with non-existent seed_type_id should return 400."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Test",
                "body": "Body",
                "seed_type_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_seed_type"

    async def test_inactive_seed_type_returns_400(self, client, inactive_seed_type):
        """POST with inactive seed_type should return 400."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Test",
                "body": "Body",
                "seed_type_id": str(inactive_seed_type.id),
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_seed_type"

    async def test_non_leaf_tag_returns_400(self, client, seed_type, non_leaf_tag):
        """POST with non-leaf tag should return 400."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Test",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
                "tag_ids": [str(non_leaf_tag.id)],
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_tags"

    async def test_inactive_tag_returns_400(self, client, seed_type, inactive_tag):
        """POST with inactive tag should return 400."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Test",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
                "tag_ids": [str(inactive_tag.id)],
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_tags"

    async def test_empty_title_returns_422(self, client, seed_type):
        """POST with empty title should return 422."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
            },
        )
        assert resp.status_code == 422

    async def test_title_too_long_returns_422(self, client, seed_type):
        """POST with title > 200 chars should return 422."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "x" * 201,
                "body": "Body",
                "seed_type_id": str(seed_type.id),
            },
        )
        assert resp.status_code == 422

    async def test_auto_follow(self, client, seed_type, db_session):
        """POST should auto-follow the planter for the creator."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "Follow Test",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
            },
        )
        planter_id = uuid.UUID(resp.json()["id"])

        result = await db_session.execute(
            select(PlanterFollow).where(PlanterFollow.planter_id == planter_id)
        )
        follow = result.scalar_one_or_none()
        assert follow is not None

    async def test_no_tags_allowed(self, client, seed_type):
        """POST without tags should succeed (tags are optional)."""
        resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={
                "title": "No Tags",
                "body": "Body",
                "seed_type_id": str(seed_type.id),
                "tag_ids": [],
            },
        )
        assert resp.status_code == 201
        assert resp.json()["tags"] == []


class TestListPlanters:
    async def test_list_returns_200(self, client, seed_type):
        """GET /api/v1/planters should return 200."""
        # Create a planter first
        await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={"title": "Test", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        resp = await client.get("/api/v1/planters")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "has_next" in data
        assert len(data["items"]) == 1

    async def test_cursor_pagination(self, client, seed_type, db_session):
        """GET /api/v1/planters should support cursor pagination."""
        import asyncio
        from datetime import timedelta

        # Create planters with distinct created_at to ensure stable ordering
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            resp = await client.post(
                "/api/v1/planters",
                headers=AUTH_HEADERS,
                json={"title": f"Seed {i}", "body": "Body", "seed_type_id": str(seed_type.id)},
            )
            # Update created_at to ensure distinct timestamps
            planter_id = uuid.UUID(resp.json()["id"])
            result = await db_session.execute(
                select(Planter).where(Planter.id == planter_id)
            )
            p = result.scalar_one()
            p.created_at = now + timedelta(seconds=i)
        await db_session.commit()

        # First page
        resp = await client.get("/api/v1/planters?limit=2")
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["has_next"] is True
        assert data["next_cursor"] is not None

        # Second page
        resp2 = await client.get(f"/api/v1/planters?limit=2&cursor={data['next_cursor']}")
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        assert data2["has_next"] is True

        # Third page
        resp3 = await client.get(f"/api/v1/planters?limit=2&cursor={data2['next_cursor']}")
        data3 = resp3.json()
        assert len(data3["items"]) == 1
        assert data3["has_next"] is False

    async def test_unauthenticated_can_list(self, client, seed_type):
        """GET /api/v1/planters should work without auth."""
        await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={"title": "Test", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        resp = await client.get("/api/v1/planters")
        assert resp.status_code == 200


class TestPlanterFollow:
    async def test_follow_planter(self, client, seed_type, db_session):
        """POST /planters/{id}/follow should succeed."""
        create_resp = await client.post(
            "/api/v1/planters", headers=AUTH_HEADERS,
            json={"title": "Follow Me", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        planter_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/planters/{planter_id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

    async def test_unfollow_planter(self, client, seed_type, db_session):
        """DELETE /planters/{id}/follow should set is_manually_unfollowed."""
        create_resp = await client.post(
            "/api/v1/planters", headers=AUTH_HEADERS,
            json={"title": "Unfollow Me", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        planter_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/planters/{planter_id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

        result = await db_session.execute(
            select(PlanterFollow).where(
                PlanterFollow.planter_id == uuid.UUID(planter_id)
            )
        )
        follow = result.scalar_one_or_none()
        assert follow is not None
        assert follow.is_manually_unfollowed is True

    async def test_follow_nonexistent_planter_returns_404(self, client):
        """POST /planters/{bad_id}/follow should return 404."""
        resp = await client.post(
            f"/api/v1/planters/{uuid.uuid4()}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404


class TestFollowingTab:
    async def test_following_tab_requires_auth(self, client):
        """GET /planters?tab=following without auth should return 401."""
        resp = await client.get("/api/v1/planters?tab=following")
        assert resp.status_code == 401

    async def test_following_tab_returns_followed_planters(self, client, seed_type):
        """GET /planters?tab=following should return followed planters."""
        create_resp = await client.post(
            "/api/v1/planters", headers=AUTH_HEADERS,
            json={"title": "My Seed", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        # The planter is auto-followed on creation
        resp = await client.get(
            "/api/v1/planters?tab=following", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1


class TestGetPlanter:
    async def test_get_existing(self, client, seed_type):
        """GET /api/v1/planters/{id} should return the planter."""
        create_resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={"title": "Detail Test", "body": "Full body", "seed_type_id": str(seed_type.id)},
        )
        planter_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/planters/{planter_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Detail Test"
        assert data["body"] == "Full body"

    async def test_get_nonexistent_returns_404(self, client):
        """GET /api/v1/planters/{id} for unknown id should return 404."""
        resp = await client.get(f"/api/v1/planters/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_get_deleted_returns_404(self, client, seed_type, db_session):
        """GET /api/v1/planters/{id} for deleted planter should return 404."""
        create_resp = await client.post(
            "/api/v1/planters",
            headers=AUTH_HEADERS,
            json={"title": "Deleted", "body": "Body", "seed_type_id": str(seed_type.id)},
        )
        planter_id = create_resp.json()["id"]

        # Soft delete
        result = await db_session.execute(
            select(Planter).where(Planter.id == uuid.UUID(planter_id))
        )
        planter = result.scalar_one()
        planter.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter_id}")
        assert resp.status_code == 404
