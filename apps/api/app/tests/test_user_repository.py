import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.seed_type import SeedType
from app.models.tag import Tag, UserTag
from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Test User", headline="Engineer")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Other User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


class TestGetById:
    async def test_get_existing_user(self, repo, test_user):
        user = await repo.get_by_id(test_user.id)
        assert user is not None
        assert user.id == test_user.id

    async def test_get_nonexistent_user(self, repo):
        user = await repo.get_by_id(uuid.uuid4())
        assert user is None

    async def test_get_deleted_user_returns_none(self, repo, db_session):
        user = User(
            auth_id=uuid.uuid4(),
            display_name="Deleted",
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        assert await repo.get_by_id(user.id) is None

    async def test_get_banned_user_returns_none(self, repo, db_session):
        user = User(
            auth_id=uuid.uuid4(),
            display_name="Banned",
            is_banned=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        assert await repo.get_by_id(user.id) is None


class TestLougeCount:
    async def test_louge_count_seed_author(self, repo, test_user, seed_type, db_session):
        """Count louges where user is the seed author."""
        # Louge planter authored by test_user
        p = Planter(
            user_id=test_user.id, title="Louge", body="B", seed_type_id=seed_type.id, status="louge"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        # Need insight_score_event with score > 0 (D9)
        evt = InsightScoreEvent(
            user_id=test_user.id, planter_id=p.id, score_delta=5.0, reason="seed_author"
        )
        db_session.add(evt)
        await db_session.commit()

        count = await repo.get_louge_count(test_user.id)
        assert count == 1

    async def test_louge_count_log_contributor(self, repo, test_user, other_user, seed_type, db_session):
        """Count louges where user contributed via log (D9: insight_score > 0)."""
        p = Planter(
            user_id=other_user.id, title="Louge", body="B", seed_type_id=seed_type.id, status="louge"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        # test_user contributed with positive score
        evt = InsightScoreEvent(
            user_id=test_user.id, planter_id=p.id, score_delta=3.0, reason="log_contribution"
        )
        db_session.add(evt)
        await db_session.commit()

        count = await repo.get_louge_count(test_user.id)
        assert count == 1

    async def test_louge_count_excludes_zero_score(self, repo, test_user, other_user, seed_type, db_session):
        """D9: Zero score contributions should not count."""
        p = Planter(
            user_id=other_user.id, title="Louge", body="B", seed_type_id=seed_type.id, status="louge"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        # Zero score
        evt = InsightScoreEvent(
            user_id=test_user.id, planter_id=p.id, score_delta=0.0, reason="minimal"
        )
        db_session.add(evt)
        await db_session.commit()

        count = await repo.get_louge_count(test_user.id)
        assert count == 0

    async def test_louge_count_deduplicates(self, repo, test_user, seed_type, db_session):
        """Same planter as both seed author and log contributor should count once."""
        p = Planter(
            user_id=test_user.id, title="Louge", body="B", seed_type_id=seed_type.id, status="louge"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        # Two events on same planter
        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p.id, score_delta=5.0, reason="seed_author"
        ))
        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p.id, score_delta=2.0, reason="log"
        ))
        await db_session.commit()

        count = await repo.get_louge_count(test_user.id)
        assert count == 1


class TestFeaturedContribution:
    async def test_featured_contribution(self, repo, test_user, seed_type, db_session):
        """Should return the planter with highest total score."""
        p1 = Planter(
            user_id=test_user.id, title="Low", body="B", seed_type_id=seed_type.id, status="louge"
        )
        p2 = Planter(
            user_id=test_user.id, title="High", body="B", seed_type_id=seed_type.id, status="louge"
        )
        db_session.add_all([p1, p2])
        await db_session.commit()
        await db_session.refresh(p1)
        await db_session.refresh(p2)

        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p1.id, score_delta=3.0, reason="r"
        ))
        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p2.id, score_delta=10.0, reason="r"
        ))
        await db_session.commit()

        featured = await repo.get_featured_contribution(test_user.id)
        assert featured is not None
        assert featured["planter_id"] == p2.id
        assert featured["total_score"] == 10.0

    async def test_featured_contribution_none(self, repo, test_user):
        """Should return None if no louge contributions."""
        featured = await repo.get_featured_contribution(test_user.id)
        assert featured is None


class TestContributionGraph:
    async def test_contribution_graph(self, repo, test_user, seed_type, db_session):
        """Should return daily seed+log counts."""
        now = datetime.now(timezone.utc)
        p = Planter(
            user_id=test_user.id, title="P", body="B", seed_type_id=seed_type.id,
            created_at=now,
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        log = Log(planter_id=p.id, user_id=test_user.id, body="Log", created_at=now)
        db_session.add(log)
        await db_session.commit()

        graph = await repo.get_contribution_graph(test_user.id, tz="UTC")
        assert len(graph) > 0
        today_entry = [g for g in graph if g["date"] == now.date()]
        assert len(today_entry) == 1
        assert today_entry[0]["count"] == 2  # 1 seed + 1 log


class TestUserPlanters:
    async def test_get_user_planters_seeds(self, repo, test_user, seed_type, db_session):
        """Should return planters authored by user."""
        p = Planter(
            user_id=test_user.id, title="My Seed", body="B", seed_type_id=seed_type.id
        )
        db_session.add(p)
        await db_session.commit()

        planters, cursor = await repo.get_user_planters(test_user.id, tab="seeds")
        assert len(planters) == 1
        assert planters[0].title == "My Seed"

    async def test_get_user_planters_louges(self, repo, test_user, other_user, seed_type, db_session):
        """tab=louges should include Louges where user contributed with score > 0 (D9)."""
        # Authored louge
        p1 = Planter(
            user_id=test_user.id, title="Authored Louge", body="B",
            seed_type_id=seed_type.id, status="louge"
        )
        # Other's louge, test_user contributed
        p2 = Planter(
            user_id=other_user.id, title="Contributed Louge", body="B",
            seed_type_id=seed_type.id, status="louge"
        )
        db_session.add_all([p1, p2])
        await db_session.commit()
        await db_session.refresh(p1)
        await db_session.refresh(p2)

        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p1.id, score_delta=5.0, reason="author"
        ))
        db_session.add(InsightScoreEvent(
            user_id=test_user.id, planter_id=p2.id, score_delta=3.0, reason="log"
        ))
        await db_session.commit()

        planters, cursor = await repo.get_user_planters(test_user.id, tab="louges")
        assert len(planters) == 2


class TestUserLogs:
    async def test_get_user_logs(self, repo, test_user, seed_type, db_session):
        """Should return logs authored by user with planter info."""
        p = Planter(
            user_id=test_user.id, title="Planter", body="B", seed_type_id=seed_type.id
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        log = Log(planter_id=p.id, user_id=test_user.id, body="My Log")
        db_session.add(log)
        await db_session.commit()

        logs, cursor = await repo.get_user_logs(test_user.id)
        assert len(logs) == 1
        assert logs[0]["body"] == "My Log"
        assert logs[0]["planter_title"] == "Planter"


class TestSimilarUsers:
    async def test_similar_users(self, repo, test_user, other_user, db_session):
        """Should return users with common tags, sorted by count."""
        tag = Tag(name="Python", category="skill")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        db_session.add(UserTag(user_id=test_user.id, tag_id=tag.id))
        db_session.add(UserTag(user_id=other_user.id, tag_id=tag.id))
        await db_session.commit()

        similar = await repo.get_similar_users(test_user.id, exclude_user_ids=[])
        assert len(similar) == 1
        assert similar[0]["user_id"] == other_user.id
        assert similar[0]["common_tag_count"] == 1

    async def test_similar_users_excludes_self(self, repo, test_user, db_session):
        """Should not include the user themselves."""
        tag = Tag(name="Go", category="skill")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        db_session.add(UserTag(user_id=test_user.id, tag_id=tag.id))
        await db_session.commit()

        similar = await repo.get_similar_users(test_user.id, exclude_user_ids=[])
        assert len(similar) == 0

    async def test_similar_users_excludes_followed(self, repo, test_user, other_user, db_session):
        """With exclude_user_ids, followed users should be excluded."""
        tag = Tag(name="Rust", category="skill")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        db_session.add(UserTag(user_id=test_user.id, tag_id=tag.id))
        db_session.add(UserTag(user_id=other_user.id, tag_id=tag.id))
        await db_session.commit()

        similar = await repo.get_similar_users(
            test_user.id, exclude_user_ids=[other_user.id]
        )
        assert len(similar) == 0
