import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import PlanterFollow, UserFollow
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
async def other_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Other User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def banned_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Banned User", is_banned=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def deleted_user(db_session: AsyncSession) -> User:
    from datetime import datetime, timezone

    user = User(
        auth_id=uuid.uuid4(),
        display_name="Deleted User",
        deleted_at=datetime.now(timezone.utc),
    )
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


# =============================================================
# Planter Follow
# =============================================================


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
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()

    async def test_follow_skipped_when_manually_unfollowed(
        self, repo, test_user, planter, db_session
    ):
        """follow_planter() should skip if is_manually_unfollowed=True (D5)."""
        # First follow
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()
        # Manually unfollow
        await repo.unfollow_planter(test_user.id, planter.id)
        await db_session.commit()
        # Auto follow should be skipped
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()

        result = await db_session.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == test_user.id,
                PlanterFollow.planter_id == planter.id,
            )
        )
        follow = result.scalar_one_or_none()
        assert follow is not None
        assert follow.is_manually_unfollowed is True

    async def test_unfollow_planter(self, repo, test_user, planter, db_session):
        """unfollow_planter() should set is_manually_unfollowed=True."""
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()
        await repo.unfollow_planter(test_user.id, planter.id)
        await db_session.commit()

        result = await db_session.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == test_user.id,
                PlanterFollow.planter_id == planter.id,
            )
        )
        follow = result.scalar_one_or_none()
        assert follow is not None
        assert follow.is_manually_unfollowed is True

    async def test_unfollow_planter_not_followed(self, repo, test_user, planter, db_session):
        """unfollow_planter() on non-followed planter should not raise."""
        await repo.unfollow_planter(test_user.id, planter.id)
        await db_session.commit()


# =============================================================
# User Follow
# =============================================================


class TestFollowUser:
    async def test_follow_user_success(self, repo, test_user, other_user, db_session):
        """follow_user() should create a UserFollow record."""
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()

        result = await db_session.execute(
            select(UserFollow).where(
                UserFollow.follower_id == test_user.id,
                UserFollow.followee_id == other_user.id,
            )
        )
        assert result.scalar_one_or_none() is not None

    async def test_follow_user_idempotent(self, repo, test_user, other_user, db_session):
        """follow_user() should be idempotent."""
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()

    async def test_self_follow_raises(self, repo, test_user, db_session):
        """follow_user() should raise ValueError on self-follow."""
        with pytest.raises(ValueError, match="self-follow"):
            await repo.follow_user(test_user.id, test_user.id)

    async def test_unfollow_user(self, repo, test_user, other_user, db_session):
        """unfollow_user() should remove the UserFollow record."""
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()
        await repo.unfollow_user(test_user.id, other_user.id)
        await db_session.commit()

        result = await db_session.execute(
            select(UserFollow).where(
                UserFollow.follower_id == test_user.id,
                UserFollow.followee_id == other_user.id,
            )
        )
        assert result.scalar_one_or_none() is None

    async def test_unfollow_user_not_followed(self, repo, test_user, other_user, db_session):
        """unfollow_user() on non-followed user should not raise (idempotent)."""
        await repo.unfollow_user(test_user.id, other_user.id)
        await db_session.commit()

    async def test_is_following_user(self, repo, test_user, other_user, db_session):
        """is_following_user() should return correct boolean."""
        assert await repo.is_following_user(test_user.id, other_user.id) is False
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()
        assert await repo.is_following_user(test_user.id, other_user.id) is True


class TestFollowCounts:
    async def test_follower_and_following_count(self, repo, db_session):
        """get_follower_count / get_following_count should return correct counts."""
        user_a = User(auth_id=uuid.uuid4(), display_name="A")
        user_b = User(auth_id=uuid.uuid4(), display_name="B")
        user_c = User(auth_id=uuid.uuid4(), display_name="C")
        db_session.add_all([user_a, user_b, user_c])
        await db_session.commit()
        await db_session.refresh(user_a)
        await db_session.refresh(user_b)
        await db_session.refresh(user_c)

        # B and C follow A
        await repo.follow_user(user_b.id, user_a.id)
        await repo.follow_user(user_c.id, user_a.id)
        await db_session.commit()

        assert await repo.get_follower_count(user_a.id) == 2
        assert await repo.get_following_count(user_a.id) == 0
        assert await repo.get_following_count(user_b.id) == 1


class TestFollowList:
    async def test_get_followers(self, repo, db_session):
        """get_followers() should return follower users, excluding BAN/deleted (D16)."""
        target = User(auth_id=uuid.uuid4(), display_name="Target")
        normal = User(auth_id=uuid.uuid4(), display_name="Normal")
        banned = User(auth_id=uuid.uuid4(), display_name="Banned", is_banned=True)
        db_session.add_all([target, normal, banned])
        await db_session.commit()
        for u in [target, normal, banned]:
            await db_session.refresh(u)

        await repo.follow_user(normal.id, target.id)
        await repo.follow_user(banned.id, target.id)
        await db_session.commit()

        followers, next_cursor = await repo.get_followers(target.id)
        assert len(followers) == 1
        assert followers[0].id == normal.id
        assert next_cursor is None

    async def test_get_following_users(self, repo, db_session):
        """get_following_users() should return followed users, excluding BAN/deleted (D16)."""
        follower = User(auth_id=uuid.uuid4(), display_name="Follower")
        normal = User(auth_id=uuid.uuid4(), display_name="Normal")
        banned = User(auth_id=uuid.uuid4(), display_name="Banned", is_banned=True)
        db_session.add_all([follower, normal, banned])
        await db_session.commit()
        for u in [follower, normal, banned]:
            await db_session.refresh(u)

        await repo.follow_user(follower.id, normal.id)
        await repo.follow_user(follower.id, banned.id)
        await db_session.commit()

        following, next_cursor = await repo.get_following_users(follower.id)
        assert len(following) == 1
        assert following[0].id == normal.id

    async def test_get_followers_cursor_pagination(self, repo, db_session):
        """get_followers() should support cursor-based pagination."""
        from datetime import datetime, timedelta, timezone

        target = User(auth_id=uuid.uuid4(), display_name="Target")
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        # Create 3 followers with staggered timestamps for cursor reliability
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        users = []
        for i in range(3):
            u = User(auth_id=uuid.uuid4(), display_name=f"User{i}")
            db_session.add(u)
            users.append(u)
        await db_session.commit()
        for u in users:
            await db_session.refresh(u)

        for i, u in enumerate(users):
            follow = UserFollow(
                follower_id=u.id,
                followee_id=target.id,
                created_at=base_time + timedelta(hours=i),
            )
            db_session.add(follow)
        await db_session.commit()

        # Fetch page 1 (limit=2)
        page1, cursor1 = await repo.get_followers(target.id, limit=2)
        assert len(page1) == 2
        assert cursor1 is not None

        # Fetch page 2
        page2, cursor2 = await repo.get_followers(target.id, limit=2, cursor=cursor1)
        assert len(page2) == 1
        assert cursor2 is None


class TestFollowingPlanterIds:
    async def test_get_following_planter_ids(self, repo, test_user, planter, db_session):
        """get_following_planter_ids() should return planter IDs."""
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()

        ids = await repo.get_following_planter_ids(test_user.id)
        assert planter.id in ids

    async def test_get_following_planter_ids_excludes_unfollowed(
        self, repo, test_user, planter, db_session
    ):
        """get_following_planter_ids() should exclude manually unfollowed planters."""
        await repo.follow_planter(test_user.id, planter.id)
        await db_session.commit()
        await repo.unfollow_planter(test_user.id, planter.id)
        await db_session.commit()

        ids = await repo.get_following_planter_ids(test_user.id)
        assert planter.id not in ids

    async def test_get_following_user_ids(self, repo, test_user, other_user, db_session):
        """get_following_user_ids() should return followed user IDs."""
        await repo.follow_user(test_user.id, other_user.id)
        await db_session.commit()

        ids = await repo.get_following_user_ids(test_user.id)
        assert other_user.id in ids
