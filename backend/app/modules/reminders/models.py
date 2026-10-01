import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TenantMixin, TimestampMixin


class Channel(enum.StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"  # sent by staff from their own WhatsApp (click-to-chat)


class SendStatus(enum.StrEnum):
    PENDING = "pending"  # claimed by a job run, being sent
    SENT = "sent"
    FAILED = "failed"


def _enum(e: type[enum.StrEnum]) -> Enum:
    return Enum(e, native_enum=False, length=20, values_callable=lambda x: [m.value for m in x])


class ReminderLog(IdMixin, TenantMixin, TimestampMixin, Base):
    """One reminder for one membership, offset and channel. The unique constraint is what
    makes the reminder job safe to run repeatedly or concurrently: a send is claimed by
    inserting this row first."""

    __tablename__ = "reminder_logs"
    __table_args__ = (UniqueConstraint("membership_id", "offset_days", "channel"),)

    membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("members.id", ondelete="CASCADE"), index=True
    )
    offset_days: Mapped[int] = mapped_column(Integer)
    channel: Mapped[Channel] = mapped_column(_enum(Channel))
    status: Mapped[SendStatus] = mapped_column(_enum(SendStatus))
    recipient: Mapped[str] = mapped_column(String(255))
    error: Mapped[str | None] = mapped_column(String(500))
    sent_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
