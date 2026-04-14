import uuid
from datetime import datetime

from pydantic import BaseModel


class StructurePartsResponse(BaseModel):
    context: bool
    problem: bool
    solution: bool
    name: bool


class PlanterScoreResponse(BaseModel):
    id: uuid.UUID
    status: str
    log_count: int
    contributor_count: int
    progress: float
    structure_fulfillment: float
    maturity_score: float | None
    structure_parts: StructurePartsResponse | None

    model_config = {"from_attributes": True}


class PlanterScoreWithPendingResponse(BaseModel):
    score: PlanterScoreResponse
    score_pending: bool
    last_scored_at: datetime | None


class ScoreSettingsResponse(BaseModel):
    min_contributors: int
    min_logs: int
    bloom_threshold: float
    bud_threshold: float
