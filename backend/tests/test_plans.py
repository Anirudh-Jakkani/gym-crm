from httpx import AsyncClient

from tests.conftest import Account
from tests.helpers import make_member, make_plan
from tests.test_gym_and_staff import invite_and_accept


async def test_create_and_list_plans(client: AsyncClient, owner: Account):
    plan = await make_plan(client, owner, services=[" Gym ", "Gym", "Steam", ""])
    assert plan["price"] == 3000
    assert plan["tax_pct"] == 18
    assert plan["services"] == ["Gym", "Steam"]
    assert plan["active_members"] == 0

    await make_plan(
        client, owner, name="Yearly", duration_value=1, duration_unit="year", price=24000
    )
    names = [p["name"] for p in (await client.get("/api/plans", headers=owner.headers)).json()]
    assert names == ["Monthly", "Yearly"]  # sorted by price


async def test_plan_validation(client: AsyncClient, owner: Account):
    bad = {"name": "X", "duration_value": 0, "duration_unit": "fortnight", "price": -1}
    res = await client.post("/api/plans", json=bad, headers=owner.headers)
    assert res.status_code == 422


async def test_archive_hides_plan_and_blocks_new_sales(client: AsyncClient, owner: Account):
    plan = await make_plan(client, owner)
    res = await client.patch(
        f"/api/plans/{plan['id']}", json={"is_active": False}, headers=owner.headers
    )
    assert res.json()["is_active"] is False
    assert (await client.get("/api/plans", headers=owner.headers)).json() == []
    archived = await client.get("/api/plans?include_archived=true", headers=owner.headers)
    assert len(archived.json()) == 1

    res = await client.post(
        "/api/members",
        json={"name": "Asha", "phone": "9000000001", "membership": {"plan_id": plan["id"]}},
        headers=owner.headers,
    )
    assert res.status_code == 409


async def test_delete_only_unsold_plans(client: AsyncClient, owner: Account):
    unsold = await make_plan(client, owner, name="Trial")
    res = await client.delete(f"/api/plans/{unsold['id']}", headers=owner.headers)
    assert res.status_code == 204

    sold = await make_plan(client, owner)
    await make_member(client, owner, membership={"plan_id": sold["id"]})
    res = await client.delete(f"/api/plans/{sold['id']}", headers=owner.headers)
    assert res.status_code == 409
    plan = (await client.get(f"/api/plans/{sold['id']}", headers=owner.headers)).json()
    assert plan["active_members"] == 1


async def test_only_managers_edit_plans(client: AsyncClient, owner: Account):
    trainer = await invite_and_accept(client, owner, "coach@a.com", "trainer")
    desk = await invite_and_accept(client, owner, "desk@a.com", "front_desk")
    plan = await make_plan(client, owner)
    for acct in (trainer, desk):
        assert (await client.get("/api/plans", headers=acct.headers)).status_code == 200
        res = await client.patch(
            f"/api/plans/{plan['id']}", json={"price": 1}, headers=acct.headers
        )
        assert res.status_code == 403
