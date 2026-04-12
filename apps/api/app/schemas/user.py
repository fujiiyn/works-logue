import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    insight_score: float
    role: str
    onboarded_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    tag_ids: list[uuid.UUID] | None = None
    complete_onboarding: bool | None = None


class UserPublicResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    insight_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
