import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.reminders.models import Channel, SendStatus
from app.modules.reminders.templates import Kind, Template


class DueReminderOut(BaseModel):
    membership_id: uuid.UUID
    member_id: uuid.UUID
    member_name: str
    phone: str
    email: str | None
    plan_name: str
    end_date: date
    offset_days: int
    kind: Kind
    subject: str
    body: str
    email_status: SendStatus | None
    email_error: str | None
    whatsapp_sent_at: datetime | None


class DueList(BaseModel):
    day: date
    items: list[DueReminderOut]
    email_provider: str


class RunSummaryOut(BaseModel):
    due: int
    emailed: int
    failed: int
    no_email: int
    already_sent: int


class WhatsAppLogIn(BaseModel):
    membership_id: uuid.UUID
    offset_days: int = Field(ge=-60, le=60)


class HistoryItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    member_name: str
    plan_name: str
    end_date: date
    offset_days: int
    channel: Channel
    status: SendStatus
    recipient: str
    error: str | None
    sent_by_name: str | None
    sent_at: datetime


class ReminderSettingsOut(BaseModel):
    enabled: bool
    hour: int
    offsets: list[int]
    templates: dict[Kind, Template]
    customized: list[Kind]
    placeholders: dict[str, str]
    email_provider: str


class ReminderSettingsUpdate(BaseModel):
    enabled: bool | None = None
    hour: int | None = Field(None, ge=0, le=23)
    offsets: list[int] | None = None
    # A kind set to null goes back to the default text.
    templates: dict[Kind, Template | None] | None = None

    @field_validator("offsets")
    @classmethod
    def _valid_offsets(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if len(v) > 10 or any(o < -60 or o > 60 for o in v):
            raise ValueError("Use up to 10 offsets between -60 and 60 days")
        return sorted(set(v), reverse=True)


class PreviewIn(BaseModel):
    template: Template
    kind: Kind


class PreviewOut(BaseModel):
    subject: str
    body: str
