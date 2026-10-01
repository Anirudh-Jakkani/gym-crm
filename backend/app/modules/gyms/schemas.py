import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.gyms.models import Role


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GymOut(ORMModel):
    id: uuid.UUID
    name: str
    logo_url: str | None
    brand_color: str
    timezone: str
    currency: str
    phone: str | None
    reminder_offsets: list[int]
    checkup_interval_days: int


class GymUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    logo_url: str | None = None
    brand_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    timezone: str | None = None
    currency: str | None = Field(None, min_length=3, max_length=3)
    phone: str | None = Field(None, max_length=30)
    reminder_offsets: list[int] | None = None
    checkup_interval_days: int | None = Field(None, ge=1, le=90)

    @field_validator("reminder_offsets")
    @classmethod
    def _valid_offsets(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if len(v) > 10 or any(o < -60 or o > 60 for o in v):
            raise ValueError("Use up to 10 offsets between -60 and 60 days")
        return sorted(set(v), reverse=True)


class BranchIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)


class BranchUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)


class BranchOut(ORMModel):
    id: uuid.UUID
    name: str
    address: str | None
    phone: str | None


class StaffOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    email: str
    role: Role
    branch_id: uuid.UUID | None
    joined_at: datetime


class StaffUpdate(BaseModel):
    role: Role | None = None
    branch_id: uuid.UUID | None = None


class InviteIn(BaseModel):
    email: EmailStr
    role: Role
    branch_id: uuid.UUID | None = None


class InviteOut(ORMModel):
    id: uuid.UUID
    email: str
    role: Role
    branch_id: uuid.UUID | None
    expires_at: datetime
    accepted_at: datetime | None
    url: str
