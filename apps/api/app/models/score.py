import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LougeScoreSnapshot(Base):
    __tablename__ = "louge_score_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    planter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planters.id"), nullable=False)
    trigger_log_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("logs.id"), nullable=True
    )
    structure_fulfillment: Mapped[float] = mapped_column(Float, nullable=False)
    maturity_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    maturity_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed_structure: Mapped[bool] = mapped_column(Boolean, nullable=False)
    passed_maturity: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InsightScoreEvent(Base):
    __tablename__ = "insight_score_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    planter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planters.id"), nullable=False)
    log_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("logs.id"), nullable=True)
    score_delta: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
