import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.insight_repository import InsightScoreRepository


async def _create_user(db: AsyncSession, display_name: str = "Test User") -> User:
    user = User(
        auth_id=uuid.uuid4(),
        display_name=display_name,
        insight_score=0.0,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _create_seed_type(db: AsyncSession) -> SeedType:
    st = SeedType(name="疑問", slug="query", description="test", sort_order=1)
    db.add(st)
    await db.flush()
    await db.refresh(st)
    return st


async def _create_planter(db: AsyncSession, user: User, seed_type: SeedType) -> Planter:
    planter = Planter(
        user_id=user.id,
        title="Test Seed",
        body="Test body",
        seed_type_id=seed_type.id,
        status="louge",
    )
    db.add(planter)
    await db.flush()
    await db.refresh(planter)
    return planter


class TestInsightScoreRepository:
    async def test_create_events(self, db_session: AsyncSession):
        """create_events() should save InsightScoreEvent records to DB."""
        user = await _create_user(db_session)
        seed_type = await _create_seed_type(db_session)
        planter = await _create_planter(db_session, user, seed_type)

        events = [
            InsightScoreEvent(
                user_id=user.id,
                planter_id=planter.id,
                log_id=None,
                score_delta=1.0,
                reason="seed_author",
            ),
        ]

        repo = InsightScoreRepository(db_session)
        await repo.create_events(events)
        await db_session.commit()

        result = await repo.get_by_planter(planter.id)
        assert len(result) == 1
        assert result[0].score_delta == 1.0

    async def test_get_by_planter(self, db_session: AsyncSession):
        """get_by_planter() should return all events for a planter."""
        user1 = await _create_user(db_session, "User 1")
        user2 = await _create_user(db_session, "User 2")
        seed_type = await _create_seed_type(db_session)
        planter = await _create_planter(db_session, user1, seed_type)

        events = [
            InsightScoreEvent(
                user_id=user1.id,
                planter_id=planter.id,
                log_id=None,
                score_delta=1.0,
                reason="seed_author",
            ),
            InsightScoreEvent(
                user_id=user2.id,
                planter_id=planter.id,
                log_id=None,
                score_delta=0.85,
                reason="log_contribution",
            ),
        ]

        repo = InsightScoreRepository(db_session)
        await repo.create_events(events)
        await db_session.commit()

        result = await repo.get_by_planter(planter.id)
        assert len(result) == 2

    async def test_update_user_scores(self, db_session: AsyncSession):
        """update_user_scores() should add score_delta to users.insight_score."""
        user = await _create_user(db_session, "Score User")
        assert user.insight_score == 0.0

        repo = InsightScoreRepository(db_session)
        await repo.update_user_scores({user.id: 2.5})
        await db_session.commit()

        await db_session.refresh(user)
        assert user.insight_score == 2.5
