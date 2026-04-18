import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import PlanterTag, Tag
from app.models.user import User


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession, mock_auth_user_sub) -> User:
    user = User(auth_id=mock_auth_user_sub, display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_planter(
    db: AsyncSession, user: User, seed_type: SeedType,
    *, title: str = "Test", status: str = "seed",
    created_at: datetime | None = None,
) -> Planter:
    p = Planter(user_id=user.id, title=title, body="Body content", seed_type_id=seed_type.id, status=status)
    if created_at:
        p.created_at = created_at
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


class TestSearchEndpoint:
    async def test_keyword_search(self, client, db_session, test_user, seed_type):
        await _create_planter(db_session, test_user, seed_type, title="人事評価の悩み")
        await _create_planter(db_session, test_user, seed_type, title="マーケティング施策")

        resp = await client.get("/api/v1/search?keyword=人事")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "人事評価の悩み"

    async def test_tag_filter(self, client, db_session, test_user, seed_type):
        tag = Tag(name="SaaS", category="industry", is_leaf=True, sort_order=1)
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        p1 = await _create_planter(db_session, test_user, seed_type, title="Tagged")
        await _create_planter(db_session, test_user, seed_type, title="Untagged")

        pt = PlanterTag(planter_id=p1.id, tag_id=tag.id)
        db_session.add(pt)
        await db_session.commit()

        resp = await client.get(f"/api/v1/search?tag_ids={tag.id}")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Tagged"

    async def test_status_filter(self, client, db_session, test_user, seed_type):
        await _create_planter(db_session, test_user, seed_type, title="S", status="seed")
        await _create_planter(db_session, test_user, seed_type, title="Sp", status="sprout")

        resp = await client.get("/api/v1/search?status=sprout")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Sp"

    async def test_combined_filters(self, client, db_session, test_user, seed_type):
        tag = Tag(name="HR", category="occupation", is_leaf=True, sort_order=1)
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        p1 = await _create_planter(db_session, test_user, seed_type, title="人事の悩み", status="sprout")
        p2 = await _create_planter(db_session, test_user, seed_type, title="人事の種", status="seed")
        for p in [p1, p2]:
            db_session.add(PlanterTag(planter_id=p.id, tag_id=tag.id))
        await db_session.commit()

        resp = await client.get(f"/api/v1/search?keyword=人事&tag_ids={tag.id}&status=sprout")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "人事の悩み"

    async def test_pagination(self, client, db_session, test_user, seed_type):
        now = datetime.now(timezone.utc)
        for i in range(5):
            await _create_planter(
                db_session, test_user, seed_type,
                title=f"Item {i}", created_at=now + timedelta(seconds=i),
            )

        resp = await client.get("/api/v1/search?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["has_next"] is True
        assert data["next_cursor"] is not None

        resp2 = await client.get(f"/api/v1/search?limit=3&cursor={data['next_cursor']}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 2

    async def test_no_filters_returns_all(self, client, db_session, test_user, seed_type):
        await _create_planter(db_session, test_user, seed_type, title="A")
        await _create_planter(db_session, test_user, seed_type, title="B")

        resp = await client.get("/api/v1/search")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2
