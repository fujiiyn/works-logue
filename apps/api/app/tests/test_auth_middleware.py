import uuid

import pytest


class TestGetCurrentUser:
    async def test_valid_token_returns_user(self, client, mock_auth_user_sub):
        """Authenticated request should return user profile."""
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Test User"
        assert data["role"] == "user"

    async def test_no_token_returns_401(self, client):
        """Request without token should return 401."""
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_auto_creates_user_on_first_login(self, client, mock_auth_user_sub):
        """First login should auto-create user record (BR-02)."""
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Test User"
        assert data["insight_score"] == 0.0

    async def test_deleted_user_returns_403(self, client, db_session, mock_auth_user_sub):
        """Deleted user (deleted_at set) should get 403."""
        from datetime import datetime, timezone

        from app.models.user import User

        user = User(
            auth_id=mock_auth_user_sub,
            display_name="Deleted User",
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 403

    async def test_banned_user_can_read(self, client, db_session, mock_auth_user_sub):
        """Banned user should still be able to make GET requests."""
        from app.models.user import User

        user = User(
            auth_id=mock_auth_user_sub,
            display_name="Banned User",
            is_banned=True,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200

    async def test_banned_user_cannot_write(self, client, db_session, mock_auth_user_sub):
        """Banned user should get 403 on write operations."""
        from app.models.user import User

        user = User(
            auth_id=mock_auth_user_sub,
            display_name="Banned User",
            is_banned=True,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
            json={"display_name": "New Name"},
        )
        assert resp.status_code == 403


class TestGetOptionalUser:
    async def test_no_token_returns_none(self, client):
        """GET on public endpoint without token should work (user=None)."""
        resp = await client.get("/health")
        assert resp.status_code == 200
