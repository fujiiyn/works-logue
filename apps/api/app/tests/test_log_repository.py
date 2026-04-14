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
async def another_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Another User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def planter(db_session: AsyncSession, test_user: User, seed_type: SeedType) -> Planter:
    p = Planter(
        user_id=test_user.id,
        title="Test Seed",
        body="Test body",
        seed_type_id=seed_type.id,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def repo(db_session: AsyncSession) -> LogRepository:
    return LogRepository(db_session)


class TestCreate:
    async def test_create_user_log(self, repo, planter, test_user):
        """create() should insert a user Log and return it."""
        log = Log(
            planter_id=planter.id, user_id=test_user.id, body="My log", is_ai_generated=False
        )
        result = await repo.create(log)
        assert result.id is not None
        assert result.planter_id == planter.id
        assert result.user_id == test_user.id
        assert result.body == "My log"
        assert result.is_ai_generated is False

    async def test_create_ai_log(self, repo, planter):
        """create() should insert an AI-generated Log with user_id=None."""
        log = Log(planter_id=planter.id, user_id=None, body="AI facilitation", is_ai_generated=True)
        result = await repo.create(log)
        assert result.id is not None
        assert result.user_id is None
        assert result.is_ai_generated is True


class TestGetById:
    async def test_get_existing_log(self, repo, planter, test_user):
        """get_by_id() should return the Log when it exists."""
        log = Log(planter_id=planter.id, user_id=test_user.id, body="Find me")
        created = await repo.create(log)
        result = await repo.get_by_id(created.id)
        assert result is not None
        assert result.body == "Find me"

    async def test_get_deleted_returns_none(self, repo, planter, test_user, db_session):
        """get_by_id() should return None for soft-deleted Logs."""
        log = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Deleted",
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)
        result = await repo.get_by_id(log.id)
        assert result is None


class TestListByPlanter:
    async def test_list_ordered_asc(self, repo, planter, test_user, db_session):
        """list_by_planter() should return top-level Logs in ascending order."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            db_session.add(
                Log(
                    planter_id=planter.id,
                    user_id=test_user.id,
                    body=f"Log {i}",
                    created_at=now + timedelta(seconds=i),
                )
            )
        await db_session.commit()

        results = await repo.list_by_planter(planter.id, limit=10)
        assert len(results) == 3
        assert results[0].body == "Log 0"
        assert results[2].body == "Log 2"

    async def test_excludes_replies(self, repo, planter, test_user, db_session):
        """list_by_planter() should only return top-level Logs (no replies)."""
        parent = Log(planter_id=planter.id, user_id=test_user.id, body="Parent")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        reply = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Reply",
            parent_log_id=parent.id,
        )
        db_session.add(reply)
        await db_session.commit()

        results = await repo.list_by_planter(planter.id, limit=10)
        assert len(results) == 1
        assert results[0].body == "Parent"

    async def test_cursor_pagination_asc(self, repo, planter, test_user, db_session):
        """list_by_planter() should support cursor pagination in ascending order."""
        now = datetime.now(timezone.utc)
        logs = []
        for i in range(5):
            log = Log(
                planter_id=planter.id,
                user_id=test_user.id,
                body=f"Log {i}",
                created_at=now + timedelta(seconds=i),
            )
            db_session.add(log)
            logs.append(log)
        await db_session.commit()
        for log in logs:
            await db_session.refresh(log)

        page1 = await repo.list_by_planter(planter.id, limit=3)
        assert len(page1) == 3
        assert page1[0].body == "Log 0"

        last = page1[-1]
        page2 = await repo.list_by_planter(
            planter.id, limit=3, cursor_created_at=last.created_at, cursor_id=last.id
        )
        assert len(page2) == 2
        assert page2[0].body == "Log 3"


class TestListReplies:
    async def test_list_replies_for_parents(self, repo, planter, test_user, db_session):
        """list_replies() should return replies grouped by parent_log_id."""
        parent1 = Log(planter_id=planter.id, user_id=test_user.id, body="Parent 1")
        parent2 = Log(planter_id=planter.id, user_id=test_user.id, body="Parent 2")
        db_session.add_all([parent1, parent2])
        await db_session.commit()
        await db_session.refresh(parent1)
        await db_session.refresh(parent2)

        reply1 = Log(
            planter_id=planter.id, user_id=test_user.id, body="Reply to P1", parent_log_id=parent1.id
        )
        reply2 = Log(
            planter_id=planter.id, user_id=test_user.id, body="Reply to P2", parent_log_id=parent2.id
        )
        db_session.add_all([reply1, reply2])
        await db_session.commit()

        replies = await repo.list_replies([parent1.id, parent2.id])
        assert len(replies) == 2
        parent1_replies = [r for r in replies if r.parent_log_id == parent1.id]
        assert len(parent1_replies) == 1
        assert parent1_replies[0].body == "Reply to P1"


class TestCounts:
    async def test_count_by_planter(self, repo, planter, test_user, db_session):
        """count_by_planter() should return the number of non-deleted Logs."""
        for i in range(3):
            db_session.add(Log(planter_id=planter.id, user_id=test_user.id, body=f"Log {i}"))
        deleted = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Deleted",
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(deleted)
        await db_session.commit()

        count = await repo.count_by_planter(planter.id)
        assert count == 3

    async def test_count_contributors(self, repo, planter, test_user, another_user, db_session):
        """count_contributors() should return DISTINCT user_id count (excluding AI)."""
        db_session.add(Log(planter_id=planter.id, user_id=test_user.id, body="Log 1"))
        db_session.add(Log(planter_id=planter.id, user_id=test_user.id, body="Log 2"))
        db_session.add(Log(planter_id=planter.id, user_id=another_user.id, body="Log 3"))
        db_session.add(
            Log(planter_id=planter.id, user_id=None, body="AI Log", is_ai_generated=True)
        )
        await db_session.commit()

        count = await repo.count_contributors(planter.id)
        assert count == 2


class TestCountUserLogsSince:
    async def test_count_user_logs_since(self, repo, planter, test_user, db_session):
        """count_user_logs_since() should count user Logs after a given Log."""
        now = datetime.now(timezone.utc)
        ref_log = Log(
            planter_id=planter.id,
            user_id=None,
            body="AI ref",
            is_ai_generated=True,
            created_at=now,
        )
        db_session.add(ref_log)
        await db_session.commit()
        await db_session.refresh(ref_log)

        # Logs after the reference
        for i in range(3):
            db_session.add(
                Log(
                    planter_id=planter.id,
                    user_id=test_user.id,
                    body=f"After {i}",
                    is_ai_generated=False,
                    created_at=now + timedelta(seconds=i + 1),
                )
            )
        # AI log after reference should not count
        db_session.add(
            Log(
                planter_id=planter.id,
                user_id=None,
                body="AI after",
                is_ai_generated=True,
                created_at=now + timedelta(seconds=10),
            )
        )
        await db_session.commit()

        count = await repo.count_user_logs_since(planter.id, ref_log.id)
        assert count == 3


class TestGetAllByPlanter:
    async def test_get_all_by_planter(self, repo, planter, test_user, db_session):
        """get_all_by_planter() should return all non-deleted Logs for a planter."""
        for i in range(3):
            db_session.add(Log(planter_id=planter.id, user_id=test_user.id, body=f"Log {i}"))
        deleted = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Deleted",
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(deleted)
        await db_session.commit()

        results = await repo.get_all_by_planter(planter.id)
        assert len(results) == 3
