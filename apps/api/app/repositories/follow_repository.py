import uuid

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import PlanterFollow, UserFollow
from app.models.user import User


class FollowRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ----- Planter Follow -----

    async def follow_planter(self, user_id: uuid.UUID, planter_id: uuid.UUID) -> None:
        """Follow a planter. Skip if already followed with is_manually_unfollowed=True (D5)."""
        result = await self.db.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == user_id,
                PlanterFollow.planter_id == planter_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return
        self.db.add(PlanterFollow(user_id=user_id, planter_id=planter_id))
        await self.db.flush()

    async def unfollow_planter(self, user_id: uuid.UUID, planter_id: uuid.UUID) -> None:
        """Mark planter follow as manually unfollowed (D5)."""
        result = await self.db.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == user_id,
                PlanterFollow.planter_id == planter_id,
            )
        )
        follow = result.scalar_one_or_none()
        if follow is None:
            return
        follow.is_manually_unfollowed = True
        await self.db.flush()

    async def get_following_planter_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Get planter IDs the user is following (excluding manually unfollowed)."""
        result = await self.db.execute(
            select(PlanterFollow.planter_id).where(
                PlanterFollow.user_id == user_id,
                PlanterFollow.is_manually_unfollowed == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def is_following_planter(
        self, user_id: uuid.UUID, planter_id: uuid.UUID
    ) -> bool:
        """Return True if the user actively follows the planter (not manually unfollowed)."""
        result = await self.db.execute(
            select(PlanterFollow).where(
                PlanterFollow.user_id == user_id,
                PlanterFollow.planter_id == planter_id,
                PlanterFollow.is_manually_unfollowed == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none() is not None

    # ----- User Follow -----

    async def follow_user(self, follower_id: uuid.UUID, followee_id: uuid.UUID) -> None:
        """Follow a user. Idempotent. Raises ValueError on self-follow."""
        if follower_id == followee_id:
            raise ValueError("Cannot self-follow")
        result = await self.db.execute(
            select(UserFollow).where(
                UserFollow.follower_id == follower_id,
                UserFollow.followee_id == followee_id,
            )
        )
        if result.scalar_one_or_none() is not None:
            return
        self.db.add(UserFollow(follower_id=follower_id, followee_id=followee_id))
        await self.db.flush()

    async def unfollow_user(self, follower_id: uuid.UUID, followee_id: uuid.UUID) -> None:
        """Unfollow a user. Idempotent."""
        await self.db.execute(
            delete(UserFollow).where(
                UserFollow.follower_id == follower_id,
                UserFollow.followee_id == followee_id,
            )
        )
        await self.db.flush()

    async def is_following_user(
        self, follower_id: uuid.UUID, followee_id: uuid.UUID
    ) -> bool:
        result = await self.db.execute(
            select(UserFollow).where(
                UserFollow.follower_id == follower_id,
                UserFollow.followee_id == followee_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_follower_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(UserFollow).where(
                UserFollow.followee_id == user_id
            )
        )
        return result.scalar_one()

    async def get_following_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(UserFollow).where(
                UserFollow.follower_id == user_id
            )
        )
        return result.scalar_one()

    async def get_followers(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[User], str | None]:
        """Get followers of a user, excluding BAN/deleted users (D16)."""
        query = (
            select(User)
            .join(UserFollow, UserFollow.follower_id == User.id)
            .where(
                UserFollow.followee_id == user_id,
                User.is_banned == False,  # noqa: E712
                User.deleted_at.is_(None),
            )
            .order_by(UserFollow.created_at.desc())
        )
        if cursor:
            from datetime import datetime, timezone

            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(UserFollow.created_at < cursor_dt)

        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        next_cursor = None
        if len(users) > limit:
            users = users[:limit]
            # Use the last user's follow created_at as cursor
            last_follow_result = await self.db.execute(
                select(UserFollow.created_at).where(
                    UserFollow.follower_id == users[-1].id,
                    UserFollow.followee_id == user_id,
                )
            )
            last_dt = last_follow_result.scalar_one()
            next_cursor = last_dt.isoformat()

        return users, next_cursor

    async def get_following_users(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[User], str | None]:
        """Get users that a user is following, excluding BAN/deleted users (D16)."""
        query = (
            select(User)
            .join(UserFollow, UserFollow.followee_id == User.id)
            .where(
                UserFollow.follower_id == user_id,
                User.is_banned == False,  # noqa: E712
                User.deleted_at.is_(None),
            )
            .order_by(UserFollow.created_at.desc())
        )
        if cursor:
            from datetime import datetime, timezone

            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(UserFollow.created_at < cursor_dt)

        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        next_cursor = None
        if len(users) > limit:
            users = users[:limit]
            last_follow_result = await self.db.execute(
                select(UserFollow.created_at).where(
                    UserFollow.follower_id == user_id,
                    UserFollow.followee_id == users[-1].id,
                )
            )
            last_dt = last_follow_result.scalar_one()
            next_cursor = last_dt.isoformat()

        return users, next_cursor

    async def get_following_user_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Get IDs of users that user_id is following."""
        result = await self.db.execute(
            select(UserFollow.followee_id).where(
                UserFollow.follower_id == user_id,
            )
        )
        return list(result.scalars().all())
