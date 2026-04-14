import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.planter_repository import PlanterRepository


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query",
        name="疑問",
        description="疑問を投稿する",
        sort_order=1,
        is_active=True,
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        auth_id=uuid.uuid4(),
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def repo(db_session: AsyncSession) -> PlanterRepository:
    return PlanterRepository(db_session)


class TestCreate:
    async def test_create_planter(self, repo, test_user, seed_type):
        """create() should insert a new Planter and return it."""
        planter = Planter(
            user_id=test_user.id,
            title="Test Seed",
            body="Test body content",
            seed_type_id=seed_type.id,
        )
        result = await repo.create(planter)
        assert result.id is not None
        assert result.title == "Test Seed"
        assert result.status == "seed"
        assert result.log_count == 0
        assert result.progress == 0.0


class TestGetById:
    async def test_get_existing_planter(self, repo, test_user, seed_type):
        """get_by_id() should return the planter when it exists."""
        planter = Planter(
            user_id=test_user.id,
            title="Find Me",
            body="Body",
            seed_type_id=seed_type.id,
        )
        created = await repo.create(planter)

        result = await repo.get_by_id(created.id)
        assert result is not None
        assert result.title == "Find Me"

    async def test_get_deleted_returns_none(self, repo, test_user, seed_type, db_session):
        """get_by_id() should return None for soft-deleted planters."""
        planter = Planter(
            user_id=test_user.id,
            title="Deleted",
            body="Body",
            seed_type_id=seed_type.id,
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(planter)
        await db_session.commit()
        await db_session.refresh(planter)

        result = await repo.get_by_id(planter.id)
        assert result is None

    async def test_get_nonexistent_returns_none(self, repo):
        """get_by_id() should return None for unknown IDs."""
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None


class TestListRecent:
    async def test_list_ordered_by_created_at_desc(self, repo, test_user, seed_type, db_session):
        """list_recent() should return planters ordered by created_at DESC."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            p = Planter(
                user_id=test_user.id,
                title=f"Seed {i}",
                body=f"Body {i}",
                seed_type_id=seed_type.id,
                created_at=now + timedelta(seconds=i),
            )
            db_session.add(p)
        await db_session.commit()

        results = await repo.list_recent(limit=10)
        assert len(results) == 3
        assert results[0].title == "Seed 2"
        assert results[1].title == "Seed 1"
        assert results[2].title == "Seed 0"

    async def test_cursor_pagination(self, repo, test_user, seed_type, db_session):
        """list_recent() should support cursor-based pagination."""
        now = datetime.now(timezone.utc)
        planters = []
        for i in range(5):
            p = Planter(
                user_id=test_user.id,
                title=f"Seed {i}",
                body=f"Body {i}",
                seed_type_id=seed_type.id,
                created_at=now + timedelta(seconds=i),
            )
            db_session.add(p)
            planters.append(p)
        await db_session.commit()
        for p in planters:
            await db_session.refresh(p)

        # First page: 3 items
        page1 = await repo.list_recent(limit=3)
        assert len(page1) == 3
        assert page1[0].title == "Seed 4"

        # Second page using cursor from last item of page1
        last = page1[-1]
        page2 = await repo.list_recent(
            cursor_created_at=last.created_at,
            cursor_id=last.id,
            limit=3,
        )
        assert len(page2) == 2
        assert page2[0].title == "Seed 1"

    async def test_excludes_deleted(self, repo, test_user, seed_type, db_session):
        """list_recent() should exclude soft-deleted planters."""
        p1 = Planter(
            user_id=test_user.id,
            title="Active",
            body="Body",
            seed_type_id=seed_type.id,
        )
        p2 = Planter(
            user_id=test_user.id,
            title="Deleted",
            body="Body",
            seed_type_id=seed_type.id,
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add_all([p1, p2])
        await db_session.commit()

        results = await repo.list_recent(limit=10)
        assert len(results) == 1
        assert results[0].title == "Active"

    async def test_excludes_archived(self, repo, test_user, seed_type, db_session):
        """list_recent() should exclude archived planters."""
        p1 = Planter(
            user_id=test_user.id,
            title="Active",
            body="Body",
            seed_type_id=seed_type.id,
        )
        p2 = Planter(
            user_id=test_user.id,
            title="Archived",
            body="Body",
            seed_type_id=seed_type.id,
            status="archived",
        )
        db_session.add_all([p1, p2])
        await db_session.commit()

        results = await repo.list_recent(limit=10)
        assert len(results) == 1
        assert results[0].title == "Active"


class TestUpdateScores:
    async def test_update_scores(self, repo, test_user, seed_type, db_session):
        """update_scores() should update score-related fields and status."""
        planter = Planter(
            user_id=test_user.id, title="Score", body="Body", seed_type_id=seed_type.id
        )
        created = await repo.create(planter)

        await repo.update_scores(
            created.id,
            structure_fulfillment=0.75,
            maturity_score=0.6,
            progress=0.5,
            status="sprout",
        )
        await db_session.refresh(created)
        assert created.structure_fulfillment == 0.75
        assert created.maturity_score == 0.6
        assert created.progress == 0.5
        assert created.status == "sprout"


class TestIncrementLogCount:
    async def test_increment_log_count(self, repo, test_user, seed_type, db_session):
        """increment_log_count() should increment log_count by 1."""
        planter = Planter(
            user_id=test_user.id, title="Count", body="Body", seed_type_id=seed_type.id
        )
        created = await repo.create(planter)
        assert created.log_count == 0

        await repo.increment_log_count(created.id)
        await db_session.refresh(created)
        assert created.log_count == 1

        await repo.increment_log_count(created.id)
        await db_session.refresh(created)
        assert created.log_count == 2


class TestUpdateContributorCount:
    async def test_update_contributor_count(self, repo, test_user, seed_type, db_session):
        """update_contributor_count() should set contributor_count to given value."""
        planter = Planter(
            user_id=test_user.id, title="Contributors", body="Body", seed_type_id=seed_type.id
        )
        created = await repo.create(planter)

        await repo.update_contributor_count(created.id, 5)
        await db_session.refresh(created)
        assert created.contributor_count == 5


class TestUpdateLougeContent:
    async def test_update_louge_content(self, repo, test_user, seed_type, db_session):
        """update_louge_content() should set louge_content and louge_generated_at."""
        planter = Planter(
            user_id=test_user.id, title="Louge", body="Body", seed_type_id=seed_type.id,
            status="louge",
        )
        created = await repo.create(planter)
        assert created.louge_content is None
        assert created.louge_generated_at is None

        now = datetime.now(timezone.utc)
        await repo.update_louge_content(created.id, "# Article", now)
        await db_session.refresh(created)
        assert created.louge_content == "# Article"
        assert created.louge_generated_at is not None
