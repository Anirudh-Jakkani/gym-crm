from decimal import Decimal

from sqlalchemy import JSON, Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.dates import DurationUnit
from app.core.db import Base, IdMixin, TenantMixin, TimestampMixin

duration_unit_enum = Enum(
    DurationUnit, native_enum=False, length=10, values_callable=lambda e: [m.value for m in e]
)


class Plan(IdMixin, TenantMixin, TimestampMixin, Base):
    """A membership plan the gym sells, e.g. "Quarterly – Gym + Cardio", 3 months, ₹4,500."""

    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    duration_value: Mapped[int] = mapped_column(Integer)
    duration_unit: Mapped[DurationUnit] = mapped_column(duration_unit_enum)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    joining_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal(0))
    tax_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal(0))
    services: Mapped[list[str]] = mapped_column(JSON, default=list)
    max_freeze_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
