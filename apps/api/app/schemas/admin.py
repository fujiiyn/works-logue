"""U7 Admin: Pydantic schemas for /api/v1/admin/* endpoints.

These schemas describe the wire format of the admin API. AdminRepository
returns plain dicts that match these models field-by-field; the router
attaches `is_self` per row before serialization.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# ---- Stats ------------------------------------------------------------------


class AdminStatsResponse(BaseModel):
    total_users: int
    total_planters: int
    new_planters_today: int
    pending_louge_count: int


# ---- Users ------------------------------------------------------------------


class AdminUserItem(BaseModel):
    id: uuid.UUID
    display_name: str
    avatar_url: str | None = None
    role: str
    is_banned: bool
    banned_at: datetime | None = None
    ban_reason: str | None = None
    planter_count: int
    log_count: int
    created_at: datetime
    is_self: bool = False

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    per_page: int


class AdminBanRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


# ---- Planters ---------------------------------------------------------------


class AdminAuthorSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class AdminPlanterItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    seed_type_name: str
    author: AdminAuthorSummary
    log_count: int
    contributor_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminPlanterListResponse(BaseModel):
    items: list[AdminPlanterItem]
    total: int
    page: int
    per_page: int


class AdminPlanterDeleteRequest(BaseModel):
    confirm_title: str


# ---- SeedTypes --------------------------------------------------------------


class AdminSeedTypeItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSeedTypeUpdateRequest(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def _trim_and_validate(cls, v: str) -> str:
        # BR-A16: 1〜1000 chars after trim. Empty or whitespace-only → 422.
        trimmed = v.strip()
        if len(trimmed) == 0:
            raise ValueError("説明は必須です")
        if len(trimmed) > 1000:
            raise ValueError("説明は 1000 文字以内で入力してください")
        return trimmed
