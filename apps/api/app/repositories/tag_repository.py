import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import PlanterTag, Tag, UserTag


class TagRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_category(self, category: str | None) -> list[Tag]:
        stmt = select(Tag).where(Tag.is_active.is_(True)).order_by(Tag.sort_order)
        if category is not None:
            stmt = stmt.where(Tag.category == category)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Tag]:
        if not ids:
            return []
        result = await self.db.execute(select(Tag).where(Tag.id.in_(ids)))
        return list(result.scalars().all())

    async def attach_to_planter(
        self, planter_id: uuid.UUID, tag_ids: list[uuid.UUID]
    ) -> None:
        for tag_id in tag_ids:
            self.db.add(PlanterTag(planter_id=planter_id, tag_id=tag_id))
        await self.db.flush()

    async def replace_user_tags(
        self, user_id: uuid.UUID, tag_ids: list[uuid.UUID]
    ) -> None:
        await self.db.execute(
            delete(UserTag).where(UserTag.user_id == user_id)
        )
        for tag_id in tag_ids:
            self.db.add(UserTag(user_id=user_id, tag_id=tag_id))
        await self.db.flush()
