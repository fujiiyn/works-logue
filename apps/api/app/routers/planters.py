import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.tag import Tag
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.log_repository import LogRepository
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
from app.services.feed_ranker import FeedRanker

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
        bloom_pending = planter.status == "louge" and planter.louge_content is None
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
            louge_content=planter.louge_content,
            louge_generated_at=planter.louge_generated_at,
            bloom_pending=bloom_pending,
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
    tab: str = Query("recent", pattern="^(recent|trending|bloomed|following)$"),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
) -> CursorPaginatedResponse:
    planter_repo = PlanterRepository(db)

    # Following tab requires authentication (BR-FF01)
    if tab == "following":
        if _user is None:
            from fastapi import HTTPException as _HTTPException

            raise _HTTPException(status_code=401, detail="Authentication required")
        return await _fetch_following(planter_repo, db, _user, limit, cursor)

    cursor_created_at = None
    cursor_id = None
    if cursor:
        cursor_created_at, cursor_id = CursorPaginatedResponse.decode_cursor(cursor)

    if tab == "trending":
        planters = await _fetch_trending(planter_repo, db, limit)
        # Trending does not support cursor pagination (returns top N)
        return await _build_feed_response(planters, False, db)

    if tab == "bloomed":
        planters = await planter_repo.list_bloomed(
            limit=limit + 1,
            cursor_louge_generated_at=cursor_created_at,
            cursor_id=cursor_id,
        )
    else:
        planters = await planter_repo.list_recent(
            limit=limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
        )

    has_next = len(planters) > limit
    if has_next:
        planters = planters[:limit]

    return await _build_feed_response(planters, has_next, db)


async def _fetch_trending(
    planter_repo: PlanterRepository,
    db: AsyncSession,
    limit: int,
) -> list[Planter]:
    candidates = await planter_repo.list_trending_candidates(window_days=7, limit=100)
    if not candidates:
        return []

    planter_ids = [p.id for p in candidates]
    since = datetime.now(timezone.utc) - timedelta(days=7)
    view_counts = await planter_repo.get_view_counts(planter_ids, since=since)

    log_repo = LogRepository(db)
    log_velocities = await log_repo.get_log_velocities(planter_ids, window_hours=72)

    ranker = FeedRanker()
    ranked = ranker.rank_trending(candidates, view_counts, log_velocities)

    return [r.planter for r in ranked[:limit]]


async def _fetch_following(
    planter_repo: PlanterRepository,
    db: AsyncSession,
    user: User,
    limit: int,
    cursor: str | None,
) -> CursorPaginatedResponse:
    """Fetch planters from followed planters + followed users' planters (BR-FF01)."""
    follow_repo = FollowRepository(db)

    # Get followed planter IDs
    followed_planter_ids = await follow_repo.get_following_planter_ids(user.id)

    # Get followed user IDs → their planters
    followed_user_ids = await follow_repo.get_following_user_ids(user.id)

    cursor_created_at = None
    cursor_id = None
    if cursor:
        cursor_created_at, cursor_id = CursorPaginatedResponse.decode_cursor(cursor)

    planters = await planter_repo.list_following(
        followed_planter_ids=followed_planter_ids,
        followed_user_ids=followed_user_ids,
        limit=limit + 1,
        cursor_updated_at=cursor_created_at,
        cursor_id=cursor_id,
    )

    has_next = len(planters) > limit
    if has_next:
        planters = planters[:limit]

    return await _build_feed_response(planters, has_next, db)


async def _build_feed_response(
    planters: list[Planter],
    has_next: bool,
    db: AsyncSession,
) -> CursorPaginatedResponse:
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

    # Batch load view counts
    planter_repo = PlanterRepository(db)
    view_counts = await planter_repo.get_view_counts(
        planter_ids, since=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )

    items = []
    for p in planters:
        card = _build_planter_response(
            p,
            st_map[p.seed_type_id],
            users_map[p.user_id],
            planter_tags_map.get(p.id, []),
            include_body=False,
        )
        card.view_count = view_counts.get(p.id, 0)
        items.append(card)

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

    response = _build_planter_response(planter, seed_type, user, tags)
    if _user is not None:
        follow_repo = FollowRepository(db)
        response.is_following = await follow_repo.is_following_planter(_user.id, planter.id)
    return response


@router.post("/planters/{planter_id}/follow", status_code=204)
async def follow_planter(
    planter_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Manually follow a planter."""
    planter_repo = PlanterRepository(db)
    planter = await planter_repo.get_by_id(planter_id)
    if planter is None:
        raise HTTPException(status_code=404, detail="planter_not_found")

    follow_repo = FollowRepository(db)
    await follow_repo.follow_planter(current_user.id, planter_id)
    await db.commit()
    return Response(status_code=204)


@router.delete("/planters/{planter_id}/follow", status_code=204)
async def unfollow_planter(
    planter_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Manually unfollow a planter (D5: sets is_manually_unfollowed)."""
    follow_repo = FollowRepository(db)
    await follow_repo.unfollow_planter(current_user.id, planter_id)
    await db.commit()
    return Response(status_code=204)


@router.post("/planters/{planter_id}/view", status_code=204)
async def record_view(
    planter_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    ip_address = request.client.host if request.client else None
    planter_repo = PlanterRepository(db)
    await planter_repo.record_view(
        planter_id,
        user_id=user.id if user else None,
        ip_address=ip_address,
    )
    await db.commit()
    return Response(status_code=204)
