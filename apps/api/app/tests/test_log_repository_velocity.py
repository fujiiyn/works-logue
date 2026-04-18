import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.log_repository import LogRepository


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1, is_active=True)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def repo(db_session: AsyncSession) -> LogRepository:
    return LogRepository(db_session)


class TestGetLogVelocities:
    async def test_counts_recent_logs(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        p = Planter(user_id=test_user.id, title="T", body="B", seed_type_id=seed_type.id)
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        # 3 logs within the window
        for i in range(3):
            log = Log(planter_id=p.id, user_id=test_user.id, body=f"Log {i}", created_at=now - timedelta(hours=i))
            db_session.add(log)
        # 1 log outside the window
        old_log = Log(planter_id=p.id, user_id=test_user.id, body="Old", created_at=now - timedelta(hours=100))
        db_session.add(old_log)
        await db_session.commit()

        velocities = await repo.get_log_velocities([p.id], window_hours=72)
        # 3 logs in 72 hours
        assert velocities[p.id] == pytest.approx(3.0 / 72.0)

    async def test_no_logs_returns_zero(self, repo, test_user, seed_type, db_session):
        p = Planter(user_id=test_user.id, title="T", body="B", seed_type_id=seed_type.id)
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        velocities = await repo.get_log_velocities([p.id], window_hours=72)
        assert velocities.get(p.id, 0.0) == 0.0

    async def test_multiple_planters(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        p1 = Planter(user_id=test_user.id, title="P1", body="B", seed_type_id=seed_type.id)
        p2 = Planter(user_id=test_user.id, title="P2", body="B", seed_type_id=seed_type.id)
        db_session.add_all([p1, p2])
        await db_session.commit()
        await db_session.refresh(p1)
        await db_session.refresh(p2)

        # p1: 2 logs, p2: 5 logs
        for i in range(2):
            db_session.add(Log(planter_id=p1.id, user_id=test_user.id, body=f"L{i}", created_at=now - timedelta(hours=i)))
        for i in range(5):
            db_session.add(Log(planter_id=p2.id, user_id=test_user.id, body=f"L{i}", created_at=now - timedelta(hours=i)))
        await db_session.commit()

        velocities = await repo.get_log_velocities([p1.id, p2.id], window_hours=72)
        assert velocities[p1.id] == pytest.approx(2.0 / 72.0)
        assert velocities[p2.id] == pytest.approx(5.0 / 72.0)
