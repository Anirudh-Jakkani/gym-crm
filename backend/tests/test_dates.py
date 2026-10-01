from datetime import date

import pytest

from app.core.dates import DurationUnit as U
from app.core.dates import membership_end


@pytest.mark.parametrize(
    ("start", "value", "unit", "end"),
    [
        (date(2026, 1, 15), 1, U.MONTH, date(2026, 2, 14)),
        (date(2026, 1, 1), 1, U.MONTH, date(2026, 1, 31)),
        (date(2026, 1, 31), 1, U.MONTH, date(2026, 2, 28)),  # clamped -> end of Feb
        (date(2028, 1, 31), 1, U.MONTH, date(2028, 2, 29)),  # leap year
        (date(2026, 3, 31), 1, U.MONTH, date(2026, 4, 30)),
        (date(2026, 11, 15), 3, U.MONTH, date(2027, 2, 14)),  # crosses year
        (date(2026, 1, 1), 1, U.YEAR, date(2026, 12, 31)),
        (date(2028, 2, 29), 1, U.YEAR, date(2029, 2, 28)),
        (date(2026, 1, 1), 2, U.WEEK, date(2026, 1, 14)),
        (date(2026, 1, 1), 1, U.DAY, date(2026, 1, 1)),
        (date(2026, 1, 1), 10, U.DAY, date(2026, 1, 10)),
    ],
)
def test_membership_end(start, value, unit, end):
    assert membership_end(start, value, unit) == end
