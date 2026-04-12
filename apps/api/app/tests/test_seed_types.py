import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seed_type import SeedType


@pytest.fixture
async def seed_types(db_session: AsyncSession) -> list[SeedType]:
    types = [
        SeedType(slug="query", name="疑問", description="疑問を投稿", sort_order=1),
        SeedType(slug="pain", name="悩み", description="悩みを投稿", sort_order=2),
        SeedType(slug="inactive", name="非表示", description="非表示", sort_order=3, is_active=False),
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
