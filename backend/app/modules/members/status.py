"""Membership/member status rules, in Python (for one record) and SQL (for lists and counts).

Both must agree; tests cover the combinations.
"""

import enum
from datetime import date, timedelta

from sqlalchemy import ColumnElement, and_, case, select
from sqlalchemy.orm import aliased

from app.modules.members.models import Member, Membership

EXPIRING_SOON_DAYS = 7


class Status(enum.StrEnum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    EXPIRING = "expiring"  # active, ending within EXPIRING_SOON_DAYS
    FROZEN = "frozen"
    EXPIRED = "expired"
    CANCELLED = "cancelled"  # membership only
    NONE = "none"  # member only: never had a membership


def membership_status(m: Membership, today: date) -> Status:
    if m.cancelled_at is not None:
        return Status.CANCELLED
    if m.end_date < today:
        return Status.EXPIRED
    if m.start_date > today:
        return Status.UPCOMING
    if m.freeze_start and m.freeze_end and m.freeze_start <= today <= m.freeze_end:
        return Status.FROZEN
    if m.end_date <= today + timedelta(days=EXPIRING_SOON_DAYS):
        return Status.EXPIRING
    return Status.ACTIVE


def pick_current(memberships: list[Membership], today: date) -> Membership | None:
    """The membership that describes the member now: the earliest one that hasn't ended
    yet (so a running membership wins over an upcoming renewal), else the latest ended one."""
    live = [m for m in memberships if m.cancelled_at is None]
    ongoing = sorted((m for m in live if m.end_date >= today), key=lambda m: m.end_date)
    if ongoing:
        return ongoing[0]
    return max(live, key=lambda m: m.end_date, default=None)


# --- SQL equivalents ---------------------------------------------------------

CurrentMembership = aliased(Membership, name="current_membership")


def current_membership_id(today: date):
    """Correlated subquery: id of the member's current membership (same rule as pick_current)."""
    m = aliased(Membership)
    not_ended = m.end_date >= today
    return (
        select(m.id)
        .where(m.member_id == Member.id, m.cancelled_at.is_(None))
        .order_by(
            case((not_ended, 0), else_=1),
            case((not_ended, m.end_date)).asc(),
            m.end_date.desc(),
        )
        .limit(1)
        .correlate(Member)
        .scalar_subquery()
    )


def status_expr(today: date) -> ColumnElement[str]:
    """Member status computed from the outer-joined CurrentMembership row."""
    cm = CurrentMembership
    return case(
        (cm.id.is_(None), Status.NONE.value),
        (cm.end_date < today, Status.EXPIRED.value),
        (cm.start_date > today, Status.UPCOMING.value),
        (
            and_(cm.freeze_start <= today, cm.freeze_end >= today),
            Status.FROZEN.value,
        ),
        (cm.end_date <= today + timedelta(days=EXPIRING_SOON_DAYS), Status.EXPIRING.value),
        else_=Status.ACTIVE.value,
    )
