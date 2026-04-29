import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ContributionDay,
    ContributionGraphResponse,
    FeaturedContributionResponse,
    FollowListResponse,
    FollowUserItem,
    ImageUploadResponse,
    LogHistoryItem,
    PlanterSummary,
    SimilarUserResponse,
    TagResponse,
    UserLogListResponse,
    UserPlanterListResponse,
    UserProfileResponse,
    UserProfileStats,
    UserPublicResponse,
    UserResponse,
    UserUpdate,
)
from app.services.storage_client import (
    AVATAR_SIZE,
    COVER_SIZE,
    MAX_AVATAR_BYTES,
    MAX_COVER_BYTES,
    StorageError,
    SupabaseStorageClient,
)

router = APIRouter(tags=["users"])


def _get_storage_client() -> SupabaseStorageClient:
    from app.config import settings

    return SupabaseStorageClient(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )


# ---- /users/me ----


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.patch("/users/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if body.display_name is not None:
        current_user.display_name = (
            body.display_name.strip() if body.display_name else body.display_name
        )

    if body.complete_onboarding:
        if not current_user.display_name or not current_user.display_name.strip():
            raise HTTPException(
                status_code=422, detail="display_name is required for onboarding"
            )

    if "bio" in body.model_fields_set:
        current_user.bio = body.bio if body.bio else None
    if "headline" in body.model_fields_set:
        current_user.headline = body.headline if body.headline else None
    if "location" in body.model_fields_set:
        current_user.location = body.location if body.location else None

    # SNS URLs (validated by Pydantic, D12)
    # Use model_fields_set to distinguish "not provided" from "explicitly set to null/empty"
    if "x_url" in body.model_fields_set:
        current_user.x_url = body.x_url if body.x_url else None
    if "linkedin_url" in body.model_fields_set:
        current_user.linkedin_url = body.linkedin_url if body.linkedin_url else None
    if "wantedly_url" in body.model_fields_set:
        current_user.wantedly_url = body.wantedly_url if body.wantedly_url else None
    if "website_url" in body.model_fields_set:
        current_user.website_url = body.website_url if body.website_url else None

    # Handle tag_ids
    if body.tag_ids is not None:
        tag_repo = TagRepository(db)
        if body.tag_ids:
            tags = await tag_repo.get_by_ids(body.tag_ids)
            if len(tags) != len(set(body.tag_ids)):
                raise HTTPException(status_code=400, detail="invalid_tags")
            for tag in tags:
                if not tag.is_leaf or not tag.is_active:
                    raise HTTPException(status_code=400, detail="invalid_tags")
        await tag_repo.replace_user_tags(current_user.id, list(set(body.tag_ids)))

    # Apply pending images (D2)
    storage = _get_storage_client()
    if current_user.pending_avatar_path:
        old_avatar_url = current_user.avatar_url
        current_user.avatar_url = storage._public_url(
            "avatars", current_user.pending_avatar_path
        )
        current_user.pending_avatar_path = None
        if old_avatar_url:
            _try_delete_old_image(storage, "avatars", old_avatar_url)

    if current_user.pending_cover_path:
        old_cover_url = current_user.cover_url
        current_user.cover_url = storage._public_url(
            "covers", current_user.pending_cover_path
        )
        current_user.pending_cover_path = None
        if old_cover_url:
            _try_delete_old_image(storage, "covers", old_cover_url)

    # Complete onboarding
    if body.complete_onboarding:
        current_user.onboarded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_user)
    return current_user


def _try_delete_old_image(
    storage: SupabaseStorageClient, bucket: str, url: str
) -> None:
    """Extract path from public URL and schedule deletion (D15: log-only on failure)."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)
    marker = f"/storage/v1/object/public/{bucket}/"
    idx = url.find(marker)
    if idx == -1:
        return
    path = url[idx + len(marker) :]

    async def _do_delete() -> None:
        try:
            await storage.delete(bucket, path)
        except Exception:
            logger.warning("Failed to delete old image %s/%s", bucket, path, exc_info=True)

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(_do_delete())
    except RuntimeError:
        pass


# ---- Avatar / Cover Upload ----


@router.post("/users/me/avatar", response_model=ImageUploadResponse)
async def upload_avatar(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Upload avatar image, store as pending (D2)."""
    storage = _get_storage_client()
    file_data = await file.read()
    try:
        public_url, path = await storage.upload(
            "avatars", current_user.id, file_data, AVATAR_SIZE, MAX_AVATAR_BYTES
        )
    except StorageError as e:
        raise HTTPException(status_code=422, detail=str(e))

    current_user.pending_avatar_path = path
    await db.commit()
    return {"url": public_url}


@router.post("/users/me/cover", response_model=ImageUploadResponse)
async def upload_cover(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Upload cover image, store as pending (D2)."""
    storage = _get_storage_client()
    file_data = await file.read()
    try:
        public_url, path = await storage.upload(
            "covers", current_user.id, file_data, COVER_SIZE, MAX_COVER_BYTES
        )
    except StorageError as e:
        raise HTTPException(status_code=422, detail=str(e))

    current_user.pending_cover_path = path
    await db.commit()
    return {"url": public_url}


# ---- Public Profile ----


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> dict:
    """Get public user profile with stats, tags, featured contribution."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    follow_repo = FollowRepository(db)
    tag_repo = TagRepository(db)

    louge_count = await user_repo.get_louge_count(user_id)
    follower_count = await follow_repo.get_follower_count(user_id)
    following_count = await follow_repo.get_following_count(user_id)
    tags = await tag_repo.get_user_tags(user_id)
    featured = await user_repo.get_featured_contribution(user_id)

    is_following = False
    is_own_profile = False
    if current_user:
        is_own_profile = current_user.id == user_id
        if not is_own_profile:
            is_following = await follow_repo.is_following_user(
                current_user.id, user_id
            )

    return {
        "user": UserPublicResponse.model_validate(user),
        "stats": UserProfileStats(
            insight_score=user.insight_score,
            louge_count=louge_count,
            follower_count=follower_count,
            following_count=following_count,
        ),
        "tags": [TagResponse.model_validate(t) for t in tags],
        "featured_contribution": (
            FeaturedContributionResponse(**featured) if featured else None
        ),
        "is_following": is_following,
        "is_own_profile": is_own_profile,
    }


# ---- Follow / Unfollow Users ----


@router.post("/users/{user_id}/follow", status_code=204)
async def follow_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Follow a user (BR-F01, BR-F02, BR-F03)."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    user_repo = UserRepository(db)
    target = await user_repo.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    follow_repo = FollowRepository(db)
    await follow_repo.follow_user(current_user.id, user_id)
    await db.commit()
    return Response(status_code=204)


@router.delete("/users/{user_id}/follow", status_code=204)
async def unfollow_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Unfollow a user (BR-F05)."""
    follow_repo = FollowRepository(db)
    await follow_repo.unfollow_user(current_user.id, user_id)
    await db.commit()
    return Response(status_code=204)


# ---- Follower / Following Lists ----


@router.get("/users/{user_id}/followers", response_model=FollowListResponse)
async def get_followers(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, le=50),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> dict:
    follow_repo = FollowRepository(db)
    users, next_cursor = await follow_repo.get_followers(user_id, limit=limit, cursor=cursor)

    # Determine is_following for each user
    following_ids: set[uuid.UUID] = set()
    if current_user:
        ids = await follow_repo.get_following_user_ids(current_user.id)
        following_ids = set(ids)

    return {
        "users": [
            FollowUserItem(
                id=u.id,
                display_name=u.display_name,
                headline=u.headline,
                avatar_url=u.avatar_url,
                insight_score=u.insight_score,
                is_following=u.id in following_ids,
            )
            for u in users
        ],
        "next_cursor": next_cursor,
    }


@router.get("/users/{user_id}/following", response_model=FollowListResponse)
async def get_following(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, le=50),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> dict:
    follow_repo = FollowRepository(db)
    users, next_cursor = await follow_repo.get_following_users(
        user_id, limit=limit, cursor=cursor
    )

    following_ids: set[uuid.UUID] = set()
    if current_user:
        ids = await follow_repo.get_following_user_ids(current_user.id)
        following_ids = set(ids)

    return {
        "users": [
            FollowUserItem(
                id=u.id,
                display_name=u.display_name,
                headline=u.headline,
                avatar_url=u.avatar_url,
                insight_score=u.insight_score,
                is_following=u.id in following_ids,
            )
            for u in users
        ],
        "next_cursor": next_cursor,
    }


# ---- User Planters / Logs ----


@router.get("/users/{user_id}/planters", response_model=UserPlanterListResponse)
async def get_user_planters(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    tab: str = Query(default="seeds"),
    cursor: str | None = None,
    limit: int = Query(default=20, le=50),
) -> dict:
    user_repo = UserRepository(db)
    planters, next_cursor = await user_repo.get_user_planters(
        user_id, tab=tab, limit=limit, cursor=cursor
    )
    return {
        "planters": [
            PlanterSummary.model_validate(p) for p in planters
        ],
        "next_cursor": next_cursor,
    }


@router.get("/users/{user_id}/logs", response_model=UserLogListResponse)
async def get_user_logs(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, le=50),
) -> dict:
    user_repo = UserRepository(db)
    logs, next_cursor = await user_repo.get_user_logs(
        user_id, limit=limit, cursor=cursor
    )
    return {
        "logs": [LogHistoryItem(**log) for log in logs],
        "next_cursor": next_cursor,
    }


# ---- Contributions Graph ----


@router.get(
    "/users/{user_id}/contributions", response_model=ContributionGraphResponse
)
async def get_contributions(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    tz: str = Query(default="Asia/Tokyo"),
) -> dict:
    """Get contribution graph data (D8: tz parameter)."""
    user_repo = UserRepository(db)
    graph = await user_repo.get_contribution_graph(user_id, tz=tz)
    return {
        "contributions": [ContributionDay(**g) for g in graph],
    }


# ---- Similar Users ----


@router.get("/users/{user_id}/similar", response_model=list[SimilarUserResponse])
async def get_similar_users(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> list[dict]:
    """Get similar users based on common tags (D11)."""
    user_repo = UserRepository(db)
    follow_repo = FollowRepository(db)

    exclude_ids: list[uuid.UUID] = []
    if current_user:
        following_ids = await follow_repo.get_following_user_ids(current_user.id)
        exclude_ids = following_ids

    similar = await user_repo.get_similar_users(
        user_id, exclude_user_ids=exclude_ids
    )

    following_set = set(exclude_ids)
    return [
        {
            "id": s["user_id"],
            "display_name": s["display_name"],
            "headline": s["headline"],
            "avatar_url": s["avatar_url"],
            "insight_score": s["insight_score"],
            "common_tag_count": s["common_tag_count"],
            "is_following": s["user_id"] in following_set,
        }
        for s in similar
    ]
