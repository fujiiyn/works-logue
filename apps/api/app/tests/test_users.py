import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


@pytest.fixture
async def leaf_tags(db_session: AsyncSession) -> list[Tag]:
    t1 = Tag(name="SaaS", category="industry", is_leaf=True, sort_order=1)
    t2 = Tag(name="法人営業", category="occupation", is_leaf=True, sort_order=1)
    db_session.add_all([t1, t2])
    await db_session.commit()
    for t in [t1, t2]:
        await db_session.refresh(t)
    return [t1, t2]


@pytest.fixture
async def non_leaf_tag(db_session: AsyncSession) -> Tag:
    t = Tag(name="IT", category="industry", is_leaf=False, sort_order=1)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


class TestGetMe:
    async def test_authenticated_returns_profile(self, client):
        """GET /api/v1/users/me with valid token should return user."""
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["display_name"] == "Test User"
        assert data["role"] == "user"
        assert data["insight_score"] == 0.0

    async def test_unauthenticated_returns_401(self, client):
        """GET /api/v1/users/me without token should return 401."""
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401


class TestUpdateMe:
    async def test_update_display_name(self, client):
        """PATCH /api/v1/users/me should update display_name."""
        # First, create the user
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        # Then update
        resp = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
            json={"display_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    async def test_update_bio(self, client):
        """PATCH /api/v1/users/me should update bio."""
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        resp = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
            json={"bio": "My new bio"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "My new bio"


class TestGetUser:
    async def test_get_existing_user(self, client):
        """GET /api/v1/users/{id} should return public profile."""
        # Create user first
        me_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        user_id = me_resp.json()["id"]

        resp = await client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Test User"
        # Public profile should not include role
        assert "role" not in data

    async def test_get_nonexistent_user_returns_404(self, client):
        """GET /api/v1/users/{id} for unknown id should return 404."""
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 404


class TestOnboarding:
    async def test_complete_onboarding(self, client, leaf_tags):
        """PATCH with complete_onboarding=true should set onboarded_at."""
        await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
        resp = await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={
                "display_name": "Onboarded User",
                "bio": "Hello",
                "tag_ids": [str(t.id) for t in leaf_tags],
                "complete_onboarding": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["onboarded_at"] is not None
        assert data["display_name"] == "Onboarded User"

    async def test_onboarding_requires_display_name(self, client):
        """PATCH with complete_onboarding=true requires display_name."""
        await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
        resp = await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={
                "display_name": "",
                "complete_onboarding": True,
            },
        )
        assert resp.status_code == 422

    async def test_tag_ids_replace_existing(self, client, leaf_tags):
        """PATCH with tag_ids should replace existing user tags."""
        await client.get("/api/v1/users/me", headers=AUTH_HEADERS)

        # Set first tag
        await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={"tag_ids": [str(leaf_tags[0].id)]},
        )

        # Replace with second tag
        resp = await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={"tag_ids": [str(leaf_tags[1].id)]},
        )
        assert resp.status_code == 200

    async def test_invalid_tag_ids_returns_400(self, client, non_leaf_tag):
        """PATCH with non-leaf tag_ids should return 400."""
        await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
        resp = await client.patch(
            "/api/v1/users/me",
            headers=AUTH_HEADERS,
            json={"tag_ids": [str(non_leaf_tag.id)]},
        )
        assert resp.status_code == 400
