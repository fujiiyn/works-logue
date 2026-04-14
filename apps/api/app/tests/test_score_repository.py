import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import LougeScoreSnapshot
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.score_repository import ScoreRepository


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="テスト用", sort_order=1, is_active=True)
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
async def planter(db_session: AsyncSession, test_user: User, seed_type: SeedType) -> Planter:
    p = Planter(
        user_id=test_user.id, title="Test Seed", body="Test body", seed_type_id=seed_type.id
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
async def trigger_log(db_session: AsyncSession, planter: Planter, test_user: User) -> Log:
    log = Log(
        planter_id=planter.id, user_id=test_user.id, body="Trigger log", is_ai_generated=False
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


@pytest.fixture
def repo(db_session: AsyncSession) -> ScoreRepository:
    return ScoreRepository(db_session)


class TestCreateSnapshot:
    async def test_create_snapshot(self, repo, planter, trigger_log):
        """create_snapshot() should insert a LougeScoreSnapshot."""
        snapshot = LougeScoreSnapshot(
            planter_id=planter.id,
            trigger_log_id=trigger_log.id,
            structure_fulfillment=0.75,
            maturity_scores=None,
            maturity_total=None,
            passed_structure=False,
            passed_maturity=None,
            structure_parts={"context": True, "problem": True, "solution": False, "name": False},
        )
        result = await repo.create_snapshot(snapshot)
        assert result.id is not None
        assert result.structure_fulfillment == 0.75
        assert result.passed_structure is False

    async def test_create_snapshot_with_structure_parts(self, repo, planter, trigger_log):
        """create_snapshot() should correctly save structure_parts JSONB."""
        parts = {"context": True, "problem": True, "solution": True, "name": True}
        snapshot = LougeScoreSnapshot(
            planter_id=planter.id,
            trigger_log_id=trigger_log.id,
            structure_fulfillment=1.0,
            maturity_scores={"comprehensiveness": 0.8, "diversity": 0.7, "counterarguments": 0.6, "specificity": 0.9},
            maturity_total=0.75,
            passed_structure=True,
            passed_maturity=True,
            structure_parts=parts,
        )
        result = await repo.create_snapshot(snapshot)
        assert result.structure_parts == parts


class TestGetLatestSnapshot:
    async def test_get_latest_snapshot(self, repo, planter, trigger_log, db_session):
        """get_latest_snapshot() should return the most recent snapshot."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            db_session.add(
                LougeScoreSnapshot(
                    planter_id=planter.id,
                    trigger_log_id=trigger_log.id,
                    structure_fulfillment=0.25 * (i + 1),
                    passed_structure=False,
                    structure_parts=None,
                    created_at=now + timedelta(seconds=i),
                )
            )
        await db_session.commit()

        result = await repo.get_latest_snapshot(planter.id)
        assert result is not None
        assert result.structure_fulfillment == 0.75

    async def test_get_latest_snapshot_none(self, repo, planter):
        """get_latest_snapshot() should return None when no snapshots exist."""
        result = await repo.get_latest_snapshot(planter.id)
        assert result is None
