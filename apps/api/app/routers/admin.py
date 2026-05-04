"""U7 Phase 6: /api/v1/admin/* endpoints.

All endpoints in this module are gated by `require_admin`, which collapses
authentication / authorization failures to 404 to keep the existence of
the admin surface secret (BR-A01, Q10=B).

Mutating endpoints emit a single structured log event per call (BR-A14).
"""
from __future__ import annotations

import uuid
from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies_admin import require_admin
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminAuthorSummary,
    AdminBanRequest,
    AdminPlanterDeleteRequest,
    AdminPlanterItem,
    AdminPlanterListResponse,
    AdminSeedTypeItem,
    AdminSeedTypeUpdateRequest,
    AdminStatsResponse,
    AdminUserItem,
    AdminUserListResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])
_logger = structlog.get_logger()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminStatsResponse:
    repo = AdminRepository(db)
    stats = await repo.get_dashboard_stats()
    return AdminStatsResponse(**stats)


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query(max_length=200)] = None,
    status: Annotated[Literal["all", "normal", "banned"], Query()] = "all",
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1)] = 20,
) -> AdminUserListResponse:
    repo = AdminRepository(db)
    items, total = await repo.list_users(
        q=q, status=status, page=page, per_page=per_page
    )
    # Re-derive the effective per_page after AdminRepository's clamp so the
    # response advertises what was actually applied (rather than the request).
    effective_per_page = max(1, min(per_page, 100))
    return AdminUserListResponse(
        items=[
            AdminUserItem(**item, is_self=(item["id"] == admin.id))
            for item in items
        ],
        total=total,
        page=max(1, page),
        per_page=effective_per_page,
    )


async def _load_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not Found")
    return user


def _user_to_admin_item(
    user: User,
    *,
    planter_count: int = 0,
    log_count: int = 0,
    is_self: bool = False,
) -> AdminUserItem:
    return AdminUserItem(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
        is_banned=user.is_banned,
        banned_at=user.banned_at,
        ban_reason=user.ban_reason,
        planter_count=planter_count,
        log_count=log_count,
        created_at=user.created_at,
        is_self=is_self,
    )


@router.post("/users/{user_id}/ban", response_model=AdminUserItem)
async def ban_user(
    user_id: uuid.UUID,
    body: AdminBanRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUserItem:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="自分を BAN できません")

    target = await _load_user_or_404(db, user_id)

    if target.role == "admin":
        raise HTTPException(
            status_code=400, detail="admin ユーザーは BAN できません"
        )

    repo = AdminRepository(db)
    await repo.ban_user(target, reason=body.reason)
    await db.commit()
    await db.refresh(target)

    _logger.info(
        "admin.user.ban",
        actor_user_id=str(admin.id),
        target_user_id=str(target.id),
        ban_reason=body.reason,
    )

    return _user_to_admin_item(target, is_self=False)


@router.post("/users/{user_id}/unban", response_model=AdminUserItem)
async def unban_user(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUserItem:
    target = await _load_user_or_404(db, user_id)

    repo = AdminRepository(db)
    await repo.unban_user(target)
    await db.commit()
    await db.refresh(target)

    _logger.info(
        "admin.user.unban",
        actor_user_id=str(admin.id),
        target_user_id=str(target.id),
    )

    return _user_to_admin_item(target, is_self=(target.id == admin.id))


# ---- Planter endpoints ------------------------------------------------------


async def _load_planter_or_404(
    db: AsyncSession, planter_id: uuid.UUID, *, allow_deleted: bool = False
) -> Planter:
    result = await db.execute(select(Planter).where(Planter.id == planter_id))
    planter = result.scalar_one_or_none()
    if planter is None:
        raise HTTPException(status_code=404, detail="Not Found")
    if not allow_deleted and planter.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not Found")
    return planter


async def _planter_to_admin_item(
    db: AsyncSession, planter: Planter
) -> AdminPlanterItem:
    """Hydrate a single Planter with author + seed_type_name for response."""
    from app.models.seed_type import SeedType

    author = (
        await db.execute(select(User).where(User.id == planter.user_id))
    ).scalar_one()
    st_name = (
        await db.execute(
            select(SeedType.name).where(SeedType.id == planter.seed_type_id)
        )
    ).scalar_one()
    return AdminPlanterItem(
        id=planter.id,
        title=planter.title,
        status=planter.status,
        seed_type_name=st_name,
        author=AdminAuthorSummary(
            id=author.id,
            display_name=author.display_name,
            avatar_url=author.avatar_url,
        ),
        log_count=planter.log_count,
        contributor_count=planter.contributor_count,
        created_at=planter.created_at,
        updated_at=planter.updated_at,
        deleted_at=planter.deleted_at,
    )


@router.get("/planters", response_model=AdminPlanterListResponse)
async def list_planters(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query(max_length=200)] = None,
    status: Annotated[
        Literal["all", "seed", "sprout", "louge", "archived", "deleted"], Query()
    ] = "all",
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1)] = 20,
) -> AdminPlanterListResponse:
    repo = AdminRepository(db)
    items, total = await repo.list_planters(
        q=q, status=status, page=page, per_page=per_page
    )
    effective_per_page = max(1, min(per_page, 100))
    return AdminPlanterListResponse(
        items=[AdminPlanterItem(**item) for item in items],
        total=total,
        page=max(1, page),
        per_page=effective_per_page,
    )


@router.post("/planters/{planter_id}/archive", response_model=AdminPlanterItem)
async def archive_planter(
    planter_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminPlanterItem:
    planter = await _load_planter_or_404(db, planter_id)

    repo = AdminRepository(db)
    await repo.archive_planter(planter)
    await db.commit()
    await db.refresh(planter)

    _logger.info(
        "admin.planter.archive",
        actor_user_id=str(admin.id),
        planter_id=str(planter.id),
    )
    return await _planter_to_admin_item(db, planter)


@router.post("/planters/{planter_id}/restore", response_model=AdminPlanterItem)
async def restore_planter(
    planter_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminPlanterItem:
    planter = await _load_planter_or_404(db, planter_id)

    repo = AdminRepository(db)
    try:
        await repo.restore_planter(planter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="アーカイブされていません") from e
    await db.commit()
    await db.refresh(planter)

    _logger.info(
        "admin.planter.restore",
        actor_user_id=str(admin.id),
        planter_id=str(planter.id),
    )
    return await _planter_to_admin_item(db, planter)


@router.delete("/planters/{planter_id}", status_code=204)
async def delete_planter(
    planter_id: uuid.UUID,
    body: AdminPlanterDeleteRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    planter = await _load_planter_or_404(db, planter_id)

    # BR-A12 / D7: trim both sides, then strict (case-sensitive) equality.
    if body.confirm_title.strip() != planter.title.strip():
        raise HTTPException(status_code=400, detail="タイトルが一致しません")

    title_for_log = planter.title  # capture before soft-delete

    repo = AdminRepository(db)
    await repo.soft_delete_planter(planter)
    await db.commit()

    _logger.info(
        "admin.planter.delete",
        actor_user_id=str(admin.id),
        planter_id=str(planter.id),
        title=title_for_log,
    )
    return Response(status_code=204)


# ---- SeedType endpoints ------------------------------------------------------


async def _load_seed_type_or_404(
    db: AsyncSession, seed_type_id: uuid.UUID
) -> SeedType:
    result = await db.execute(select(SeedType).where(SeedType.id == seed_type_id))
    seed_type = result.scalar_one_or_none()
    if seed_type is None:
        raise HTTPException(status_code=404, detail="Not Found")
    return seed_type


@router.get("/seed-types", response_model=list[AdminSeedTypeItem])
async def list_admin_seed_types(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[Literal["all", "active", "inactive"], Query()] = "all",
) -> list[AdminSeedTypeItem]:
    repo = AdminRepository(db)
    rows = await repo.list_seed_types(status=status)
    return [AdminSeedTypeItem.model_validate(r) for r in rows]


@router.patch("/seed-types/{seed_type_id}", response_model=AdminSeedTypeItem)
async def update_admin_seed_type(
    seed_type_id: uuid.UUID,
    body: AdminSeedTypeUpdateRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminSeedTypeItem:
    seed_type = await _load_seed_type_or_404(db, seed_type_id)
    before = seed_type.description

    repo = AdminRepository(db)
    await repo.update_seed_type_description(seed_type, body.description)
    await db.commit()
    await db.refresh(seed_type)

    _logger.info(
        "admin.seed_type.update",
        actor_user_id=str(admin.id),
        seed_type_id=str(seed_type.id),
        before_description=before,
        after_description=seed_type.description,
    )
    return AdminSeedTypeItem.model_validate(seed_type)


@router.post(
    "/seed-types/{seed_type_id}/toggle-active",
    response_model=AdminSeedTypeItem,
)
async def toggle_admin_seed_type_active(
    seed_type_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminSeedTypeItem:
    seed_type = await _load_seed_type_or_404(db, seed_type_id)
    before = seed_type.is_active

    repo = AdminRepository(db)
    await repo.toggle_seed_type_active(seed_type)
    await db.commit()
    await db.refresh(seed_type)

    _logger.info(
        "admin.seed_type.update",
        actor_user_id=str(admin.id),
        seed_type_id=str(seed_type.id),
        before_is_active=before,
        after_is_active=seed_type.is_active,
    )
    return AdminSeedTypeItem.model_validate(seed_type)
