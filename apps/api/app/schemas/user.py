import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator


# --- SNS URL Validators (D12) ---

_SNS_ALLOWLIST: dict[str, list[str]] = {
    "x_url": ["x.com", "twitter.com"],
    "linkedin_url": ["linkedin.com", "www.linkedin.com"],
    "wantedly_url": ["wantedly.com", "www.wantedly.com"],
}

_URL_PATTERN = re.compile(r"^https://([^/]+)")


def _validate_sns_url(value: str | None, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    if not value.startswith("https://"):
        raise ValueError(f"{field_name} must start with https://")
    match = _URL_PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid URL format for {field_name}")
    domain = match.group(1).lower()
    if field_name in _SNS_ALLOWLIST:
        allowed = _SNS_ALLOWLIST[field_name]
        if not any(domain == d or domain.endswith("." + d) for d in allowed):
            raise ValueError(
                f"{field_name} must be from {', '.join(allowed)}"
            )
    return value


def _validate_website_url(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not value.startswith("https://"):
        raise ValueError("website_url must start with https://")
    return value


# --- Response Schemas ---


class UserResponse(BaseModel):
    """Authenticated user's own profile (includes pending_* fields)."""

    id: uuid.UUID
    display_name: str
    headline: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    location: str | None = None
    x_url: str | None = None
    linkedin_url: str | None = None
    wantedly_url: str | None = None
    website_url: str | None = None
    insight_score: float
    role: str
    onboarded_at: datetime | None = None
    pending_avatar_path: str | None = None
    pending_cover_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPublicResponse(BaseModel):
    """Public-facing user info (excludes auth_id, role, is_banned, pending_*)."""

    id: uuid.UUID
    display_name: str
    headline: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    location: str | None = None
    x_url: str | None = None
    linkedin_url: str | None = None
    wantedly_url: str | None = None
    website_url: str | None = None
    insight_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str

    model_config = {"from_attributes": True}


class UserProfileStats(BaseModel):
    insight_score: float
    louge_count: int
    follower_count: int
    following_count: int


class FeaturedContributionResponse(BaseModel):
    planter_id: uuid.UUID
    planter_title: str
    planter_status: str
    total_score: float


class UserProfileResponse(BaseModel):
    """Full public profile with stats, tags, featured_contribution, is_following."""

    user: UserPublicResponse
    stats: UserProfileStats
    tags: list[TagResponse]
    featured_contribution: FeaturedContributionResponse | None = None
    is_following: bool = False
    is_own_profile: bool = False


class ContributionDay(BaseModel):
    date: date
    count: int


class ContributionGraphResponse(BaseModel):
    contributions: list[ContributionDay]


class PlanterSummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    log_count: int
    contributor_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPlanterListResponse(BaseModel):
    planters: list[PlanterSummary]
    next_cursor: str | None = None


class LogHistoryItem(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    planter_id: uuid.UUID
    planter_title: str
    planter_status: str


class UserLogListResponse(BaseModel):
    logs: list[LogHistoryItem]
    next_cursor: str | None = None


class FollowUserItem(BaseModel):
    id: uuid.UUID
    display_name: str
    headline: str | None = None
    avatar_url: str | None = None
    insight_score: float
    is_following: bool = False

    model_config = {"from_attributes": True}


class FollowListResponse(BaseModel):
    users: list[FollowUserItem]
    next_cursor: str | None = None


class SimilarUserResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    headline: str | None = None
    avatar_url: str | None = None
    insight_score: float
    common_tag_count: int
    is_following: bool = False


# --- Update Schema ---


class UserUpdate(BaseModel):
    display_name: str | None = None
    headline: str | None = None
    bio: str | None = None
    location: str | None = None
    x_url: str | None = None
    linkedin_url: str | None = None
    wantedly_url: str | None = None
    website_url: str | None = None
    tag_ids: list[uuid.UUID] | None = None
    complete_onboarding: bool | None = None

    @field_validator("x_url")
    @classmethod
    def validate_x_url(cls, v: str | None) -> str | None:
        return _validate_sns_url(v, "x_url")

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: str | None) -> str | None:
        return _validate_sns_url(v, "linkedin_url")

    @field_validator("wantedly_url")
    @classmethod
    def validate_wantedly_url(cls, v: str | None) -> str | None:
        return _validate_sns_url(v, "wantedly_url")

    @field_validator("website_url")
    @classmethod
    def validate_website_url(cls, v: str | None) -> str | None:
        return _validate_website_url(v)


class ImageUploadResponse(BaseModel):
    url: str
