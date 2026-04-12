import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import Tag, PlanterTag, UserTag
from app.models.user import User
from app.repositories.tag_repository import TagRepository


@pytest.fixture
async def tags(db_session: AsyncSession) -> dict[str, Tag]:
    root = Tag(name="IT", category="industry", is_leaf=False, sort_order=1)
    child = Tag(name="SaaS", category="industry", is_leaf=True, sort_order=1)
    inactive = Tag(name="Inactive", category="industry", is_leaf=True, is_active=False, sort_order=2)
    occ_root = Tag(name="営業", category="occupation", is_leaf=False, sort_order=1)
    occ_leaf = Tag(name="法人営業", category="occupation", is_leaf=True, sort_order=1)

    db_session.add_all([root, child, inactive, occ_root, occ_leaf])
    await db_session.flush()

    child.parent_tag_id = root.id
    inactive.parent_tag_id = root.id
    occ_leaf.parent_tag_id = occ_root.id
    await db_session.commit()

    for t in [root, child, inactive, occ_root, occ_leaf]:
        await db_session.refresh(t)

    return {"root": root, "child": child, "inactive": inactive, "occ_root": occ_root, "occ_leaf": occ_leaf}


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
def repo(db_session: AsyncSession) -> TagRepository:
    return TagRepository(db_session)


class TestListByCategory:
    async def test_filter_by_category(self, repo, tags):
        """list_by_category() should return only tags of the given category."""
        result = await repo.list_by_category("industry")
        names = {t.name for t in result}
        assert "IT" in names
        assert "SaaS" in names
        assert "営業" not in names

    async def test_all_categories(self, repo, tags):
        """list_by_category(None) should return all active tags."""
        result = await repo.list_by_category(None)
        names = {t.name for t in result}
        assert "IT" in names
        assert "営業" in names

    async def test_excludes_inactive(self, repo, tags):
        """list_by_category() should exclude inactive tags."""
        result = await repo.list_by_category("industry")
        names = {t.name for t in result}
        assert "Inactive" not in names


class TestGetByIds:
    async def test_get_multiple(self, repo, tags):
        """get_by_ids() should return all matching tags."""
        ids = [tags["child"].id, tags["occ_leaf"].id]
        result = await repo.get_by_ids(ids)
        assert len(result) == 2

    async def test_empty_list(self, repo):
        """get_by_ids([]) should return empty list."""
        result = await repo.get_by_ids([])
        assert result == []


class TestAttachToPlanter:
    async def test_attach_tags(self, repo, tags, test_user, seed_type, db_session):
        """attach_to_planter() should create PlanterTag records."""
        planter = Planter(
            user_id=test_user.id, title="T", body="B", seed_type_id=seed_type.id
        )
        db_session.add(planter)
        await db_session.flush()
        await db_session.refresh(planter)

        await repo.attach_to_planter(planter.id, [tags["child"].id, tags["occ_leaf"].id])
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(PlanterTag).where(PlanterTag.planter_id == planter.id)
        )
        pts = result.scalars().all()
        assert len(pts) == 2


class TestReplaceUserTags:
    async def test_replace_tags(self, repo, tags, test_user, db_session):
        """replace_user_tags() should delete existing and insert new tags."""
        # First set
        await repo.replace_user_tags(test_user.id, [tags["child"].id])
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(UserTag).where(UserTag.user_id == test_user.id)
        )
        assert len(result.scalars().all()) == 1

        # Replace
        await repo.replace_user_tags(test_user.id, [tags["child"].id, tags["occ_leaf"].id])
        await db_session.commit()

        result = await db_session.execute(
            select(UserTag).where(UserTag.user_id == test_user.id)
        )
        assert len(result.scalars().all()) == 2
