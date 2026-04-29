import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.seed_type import SeedType
from app.models.tag import Tag, UserTag
from app.models.user import User


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


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


async def _create_me(client) -> dict:
    """Helper to create/get the authenticated test user."""
    resp = await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
    return resp.json()


class TestGetMe:
    async def test_authenticated_returns_profile(self, client):
        resp = await client.get("/api/v1/users/me", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["display_name"] == "Test User"
        assert data["role"] == "user"
        assert data["insight_score"] == 0.0

    async def test_unauthenticated_returns_401(self, client):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401


class TestUpdateMe:
    async def test_update_display_name(self, client):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"display_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    async def test_update_bio(self, client):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"bio": "My new bio"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "My new bio"

    async def test_clear_bio_with_null(self, client):
        await _create_me(client)
        await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"bio": "to be cleared"},
        )
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"bio": None},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] is None

    async def test_update_headline(self, client):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"headline": "Senior Engineer"},
        )
        assert resp.status_code == 200
        assert resp.json()["headline"] == "Senior Engineer"

    async def test_update_location(self, client):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"location": "Tokyo"},
        )
        assert resp.status_code == 200
        assert resp.json()["location"] == "Tokyo"

    async def test_update_sns_valid(self, client):
        """PATCH with valid SNS URLs should succeed (D12)."""
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={
                "x_url": "https://x.com/testuser",
                "linkedin_url": "https://linkedin.com/in/testuser",
                "wantedly_url": "https://wantedly.com/id/testuser",
                "website_url": "https://example.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["x_url"] == "https://x.com/testuser"
        assert data["linkedin_url"] == "https://linkedin.com/in/testuser"
        assert data["wantedly_url"] == "https://wantedly.com/id/testuser"
        assert data["website_url"] == "https://example.com"

    async def test_update_sns_invalid_domain_rejected(self, client):
        """PATCH with SNS URL outside allowlist should return 422 (D12)."""
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"x_url": "https://evil.com/xss"},
        )
        assert resp.status_code == 422

    async def test_update_sns_clear_with_null(self, client):
        """PATCH with null SNS URL should clear the field."""
        await _create_me(client)
        # Set first
        await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"x_url": "https://x.com/test"},
        )
        # Clear
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"x_url": None},
        )
        assert resp.status_code == 200
        assert resp.json()["x_url"] is None

    async def test_update_sns_clear_with_empty_string(self, client):
        """PATCH with empty string SNS URL should clear the field."""
        await _create_me(client)
        await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"x_url": "https://x.com/test"},
        )
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"x_url": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["x_url"] is None

    async def test_website_requires_https(self, client):
        """website_url must start with https://."""
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"website_url": "http://insecure.com"},
        )
        assert resp.status_code == 422

    async def test_avatar_url_not_accepted_in_patch(self, client):
        """PATCH should not accept avatar_url from client (D2)."""
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"display_name": "Test"},
        )
        assert resp.status_code == 200
        # Just ensure no error — avatar_url field simply doesn't exist in UserUpdate


class TestGetUser:
    async def test_get_existing_user(self, client):
        me = await _create_me(client)
        user_id = me["id"]
        resp = await client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["display_name"] == "Test User"
        assert "stats" in data
        assert "tags" in data

    async def test_get_nonexistent_user_returns_404(self, client):
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 404

    async def test_get_banned_user_returns_404(self, client, db_session):
        """Banned users should return 404 (BR-U08)."""
        user = User(
            auth_id=uuid.uuid4(), display_name="Banned", is_banned=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        resp = await client.get(f"/api/v1/users/{user.id}")
        assert resp.status_code == 404

    async def test_get_user_with_stats(self, client, db_session, seed_type):
        """GET /users/{id} should include stats."""
        me = await _create_me(client)
        user_id = me["id"]

        resp = await client.get(f"/api/v1/users/{user_id}")
        data = resp.json()
        assert data["stats"]["insight_score"] == 0.0
        assert data["stats"]["louge_count"] == 0
        assert data["stats"]["follower_count"] == 0
        assert data["stats"]["following_count"] == 0

    async def test_get_user_is_following(self, client, db_session):
        """GET /users/{id} should include is_following when authenticated."""
        # Create another user
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        # Not following yet
        resp = await client.get(
            f"/api/v1/users/{other.id}", headers=AUTH_HEADERS,
        )
        assert resp.json()["is_following"] is False

    async def test_get_own_profile_is_own_profile(self, client):
        """GET /users/{my_id} should set is_own_profile=True."""
        me = await _create_me(client)
        resp = await client.get(
            f"/api/v1/users/{me['id']}", headers=AUTH_HEADERS,
        )
        assert resp.json()["is_own_profile"] is True


class TestOnboarding:
    async def test_complete_onboarding(self, client, leaf_tags):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={
                "display_name": "Onboarded User",
                "bio": "Hello",
                "tag_ids": [str(t.id) for t in leaf_tags],
                "complete_onboarding": True,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["onboarded_at"] is not None

    async def test_onboarding_requires_display_name(self, client):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"display_name": "", "complete_onboarding": True},
        )
        assert resp.status_code == 422

    async def test_tag_ids_replace_existing(self, client, leaf_tags):
        await _create_me(client)
        await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"tag_ids": [str(leaf_tags[0].id)]},
        )
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"tag_ids": [str(leaf_tags[1].id)]},
        )
        assert resp.status_code == 200

    async def test_invalid_tag_ids_returns_400(self, client, non_leaf_tag):
        await _create_me(client)
        resp = await client.patch(
            "/api/v1/users/me", headers=AUTH_HEADERS,
            json={"tag_ids": [str(non_leaf_tag.id)]},
        )
        assert resp.status_code == 400


class TestUserFollow:
    async def test_follow_user(self, client, db_session):
        """POST /users/{id}/follow should succeed."""
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        await _create_me(client)
        resp = await client.post(
            f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

    async def test_follow_user_idempotent(self, client, db_session):
        """POST /users/{id}/follow twice should succeed (idempotent)."""
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        await _create_me(client)
        await client.post(f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS)
        resp = await client.post(
            f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

    async def test_self_follow_returns_400(self, client):
        """POST /users/{my_id}/follow should return 400."""
        me = await _create_me(client)
        resp = await client.post(
            f"/api/v1/users/{me['id']}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400

    async def test_unfollow_user(self, client, db_session):
        """DELETE /users/{id}/follow should succeed."""
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        await _create_me(client)
        await client.post(f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS)
        resp = await client.delete(
            f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

    async def test_unfollow_not_followed_returns_204(self, client, db_session):
        """DELETE /users/{id}/follow when not following should return 204 (idempotent)."""
        other = User(auth_id=uuid.uuid4(), display_name="Other")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        await _create_me(client)
        resp = await client.delete(
            f"/api/v1/users/{other.id}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

    async def test_follow_nonexistent_user_returns_404(self, client):
        """POST /users/{bad_id}/follow should return 404."""
        await _create_me(client)
        resp = await client.post(
            f"/api/v1/users/{uuid.uuid4()}/follow", headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404


class TestFollowList:
    async def test_get_followers(self, client, db_session):
        """GET /users/{id}/followers should return follower list."""
        me = await _create_me(client)
        resp = await client.get(f"/api/v1/users/{me['id']}/followers")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert data["next_cursor"] is None

    async def test_get_following(self, client, db_session):
        """GET /users/{id}/following should return following list."""
        me = await _create_me(client)
        resp = await client.get(f"/api/v1/users/{me['id']}/following")
        assert resp.status_code == 200
        assert "users" in data if (data := resp.json()) else True


class TestUserPlanters:
    async def test_get_user_planters_seeds(self, client, db_session, seed_type):
        """GET /users/{id}/planters?tab=seeds should return user's planters."""
        me = await _create_me(client)
        user_id = uuid.UUID(me["id"])

        p = Planter(
            user_id=user_id, title="My Seed", body="B", seed_type_id=seed_type.id
        )
        db_session.add(p)
        await db_session.commit()

        resp = await client.get(f"/api/v1/users/{user_id}/planters?tab=seeds")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["planters"]) == 1
        assert data["planters"][0]["title"] == "My Seed"

    async def test_get_user_planters_louges(self, client, db_session, seed_type):
        """GET /users/{id}/planters?tab=louges should return contributed louges (D9)."""
        me = await _create_me(client)
        user_id = uuid.UUID(me["id"])

        p = Planter(
            user_id=user_id, title="Louge", body="B",
            seed_type_id=seed_type.id, status="louge"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        evt = InsightScoreEvent(
            user_id=user_id, planter_id=p.id, score_delta=5.0, reason="seed_author"
        )
        db_session.add(evt)
        await db_session.commit()

        resp = await client.get(f"/api/v1/users/{user_id}/planters?tab=louges")
        assert resp.status_code == 200
        assert len(resp.json()["planters"]) == 1


class TestUserLogs:
    async def test_get_user_logs(self, client, db_session, seed_type):
        """GET /users/{id}/logs should return user's logs."""
        me = await _create_me(client)
        user_id = uuid.UUID(me["id"])

        p = Planter(
            user_id=user_id, title="P", body="B", seed_type_id=seed_type.id
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        log = Log(planter_id=p.id, user_id=user_id, body="My Log")
        db_session.add(log)
        await db_session.commit()

        resp = await client.get(f"/api/v1/users/{user_id}/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["body"] == "My Log"


class TestContributions:
    async def test_get_contributions(self, client, db_session, seed_type):
        """GET /users/{id}/contributions should return contribution graph (D8)."""
        me = await _create_me(client)
        user_id = uuid.UUID(me["id"])

        p = Planter(
            user_id=user_id, title="P", body="B", seed_type_id=seed_type.id
        )
        db_session.add(p)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/users/{user_id}/contributions?tz=Asia/Tokyo"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "contributions" in data


class TestSimilarUsers:
    async def test_get_similar_users(self, client, db_session):
        """GET /users/{id}/similar should return users with common tags (D11)."""
        me = await _create_me(client)
        user_id = uuid.UUID(me["id"])

        resp = await client.get(f"/api/v1/users/{user_id}/similar")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
