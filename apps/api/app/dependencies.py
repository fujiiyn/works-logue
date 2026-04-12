import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.supabase_auth import SupabaseAuthClient, SupabaseAuthError


def _get_auth_client() -> SupabaseAuthClient:
    from app.config import settings

    return SupabaseAuthClient(
        supabase_url=settings.supabase_url,
        anon_key=settings.supabase_publishable_key,
        service_role_key=settings.supabase_service_role_key,
    )


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


async def _find_or_create_user(
    db: AsyncSession,
    auth_id: uuid.UUID,
    auth_client: SupabaseAuthClient,
    email: str | None = None,
    user_metadata: dict | None = None,
) -> User:
    result = await db.execute(select(User).where(User.auth_id == auth_id))
    user = result.scalar_one_or_none()

    if user is not None:
        if user.deleted_at is not None:
            raise HTTPException(status_code=403, detail="Account has been deleted")
        return user

    # Auto-create user on first login (BR-02)
    # Use JWT claims first, fall back to Admin API
    jwt_meta = user_metadata or {}
    display_name = (
        jwt_meta.get("full_name")
        or jwt_meta.get("name")
        or (email or "").split("@")[0]
        or "User"
    )
    avatar_url = jwt_meta.get("avatar_url")

    user = User(
        auth_id=auth_id,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = _extract_bearer_token(request)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_client = _get_auth_client()
    try:
        auth_user = await auth_client.verify_token(token)
    except SupabaseAuthError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await _find_or_create_user(
        db, auth_user.sub, auth_client,
        email=auth_user.email,
        user_metadata=auth_user.user_metadata,
    )

    if user.is_banned:
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            raise HTTPException(status_code=403, detail="Account is banned")

    return user


async def get_optional_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    token = _extract_bearer_token(request)
    if token is None:
        return None

    auth_client = _get_auth_client()
    try:
        auth_user = await auth_client.verify_token(token)
    except SupabaseAuthError:
        return None

    try:
        return await _find_or_create_user(
            db, auth_user.sub, auth_client,
            email=auth_user.email,
            user_metadata=auth_user.user_metadata,
        )
    except HTTPException:
        return None
