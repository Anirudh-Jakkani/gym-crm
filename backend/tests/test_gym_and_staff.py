from httpx import AsyncClient

from tests.conftest import Account


async def test_update_gym_settings(client: AsyncClient, owner: Account):
    res = await client.patch(
        "/api/gym",
        json={"brand_color": "#ff0000", "reminder_offsets": [1, 7, 7, -2]},
        headers=owner.headers,
    )
    assert res.status_code == 200
    assert res.json()["brand_color"] == "#ff0000"
    assert res.json()["reminder_offsets"] == [7, 1, -2]


async def test_branch_crud_and_last_branch_guard(client: AsyncClient, owner: Account):
    h = owner.headers
    main = (await client.get("/api/branches", headers=h)).json()[0]
    assert (await client.delete(f"/api/branches/{main['id']}", headers=h)).status_code == 409

    created = await client.post("/api/branches", json={"name": "Downtown"}, headers=h)
    assert created.status_code == 201
    bid = created.json()["id"]
    patched = await client.patch(f"/api/branches/{bid}", json={"address": "MG Road"}, headers=h)
    assert patched.json()["address"] == "MG Road"
    assert (await client.delete(f"/api/branches/{bid}", headers=h)).status_code == 204


async def invite_and_accept(client: AsyncClient, owner: Account, email: str, role: str) -> Account:
    inv = await client.post(
        "/api/invites", json={"email": email, "role": role}, headers=owner.headers
    )
    assert inv.status_code == 201, inv.text
    token = inv.json()["url"].rsplit("/", 1)[-1]

    preview = await client.get(f"/api/auth/invites/{token}")
    assert preview.json()["role"] == role

    accepted = await client.post(
        f"/api/auth/invites/{token}/accept", json={"name": "Staff", "password": "staffpass1"}
    )
    assert accepted.status_code == 200, accepted.text
    client.cookies.clear()
    data = accepted.json()
    assert data["gym"]["id"] == owner.gym_id
    # Invite links are single-use.
    assert (await client.get(f"/api/auth/invites/{token}")).status_code == 404
    return Account(token=data["access_token"], gym_id=data["gym"]["id"], user_id=data["user"]["id"])


async def test_invite_flow_and_roles(client: AsyncClient, owner: Account):
    trainer = await invite_and_accept(client, owner, "coach@a.com", "trainer")

    staff = (await client.get("/api/staff", headers=owner.headers)).json()
    assert {s["role"] for s in staff} == {"owner", "trainer"}

    # Trainers can read but not manage.
    assert (await client.get("/api/branches", headers=trainer.headers)).status_code == 200
    res = await client.post("/api/branches", json={"name": "X"}, headers=trainer.headers)
    assert res.status_code == 403
    res = await client.patch("/api/gym", json={"name": "Hacked"}, headers=trainer.headers)
    assert res.status_code == 403

    # Re-inviting existing staff is rejected.
    res = await client.post(
        "/api/invites", json={"email": "coach@a.com", "role": "manager"}, headers=owner.headers
    )
    assert res.status_code == 409


async def test_role_change_applies_immediately(client: AsyncClient, owner: Account):
    manager = await invite_and_accept(client, owner, "mgr@a.com", "manager")
    assert (
        await client.post("/api/branches", json={"name": "B2"}, headers=manager.headers)
    ).status_code == 201

    staff = (await client.get("/api/staff", headers=owner.headers)).json()
    mgr_id = next(s["id"] for s in staff if s["email"] == "mgr@a.com")
    await client.patch(f"/api/staff/{mgr_id}", json={"role": "front_desk"}, headers=owner.headers)
    # Same token, but the role now comes from the database.
    assert (
        await client.post("/api/branches", json={"name": "B3"}, headers=manager.headers)
    ).status_code == 403

    await client.delete(f"/api/staff/{mgr_id}", headers=owner.headers)
    assert (await client.get("/api/gym", headers=manager.headers)).status_code == 401


async def test_manager_cannot_invite_owner(client: AsyncClient, owner: Account):
    manager = await invite_and_accept(client, owner, "mgr@a.com", "manager")
    res = await client.post(
        "/api/invites", json={"email": "x@a.com", "role": "owner"}, headers=manager.headers
    )
    assert res.status_code == 403


async def test_last_owner_cannot_be_demoted(client: AsyncClient, owner: Account):
    staff = (await client.get("/api/staff", headers=owner.headers)).json()
    res = await client.patch(
        f"/api/staff/{staff[0]['id']}", json={"role": "manager"}, headers=owner.headers
    )
    assert res.status_code == 409
