import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import PlanterFollow
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.follow_repository import FollowRepository


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def planter(db_session: AsyncSession, test_user, seed_type) -> Planter:
    p = Planter(
        user_id=test_user.id, title="Test", body="Body", seed_type_id=seed_type.id
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def repo(db_session: AsyncSession) -> FollowRepository:
    return FollowRepository(db_session)


class TestFollowPlanter:
    async def test_follow_success(self, repo, test_user, planter, db_session):
        """follow_planter() should create a PlanterFollow record."""
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()

        result = await db_session.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == test_user.id,
                PlanterFollow.planter_id == planter.id,
            )
        )
        assert result.scalar_one_or_none() is not None

    async def test_follow_duplicate_no_error(self, repo, test_user, planter, db_session):
        """follow_planter() should not raise on duplicate follow."""
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()
        # Should not raise
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()
