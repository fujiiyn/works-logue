
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seed_type import SeedType


@pytest.fixture
async def seed_types(db_session: AsyncSession) -> list[SeedType]:
    types = [
        SeedType(slug="query", name="疑問", description="疑問を投稿", sort_order=1),
        SeedType(slug="pain", name="悩み", description="悩みを投稿", sort_order=2),
        SeedType(
            slug="inactive",
            name="非表示",
            description="非表示",
            sort_order=3,
            is_active=False,
        ),
    ]
    db_session.add_all(types)
    await db_session.commit()
    return types


class TestListSeedTypes:
    async def test_returns_active_seed_types(self, client, seed_types):
        """GET /api/v1/seed-types should return active seed types."""
        resp = await client.get("/api/v1/seed-types")
        assert resp.status_code == 200
        data = resp.json()
        names = [st["name"] for st in data]
        assert "疑問" in names
        assert "悩み" in names

    async def test_excludes_inactive(self, client, seed_types):
        """GET /api/v1/seed-types should exclude inactive types."""
        resp = await client.get("/api/v1/seed-types")
        data = resp.json()
        slugs = [st["slug"] for st in data]
        assert "inactive" not in slugs

    async def test_ordered_by_sort_order(self, client, seed_types):
        """GET /api/v1/seed-types should be ordered by sort_order ASC."""
        resp = await client.get("/api/v1/seed-types")
        data = resp.json()
        assert data[0]["slug"] == "query"
        assert data[1]["slug"] == "pain"


class TestSeedTypeAdminToggleContract:
    """BR-A17: deactivating a seed_type via admin API must hide it from
    the public /seed-types endpoint immediately. This test pins the U2
    public-endpoint behavior (`is_active=true` filter) as a contract so a
    future "show all" change cannot silently leak inactive types to feeds.
    """

    async def test_inactive_seed_type_hidden_from_public_endpoint(
        self, client, db_session, mock_auth_user_sub
    ):
        from app.models.user import User

        admin = User(
            auth_id=mock_auth_user_sub,
            display_name="Admin",
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        st = SeedType(
            slug="contract-toggle",
            name="contract-toggle",
            description="d",
            sort_order=99,
            is_active=True,
        )
        db_session.add(st)
        await db_session.commit()

        # Visible while active.
        resp = await client.get("/api/v1/seed-types")
        slugs = [it["slug"] for it in resp.json()]
        assert "contract-toggle" in slugs

        # Toggle off via admin endpoint.
        resp = await client.post(
            f"/api/v1/admin/seed-types/{st.id}/toggle-active",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Hidden after toggle.
        resp = await client.get("/api/v1/seed-types")
        slugs = [it["slug"] for it in resp.json()]
        assert "contract-toggle" not in slugs
