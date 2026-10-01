import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, IdMixin, TenantMixin, TimestampMixin


class CheckUp(IdMixin, TenantMixin, TimestampMixin, Base):
    """A body-composition check-in for a member. At most one per member per day."""

    __tablename__ = "checkups"
    __table_args__ = (UniqueConstraint("member_id", "recorded_on"),)

    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("members.id", ondelete="CASCADE"), index=True
    )
    recorded_on: Mapped[date] = mapped_column(Date, index=True)

    weight_kg: Mapped[float | None] = mapped_column(Float)
    height_cm: Mapped[float | None] = mapped_column(Float)  # used for BMI at the time
    bmi: Mapped[float | None] = mapped_column(Float)
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    muscle_mass_kg: Mapped[float | None] = mapped_column(Float)

    chest_cm: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    hips_cm: Mapped[float | None] = mapped_column(Float)
    arm_cm: Mapped[float | None] = mapped_column(Float)
    thigh_cm: Mapped[float | None] = mapped_column(Float)

    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    photos: Mapped[list["CheckUpPhoto"]] = relationship(
        back_populates="checkup", cascade="all, delete-orphan", order_by="CheckUpPhoto.created_at"
    )


class CheckUpPhoto(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "checkup_photos"

    checkup_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("checkups.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(String(300), unique=True)
    content_type: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(Integer)

    checkup: Mapped[CheckUp] = relationship(back_populates="photos")
