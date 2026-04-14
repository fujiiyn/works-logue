import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import Tag
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.planter_repository import PlanterRepository
from app.repositories.tag_repository import TagRepository
from app.schemas.planter import (
    CursorPaginatedResponse,
    PlanterCardResponse,
    PlanterCreateRequest,
    PlanterResponse,
)
from app.schemas.score import StructurePartsResponse
from app.schemas.seed_type import SeedTypeResponse
from app.schemas.tag import TagResponse
from app.schemas.user import UserPublicResponse

DEFAULT_BLOOM_THRESHOLD = 0.7

router = APIRouter(tags=["planters"])


def _build_planter_response(
    planter: Planter,
    seed_type: SeedType,
    user: User,
    tags: list[Tag],
    *,
    include_body: bool = True,
    bloom_threshold: float = DEFAULT_BLOOM_THRESHOLD,
) -> PlanterResponse | PlanterCardResponse:
    user_resp = UserPublicResponse.model_validate(user)
    seed_type_resp = SeedTypeResponse.model_validate(seed_type)
    tag_resps = [TagResponse.model_validate(t) for t in tags]

    # Build structure_parts from planter's stored data (if any)
    structure_parts = None
    # structure_parts will be populated from LougeScoreSnapshot in score endpoints

    if include_body:
        return PlanterResponse(
            id=planter.id,
            title=planter.title,
            body=planter.body,
            status=planter.status,
            seed_type=seed_type_resp,
            user=user_resp,
            tags=tag_resps,
            log_count=planter.log_count,
            contributor_count=planter.contributor_count,
            progress=planter.progress,
            structure_fulfillment=planter.structure_fulfillment,
            maturity_score=planter.maturity_score,
            structure_parts=structure_parts,
            bloom_threshold=bloom_threshold,
            created_at=planter.created_at,
        )
    return PlanterCardResponse(
        id=planter.id,
        title=planter.title,
        status=planter.status,
        seed_type=seed_type_resp,
        user=user_resp,
        tags=tag_resps,
        log_count=planter.log_count,
        contributor_count=planter.contributor_count,
        progress=planter.progress,
        created_at=planter.created_at,
    )


@router.post("/planters", response_model=PlanterResponse, status_code=201)
async def create_planter(
    body: PlanterCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlanterResponse:
    # Validate seed_type
    result = await db.execute(
        select(SeedType).where(
            SeedType.id == body.seed_type_id,
            SeedType.is_active.is_(True),
        )
    )
    seed_type = result.scalar_one_or_none()
    if seed_type is None:
        raise HTTPException(status_code=400, detail="invalid_seed_type")

    # Validate tags
    tag_repo = TagRepository(db)
    tags: list[Tag] = []
    if body.tag_ids:
        unique_ids = list(set(body.tag_ids))
        tags = await tag_repo.get_by_ids(unique_ids)
        if len(tags) != len(unique_ids):
            raise HTTPException(status_code=400, detail="invalid_tags")
        for tag in tags:
            if not tag.is_leaf or not tag.is_active:
                raise HTTPException(status_code=400, detail="invalid_tags")

    # Create planter
    planter_repo = PlanterRepository(db)
    planter = Planter(
        user_id=current_user.id,
        title=body.title.strip(),
        body=body.body.strip(),
        seed_type_id=body.seed_type_id,
    )
    planter = await planter_repo.create(planter)

    # Attach tags
    if body.tag_ids:
        await tag_repo.attach_to_planter(planter.id, [t.id for t in tags])

    # Auto-follow
    follow_repo = FollowRepository(db)
    await follow_repo.follow_planter(current_user.id, planter.id)

    await db.commit()
    await db.refresh(planter)

    return _build_planter_response(planter, seed_type, current_user, tags)


@router.get("/planters", response_model=CursorPaginatedResponse)
async def list_planters(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
) -> CursorPaginatedResponse:
    planter_repo = PlanterRepository(db)

    cursor_created_at = None
    cursor_id = None
    if cursor:
        cursor_created_at, cursor_id = CursorPaginatedResponse.decode_cursor(cursor)

    planters = await planter_repo.list_recent(
        limit=limit + 1,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )

    has_next = len(planters) > limit
    if has_next:
        planters = planters[:limit]

    # Batch load related data
    if not planters:
        return CursorPaginatedResponse(items=[], has_next=False)

    user_ids = list({p.user_id for p in planters})
    seed_type_ids = list({p.seed_type_id for p in planters})
    planter_ids = [p.id for p in planters]

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    st_result = await db.execute(select(SeedType).where(SeedType.id.in_(seed_type_ids)))
    st_map = {st.id: st for st in st_result.scalars().all()}

    from app.models.tag import PlanterTag
    pt_result = await db.execute(
        select(PlanterTag).where(PlanterTag.planter_id.in_(planter_ids))
    )
    planter_tag_rows = pt_result.scalars().all()
    tag_ids = list({pt.tag_id for pt in planter_tag_rows})

    tags_map: dict[uuid.UUID, Tag] = {}
    if tag_ids:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        tags_map = {t.id: t for t in tags_result.scalars().all()}

    planter_tags_map: dict[uuid.UUID, list[Tag]] = {p.id: [] for p in planters}
    for pt in planter_tag_rows:
        if pt.tag_id in tags_map:
            planter_tags_map[pt.planter_id].append(tags_map[pt.tag_id])

    items = [
        _build_planter_response(
            p,
            st_map[p.seed_type_id],
            users_map[p.user_id],
            planter_tags_map.get(p.id, []),
            include_body=False,
        )
        for p in planters
    ]

    next_cursor = None
    if has_next:
        last = planters[-1]
        next_cursor = CursorPaginatedResponse.encode_cursor(last.created_at, last.id)

    return CursorPaginatedResponse(items=items, next_cursor=next_cursor, has_next=has_next)


@router.get("/planters/{planter_id}", response_model=PlanterResponse)
async def get_planter(
    planter_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_user)],
) -> PlanterResponse:
    planter_repo = PlanterRepository(db)
    planter = await planter_repo.get_by_id(planter_id)
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")

    user_result = await db.execute(select(User).where(User.id == planter.user_id))
    user = user_result.scalar_one()

    st_result = await db.execute(select(SeedType).where(SeedType.id == planter.seed_type_id))
    seed_type = st_result.scalar_one()

    from app.models.tag import PlanterTag
    pt_result = await db.execute(
        select(PlanterTag).where(PlanterTag.planter_id == planter.id)
    )
    tag_ids = [pt.tag_id for pt in pt_result.scalars().all()]
    tags: list[Tag] = []
    if tag_ids:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        tags = list(tags_result.scalars().all())

    return _build_planter_response(planter, seed_type, user, tags)
