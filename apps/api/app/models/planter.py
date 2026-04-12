import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Planter(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "planters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('seed', 'sprout', 'louge', 'archived')", name="chk_planters_status"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(nullable=False)
    seed_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seed_types.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="seed", server_default="'seed'"
    )
    louge_content: Mapped[str | None] = mapped_column(nullable=True)
    louge_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    structure_fulfillment: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )
    maturity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    log_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    contributor_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    parent_planter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("planters.id"), nullable=True
    )
