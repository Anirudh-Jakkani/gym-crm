import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.core.dates import DurationUnit
from app.core.schemas import Money, MoneyIn, ORMModel


def _clean_services(v: list[str] | None) -> list[str] | None:
    if v is None:
        return v
    seen: dict[str, None] = {}
    for s in v:
        s = s.strip()
        if s:
            seen.setdefault(s[:60], None)
    if len(seen) > 20:
        raise ValueError("Up to 20 services per plan")
    return list(seen)


class PlanBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(None, max_length=2000)
    duration_value: int = Field(ge=1, le=1000)
    duration_unit: DurationUnit
    price: MoneyIn
    joining_fee: MoneyIn = Decimal(0)
    tax_pct: Decimal = Field(Decimal(0), ge=0, le=100, decimal_places=2)
    services: list[str] = []
    max_freeze_days: int = Field(0, ge=0, le=365)

    _services = field_validator("services")(_clean_services)


class PlanIn(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    description: str | None = Field(None, max_length=2000)
    duration_value: int | None = Field(None, ge=1, le=1000)
    duration_unit: DurationUnit | None = None
    price: MoneyIn | None = None
    joining_fee: MoneyIn | None = None
    tax_pct: Decimal | None = Field(None, ge=0, le=100, decimal_places=2)
    services: list[str] | None = None
    max_freeze_days: int | None = Field(None, ge=0, le=365)
    is_active: bool | None = None

    _services = field_validator("services")(_clean_services)


class PlanOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    duration_value: int
    duration_unit: DurationUnit
    price: Money
    joining_fee: Money
    tax_pct: Money
    services: list[str]
    max_freeze_days: int
    is_active: bool
    active_members: int = 0
