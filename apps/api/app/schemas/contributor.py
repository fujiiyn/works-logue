import uuid

from pydantic import BaseModel


class ContributorResponse(BaseModel):
    user_id: uuid.UUID
    display_name: str
    avatar_url: str | None
    insight_score_earned: float
    log_count: int
    is_seed_author: bool


class ContributorsListResponse(BaseModel):
    contributors: list[ContributorResponse]
