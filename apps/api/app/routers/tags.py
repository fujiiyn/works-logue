from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagTreeNode

router = APIRouter(tags=["tags"])


def build_tree(flat_tags: list[Tag]) -> list[TagTreeNode]:
    nodes: dict[str, TagTreeNode] = {}
    for t in flat_tags:
        nodes[str(t.id)] = TagTreeNode(
            id=t.id,
            name=t.name,
            category=t.category,
            is_leaf=t.is_leaf,
            children=[],
        )

    roots: list[TagTreeNode] = []
    for t in flat_tags:
        node = nodes[str(t.id)]
        if t.parent_tag_id is None:
            roots.append(node)
        elif str(t.parent_tag_id) in nodes:
            nodes[str(t.parent_tag_id)].children.append(node)

    return roots


@router.get("/tags", response_model=list[TagTreeNode])
async def list_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(None),
) -> list[TagTreeNode]:
    repo = TagRepository(db)
    flat_tags = await repo.list_by_category(category)
    return build_tree(flat_tags)
