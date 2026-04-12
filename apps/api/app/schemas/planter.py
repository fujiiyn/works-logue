import uuid
from base64 import b64decode, b64encode
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.seed_type import SeedTypeResponse
from app.schemas.tag import TagResponse
from app.schemas.user import UserPublicResponse


class PlanterCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000)
    seed_type_id: uuid.UUID
    tag_ids: list[uuid.UUID] = []


class PlanterResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    status: str
    seed_type: SeedTypeResponse
    user: UserPublicResponse
    tags: list[TagResponse]
    log_count: int
    contributor_count: int
    progress: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanterCardResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    seed_type: SeedTypeResponse
    user: UserPublicResponse
    tags: list[TagResponse]
    log_count: int
    contributor_count: int
    progress: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CursorPaginatedResponse(BaseModel):
    items: list[PlanterCardResponse]
    next_cursor: str | None = None
    has_next: bool = False

    @staticmethod
    def encode_cursor(created_at: datetime, planter_id: uuid.UUID) -> str:
        # Store timestamp as-is (DB native format)
        raw = f"{created_at.isoformat()}|{planter_id}"
        return b64encode(raw.encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
        raw = b64decode(cursor.encode()).decode()
        parts = raw.split("|", 1)
        return datetime.fromisoformat(parts[0]), uuid.UUID(parts[1])
