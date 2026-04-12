import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


@pytest.fixture
async def tag_tree(db_session: AsyncSession) -> dict[str, Tag]:
    # Industry tree
    ind_root = Tag(name="IT", category="industry", is_leaf=False, sort_order=1)
    db_session.add(ind_root)
    await db_session.flush()

    ind_child = Tag(
        name="SaaS", category="industry", is_leaf=True, sort_order=1,
        parent_tag_id=ind_root.id,
    )
    ind_inactive = Tag(
        name="Inactive", category="industry", is_leaf=True, sort_order=2,
        is_active=False, parent_tag_id=ind_root.id,
    )
    db_session.add_all([ind_child, ind_inactive])

    # Occupation tree
    occ_root = Tag(name="営業", category="occupation", is_leaf=False, sort_order=1)
    db_session.add(occ_root)
    await db_session.flush()

    occ_child = Tag(
        name="法人営業", category="occupation", is_leaf=True, sort_order=1,
        parent_tag_id=occ_root.id,
    )
    db_session.add(occ_child)
    await db_session.commit()

    for t in [ind_root, ind_child, ind_inactive, occ_root, occ_child]:
        await db_session.refresh(t)

    return {
        "ind_root": ind_root, "ind_child": ind_child, "ind_inactive": ind_inactive,
        "occ_root": occ_root, "occ_child": occ_child,
    }


class TestListTags:
    async def test_returns_tree_structure(self, client, tag_tree):
        """GET /api/v1/tags should return a tree structure."""
        resp = await client.get("/api/v1/tags")
        assert resp.status_code == 200
        data = resp.json()
        # Should have root nodes
        root_names = [t["name"] for t in data]
        assert "IT" in root_names
        assert "営業" in root_names

    async def test_children_nested(self, client, tag_tree):
        """Tree nodes should have children nested."""
        resp = await client.get("/api/v1/tags")
        data = resp.json()
        it_node = next(t for t in data if t["name"] == "IT")
        child_names = [c["name"] for c in it_node["children"]]
        assert "SaaS" in child_names

    async def test_filter_by_category(self, client, tag_tree):
        """GET /api/v1/tags?category=occupation should filter."""
        resp = await client.get("/api/v1/tags?category=occupation")
        data = resp.json()
        root_names = [t["name"] for t in data]
        assert "営業" in root_names
        assert "IT" not in root_names

    async def test_excludes_inactive(self, client, tag_tree):
        """Inactive tags should be excluded from tree."""
        resp = await client.get("/api/v1/tags")
        data = resp.json()
        it_node = next(t for t in data if t["name"] == "IT")
        child_names = [c["name"] for c in it_node["children"]]
        assert "Inactive" not in child_names
