import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", "category", name="uq_tags_name_category"),
        CheckConstraint(
            "category IN ('industry', 'occupation', 'role', 'situation', 'skill', 'knowledge')",
            name="chk_tags_category",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_tag_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tags.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_leaf: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class PlanterTag(Base):
    __tablename__ = "planter_tags"

    planter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("planters.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id"), primary_key=True
    )


class UserTag(Base):
    __tablename__ = "user_tags"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id"), primary_key=True
    )
