import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TenantMixin, TimestampMixin, UTCDateTime


class PlanStatus(enum.StrEnum):
    GENERATING = "generating"
    FAILED = "failed"
    DRAFT = "draft"  # generated, waiting for trainer review
    PUBLISHED = "published"  # what the member sees (one per member)
    ARCHIVED = "archived"  # replaced by a newer published plan


class AIPlan(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "ai_plans"

    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("members.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(
            PlanStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]
        )
    )
    title: Mapped[str] = mapped_column(String(200))
    # Inputs the trainer chose (days per week, equipment, instructions) - kept for regenerating.
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    content: Mapped[dict | None] = mapped_column(JSON)  # PlanContent
    error: Mapped[str | None] = mapped_column(Text)

    model: Mapped[str | None] = mapped_column(String(60))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
