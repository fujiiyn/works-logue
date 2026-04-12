import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    auth_id: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)
    insight_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default="'user'")
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ban_reason: Mapped[str | None] = mapped_column(nullable=True)
