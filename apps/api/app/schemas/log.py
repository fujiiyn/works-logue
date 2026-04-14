import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserPublicResponse


class LogCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    parent_log_id: uuid.UUID | None = None


class LogResponse(BaseModel):
    id: uuid.UUID
    planter_id: uuid.UUID
    user: UserPublicResponse | None
    body: str
    parent_log_id: uuid.UUID | None
    is_ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LogWithRepliesResponse(BaseModel):
    id: uuid.UUID
    planter_id: uuid.UUID
    user: UserPublicResponse | None
    body: str
    is_ai_generated: bool
    created_at: datetime
    replies: list[LogResponse]

    model_config = {"from_attributes": True}


class LogCreateResponse(BaseModel):
    log: LogResponse
    planter: "PlanterScoreResponse"
    score_pending: bool


from app.schemas.score import PlanterScoreResponse  # noqa: E402

LogCreateResponse.model_rebuild()
