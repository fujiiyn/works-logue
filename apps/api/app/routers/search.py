import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import PlanterTag, Tag
from app.models.user import User
from app.repositories.planter_repository import PlanterRepository
from app.schemas.planter import CursorPaginatedResponse, PlanterCardResponse
from app.schemas.seed_type import SeedTypeResponse
from app.schemas.tag import TagResponse
from app.schemas.user import UserPublicResponse

router = APIRouter(tags=["search"])


@router.get("/search", response_model=CursorPaginatedResponse)
async def search_planters(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
    keyword: str | None = Query(None),
    tag_ids: list[uuid.UUID] | None = Query(None),
    status: str | None = Query(None, pattern="^(seed|sprout|louge)$"),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
) -> CursorPaginatedResponse:
    planter_repo = PlanterRepository(db)

    cursor_created_at = None
    cursor_id = None
    if cursor:
        cursor_created_at, cursor_id = CursorPaginatedResponse.decode_cursor(cursor)

    planters = await planter_repo.search(
        keyword=keyword,
        tag_ids=tag_ids,
        status=status,
        limit=limit + 1,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )

    has_next = len(planters) > limit
    if has_next:
        planters = planters[:limit]

    if not planters:
        return CursorPaginatedResponse(items=[], has_next=False)

    # Batch load related data
    user_ids = list({p.user_id for p in planters})
    seed_type_ids = list({p.seed_type_id for p in planters})
    planter_ids = [p.id for p in planters]

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    st_result = await db.execute(select(SeedType).where(SeedType.id.in_(seed_type_ids)))
    st_map = {st.id: st for st in st_result.scalars().all()}

    pt_result = await db.execute(
        select(PlanterTag).where(PlanterTag.planter_id.in_(planter_ids))
    )
    planter_tag_rows = pt_result.scalars().all()
    all_tag_ids = list({pt.tag_id for pt in planter_tag_rows})

    tags_map: dict[uuid.UUID, Tag] = {}
    if all_tag_ids:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(all_tag_ids)))
        tags_map = {t.id: t for t in tags_result.scalars().all()}

    planter_tags_map: dict[uuid.UUID, list[Tag]] = {p.id: [] for p in planters}
    for pt in planter_tag_rows:
        if pt.tag_id in tags_map:
            planter_tags_map[pt.planter_id].append(tags_map[pt.tag_id])

    # Batch load view counts
    view_counts = await planter_repo.get_view_counts(
        planter_ids, since=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )

    items = [
        PlanterCardResponse(
            id=p.id,
            title=p.title,
            status=p.status,
            seed_type=SeedTypeResponse.model_validate(st_map[p.seed_type_id]),
            user=UserPublicResponse.model_validate(users_map[p.user_id]),
            tags=[TagResponse.model_validate(t) for t in planter_tags_map.get(p.id, [])],
            log_count=p.log_count,
            contributor_count=p.contributor_count,
            progress=p.progress,
            view_count=view_counts.get(p.id, 0),
            created_at=p.created_at,
        )
        for p in planters
    ]

    next_cursor = None
    if has_next:
        last = planters[-1]
        next_cursor = CursorPaginatedResponse.encode_cursor(last.created_at, last.id)

    return CursorPaginatedResponse(items=items, next_cursor=next_cursor, has_next=has_next)
