import uuid


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
