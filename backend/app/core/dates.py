import calendar
import enum
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class DurationUnit(enum.StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


def _add_months(start: date, months: int) -> tuple[date, bool]:
    """Returns (date, clamped). Clamped means the day didn't exist in the target month."""
    years, month_index = divmod(start.month - 1 + months, 12)
    year, month = start.year + years, month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, last_day)), start.day > last_day


def membership_end(start: date, value: int, unit: DurationUnit) -> date:
    """Last day (inclusive) of a membership that starts on `start`.

    1 month from 15 Jan ends 14 Feb. When the start day doesn't exist in the target
    month (31 Jan + 1 month), the membership runs to the end of that month (28/29 Feb).
    """
    if unit == DurationUnit.DAY:
        return start + timedelta(days=value - 1)
    if unit == DurationUnit.WEEK:
        return start + timedelta(weeks=value) - timedelta(days=1)
    months = value * 12 if unit == DurationUnit.YEAR else value
    target, clamped = _add_months(start, months)
    return target if clamped else target - timedelta(days=1)


def today_in(timezone: str) -> date:
    try:
        return datetime.now(ZoneInfo(timezone)).date()
    except ZoneInfoNotFoundError:
        return datetime.now(ZoneInfo("UTC")).date()
