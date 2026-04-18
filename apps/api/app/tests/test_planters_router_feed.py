import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.planter_view import PlanterView
from app.models.seed_type import SeedType
from app.models.user import User

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


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
    db: AsyncSession,
    user: User,
    seed_type: SeedType,
    *,
    title: str = "Test",
    status: str = "seed",
    created_at: datetime | None = None,
    louge_generated_at: datetime | None = None,
    structure_fulfillment: float = 0.0,
) -> Planter:
    p = Planter(
        user_id=user.id,
        title=title,
        body="Body",
        seed_type_id=seed_type.id,
        status=status,
        structure_fulfillment=structure_fulfillment,
    )
    if created_at:
        p.created_at = created_at
    if louge_generated_at:
        p.louge_generated_at = louge_generated_at
        p.louge_content = "# Article"
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


class TestListPlantersTabRecent:
    async def test_default_tab_is_recent(self, client, db_session, test_user, seed_type):
        await _create_planter(db_session, test_user, seed_type, title="Seed A")

        resp = await client.get("/api/v1/planters")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Seed A"

    async def test_tab_recent_explicit(self, client, db_session, test_user, seed_type):
        await _create_planter(db_session, test_user, seed_type, title="Seed B")

        resp = await client.get("/api/v1/planters?tab=recent")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1


class TestListPlantersTabTrending:
    async def test_trending_returns_ranked(self, client, db_session, test_user, seed_type):
        now = datetime.now(timezone.utc)

        # p1: low views, high velocity
        p1 = await _create_planter(
            db_session, test_user, seed_type,
            title="High Velocity", created_at=now - timedelta(hours=1),
        )
        for i in range(5):
            db_session.add(Log(planter_id=p1.id, user_id=test_user.id, body=f"L{i}", created_at=now - timedelta(hours=i)))

        # p2: high views, low velocity
        p2 = await _create_planter(
            db_session, test_user, seed_type,
            title="High Views", created_at=now - timedelta(hours=2),
        )
        user2 = User(auth_id=uuid.uuid4(), display_name="User2")
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)
        for u in [test_user, user2]:
            db_session.add(PlanterView(planter_id=p2.id, user_id=u.id, viewed_at=now))

        await db_session.commit()

        resp = await client.get("/api/v1/planters?tab=trending")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2


class TestListPlantersTabBloomed:
    async def test_bloomed_returns_louge_only(self, client, db_session, test_user, seed_type):
        now = datetime.now(timezone.utc)
        await _create_planter(db_session, test_user, seed_type, title="Seed", status="seed")
        await _create_planter(
            db_session, test_user, seed_type,
            title="Bloomed", status="louge", louge_generated_at=now,
        )

        resp = await client.get("/api/v1/planters?tab=bloomed")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Bloomed"


class TestRecordView:
    async def test_record_view_authenticated(self, client, db_session, test_user, seed_type):
        p = await _create_planter(db_session, test_user, seed_type, title="ViewMe")

        resp = await client.post(f"/api/v1/planters/{p.id}/view", headers=AUTH_HEADERS)
        assert resp.status_code == 204

    async def test_record_view_unauthenticated(self, client, db_session, test_user, seed_type):
        p = await _create_planter(db_session, test_user, seed_type, title="ViewMe")

        # Without auth header - should still return 204 and record view
        resp = await client.post(f"/api/v1/planters/{p.id}/view")
        assert resp.status_code == 204
