"""U7 Step 3: admin authorization dependency.

Enforces BR-A01: admin access is conditional on
  role == 'admin' AND is_banned == False AND deleted_at IS NULL.

Any failure (including unauthenticated and unauthorized) returns
404 Not Found to keep the existence of /admin endpoints secret (Q10=B).
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import extract_bearer_token, get_auth_client
from app.models.user import User
from app.services.supabase_auth import SupabaseAuthError

_logger = structlog.get_logger()


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Not Found")


async def require_admin(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve the current user and enforce admin role; otherwise 404.

    Unlike get_current_user, this dependency NEVER auto-creates a user row.
    Admin endpoints must only ever be reached by an existing admin record;
    otherwise the response collapses to 404 to keep /admin paths secret.
    """
    token = extract_bearer_token(request)
    if token is None:
        raise _not_found()

    auth_client = get_auth_client()
    try:
        auth_user = await auth_client.verify_token(token)
    except SupabaseAuthError:
        raise _not_found() from None

    result = await db.execute(select(User).where(User.auth_id == auth_user.sub))
    user = result.scalar_one_or_none()

    if (
        user is None
        or user.role != "admin"
        or user.is_banned
        or user.deleted_at is not None
    ):
        raise _not_found()

    _logger.info(
        "admin.access",
        actor_user_id=str(user.id),
        path=request.url.path,
        method=request.method,
    )

    return user
