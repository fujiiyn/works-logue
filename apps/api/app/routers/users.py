import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.tag_repository import TagRepository
from app.schemas.user import UserPublicResponse, UserResponse, UserUpdate

router = APIRouter(tags=["users"])


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
        current_user.display_name = body.display_name.strip() if body.display_name else body.display_name

    # Validate display_name for onboarding
    if body.complete_onboarding:
        if not current_user.display_name or not current_user.display_name.strip():
            raise HTTPException(status_code=422, detail="display_name is required for onboarding")
    if body.bio is not None:
        current_user.bio = body.bio

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

    # Complete onboarding
    if body.complete_onboarding:
        current_user.onboarded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/users/{user_id}", response_model=UserPublicResponse)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
