"""Reminder message templates with {placeholder} substitution."""

import enum
import re
from datetime import date

from pydantic import BaseModel, Field


class Kind(enum.StrEnum):
    BEFORE = "before"  # membership ends in N days
    ON_DAY = "on_day"  # ends today
    AFTER = "after"  # ended N days ago


def kind_for(offset_days: int) -> Kind:
    if offset_days > 0:
        return Kind.BEFORE
    return Kind.ON_DAY if offset_days == 0 else Kind.AFTER


class Template(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=3000)


PLACEHOLDERS = {
    "first_name": "Member's first name",
    "name": "Member's full name",
    "plan_name": "Plan name",
    "end_date": "Membership end date",
    "days": "Days until / since the end date",
    "gym_name": "Your gym's name",
    "gym_phone": "Your gym's phone number",
    "preview_link": "Member's personal page link",
}

DEFAULTS: dict[Kind, Template] = {
    Kind.BEFORE: Template(
        subject="Your {gym_name} membership ends in {days} days",
        body=(
            "Hi {first_name},\n\n"
            "Your {plan_name} membership at {gym_name} ends on {end_date} ({days} days left). "
            "Renew before then to keep training without a break.\n\n"
            "Questions? Call us on {gym_phone}.\n\n"
            "– {gym_name}"
        ),
    ),
    Kind.ON_DAY: Template(
        subject="Your {gym_name} membership ends today",
        body=(
            "Hi {first_name},\n\n"
            "Your {plan_name} membership at {gym_name} ends today ({end_date}). "
            "Renew today so your training isn't interrupted.\n\n"
            "Questions? Call us on {gym_phone}.\n\n"
            "– {gym_name}"
        ),
    ),
    Kind.AFTER: Template(
        subject="We miss you at {gym_name}",
        body=(
            "Hi {first_name},\n\n"
            "Your {plan_name} membership at {gym_name} ended on {end_date}. "
            "We'd love to have you back – drop by or call us on {gym_phone} to renew.\n\n"
            "– {gym_name}"
        ),
    ),
}

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def render(text: str, values: dict[str, str]) -> str:
    """Replaces {known_placeholder}; anything else is left untouched. Deliberately not
    str.format, which would allow attribute access in owner-written templates."""
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)


def template_for(stored: dict | None, kind: Kind) -> Template:
    raw = (stored or {}).get(kind.value)
    return Template.model_validate(raw) if raw else DEFAULTS[kind]


def values_for(
    *,
    member_name: str,
    plan_name: str,
    end_date: date,
    offset_days: int,
    gym_name: str,
    gym_phone: str | None,
    preview_link: str,
) -> dict[str, str]:
    return {
        "first_name": member_name.split()[0] if member_name.split() else member_name,
        "name": member_name,
        "plan_name": plan_name,
        "end_date": f"{end_date:%d %b %Y}",
        "days": str(abs(offset_days)),
        "gym_name": gym_name,
        "gym_phone": gym_phone or "",
        "preview_link": preview_link,
    }
