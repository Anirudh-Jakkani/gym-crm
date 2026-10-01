from httpx import AsyncClient

from tests.conftest import Account


async def test_signup_creates_gym_branch_and_owner(client: AsyncClient):
    res = await client.post(
        "/api/auth/signup",
        json={
            "name": "Asha",
            "email": "Asha@Example.com",
            "password": "supersecret1",
            "gym_name": "Flex Fitness",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "asha@example.com"
    assert body["gym"]["name"] == "Flex Fitness"
    assert body["role"] == "owner"
    assert body["gym"]["reminder_offsets"] == [7, 3, 1, 0, -3]
    assert "access_token" in res.cookies

    branches = await client.get("/api/branches")  # authenticated through the cookie
    assert [b["name"] for b in branches.json()] == ["Main branch"]


async def test_duplicate_signup_rejected(client: AsyncClient, owner: Account):
    res = await client.post(
        "/api/auth/signup",
        json={
            "name": "Xavi",
            "email": "owner@a.com",
            "password": "supersecret1",
            "gym_name": "Dup",
        },
    )
    assert res.status_code == 409


async def test_login_wrong_password(client: AsyncClient, owner: Account):
    res = await client.post(
        "/api/auth/login", json={"email": "owner@a.com", "password": "nope1234"}
    )
    assert res.status_code == 401
    res = await client.post(
        "/api/auth/login", json={"email": "ghost@a.com", "password": "nope1234"}
    )
    assert res.status_code == 401


async def test_login_me_refresh_logout(client: AsyncClient, owner: Account):
    res = await client.post(
        "/api/auth/login", json={"email": "OWNER@a.com", "password": "supersecret1"}
    )
    assert res.status_code == 200
    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["gym"]["id"] == owner.gym_id

    refreshed = await client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_requires_auth(client: AsyncClient):
    assert (await client.get("/api/gym")).status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await client.get("/api/gym", headers=bad)).status_code == 401


async def test_refresh_token_cannot_be_used_as_access(client: AsyncClient, owner: Account):
    res = await client.post(
        "/api/auth/login", json={"email": "owner@a.com", "password": "supersecret1"}
    )
    refresh = res.json()["refresh_token"]
    client.cookies.clear()
    res = await client.get("/api/gym", headers={"Authorization": f"Bearer {refresh}"})
    assert res.status_code == 401


async def test_failed_refresh_clears_cookies(client: AsyncClient, owner: Account):
    client.cookies.set("refresh_token", "garbage")
    res = await client.post("/api/auth/refresh")
    assert res.status_code == 401
    cleared = [c for c in res.headers.get_list("set-cookie") if c.startswith("refresh_token=")]
    assert cleared and "Max-Age=0" in cleared[0]


async def test_refresh_after_removal_from_gym(client: AsyncClient, owner: Account):
    other = await client.post(
        "/api/auth/signup",
        json={"name": "Two", "email": "two@a.com", "password": "supersecret1", "gym_name": "G2"},
    )
    refresh = other.json()["refresh_token"]
    client.cookies.clear()
    # Token for a gym the caller isn't staff of -> session ends instead of erroring.
    import jwt as pyjwt

    from app.core.config import settings

    payload = pyjwt.decode(refresh, settings.jwt_secret, algorithms=["HS256"])
    payload["gym"] = owner.gym_id
    forged_scope = pyjwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    res = await client.post("/api/auth/refresh", json={"refresh_token": forged_scope})
    assert res.status_code == 401
