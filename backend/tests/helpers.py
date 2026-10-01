from datetime import date, timedelta

from httpx import AsyncClient

from app.core.dates import today_in
from tests.conftest import Account


def today() -> date:
    # New gyms default to Asia/Kolkata.
    return today_in("Asia/Kolkata")


def days(n: int) -> str:
    return (today() + timedelta(days=n)).isoformat()


async def make_plan(client: AsyncClient, acct: Account, **overrides) -> dict:
    body = {
        "name": "Monthly",
        "duration_value": 1,
        "duration_unit": "month",
        "price": 3000,
        "joining_fee": 500,
        "tax_pct": 18,
        "max_freeze_days": 15,
        "services": ["Gym", "Cardio"],
        **overrides,
    }
    res = await client.post("/api/plans", json=body, headers=acct.headers)
    assert res.status_code == 201, res.text
    return res.json()


async def make_member(client: AsyncClient, acct: Account, phone="9876543210", **overrides) -> dict:
    body = {"name": "Ravi Kumar", "phone": phone, **overrides}
    res = await client.post("/api/members", json=body, headers=acct.headers)
    assert res.status_code == 201, res.text
    return res.json()
