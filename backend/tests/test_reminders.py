from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core.email import Email, EmailError
from app.modules.reminders.service import run_all_gyms
from app.modules.reminders.templates import render
from tests.conftest import Account
from tests.helpers import days, make_member, make_plan, today
from tests.test_gym_and_staff import invite_and_accept


class FakeSender:
    def __init__(self):
        self.sent: list[Email] = []
        self.fail = False

    async def send(self, email: Email) -> None:
        if self.fail:
            raise EmailError("SMTP said no")
        self.sent.append(email)


@pytest.fixture
def outbox(monkeypatch) -> FakeSender:
    sender = FakeSender()
    monkeypatch.setattr("app.core.email.get_sender", lambda: sender)
    return sender


async def member_ending_in(
    client: AsyncClient, acct: Account, plan: dict, n: int, phone: str, email: str | None, name: str
) -> dict:
    """Member whose 10-day membership ends `n` days from today."""
    return await make_member(
        client,
        acct,
        name=name,
        phone=phone,
        email=email,
        membership={"plan_id": plan["id"], "start_date": days(n - 9)},
    )


@pytest.fixture
async def scenario(client: AsyncClient, owner: Account) -> dict:
    """Default offsets are 7, 3, 1, 0, -3."""
    plan = await make_plan(client, owner, name="10 days", duration_value=10, duration_unit="day")
    ending = lambda *a: member_ending_in(client, owner, plan, *a)  # noqa: E731
    m = {
        "in7": await ending(7, "9000000001", "a@x.com", "Anil Seven"),
        "in3_no_email": await ending(3, "9000000002", None, "Bina Three"),
        "today": await ending(0, "9000000003", "c@x.com", "Chetan Today"),
        "ago3": await ending(-3, "9000000004", "d@x.com", "Divya Expired"),
        "in5": await ending(5, "9000000005", "e@x.com", "Esha Five"),  # not an offset
        "renewed": await ending(7, "9000000006", "f@x.com", "Farhan Renewed"),
        "cancelled": await ending(7, "9000000007", "g@x.com", "Gita Cancelled"),
    }
    await client.post(
        f"/api/members/{m['renewed']['id']}/memberships",
        json={"plan_id": plan["id"]},
        headers=owner.headers,
    )
    await client.post(
        f"/api/memberships/{m['cancelled']['memberships'][0]['id']}/cancel",
        headers=owner.headers,
    )
    return m


async def test_due_list(client: AsyncClient, owner: Account, scenario):
    res = await client.get("/api/reminders/due", headers=owner.headers)
    assert res.status_code == 200
    body = res.json()
    assert body["day"] == today().isoformat()
    by_name = {i["member_name"]: i for i in body["items"]}
    assert set(by_name) == {"Anil Seven", "Bina Three", "Chetan Today", "Divya Expired"}

    anil = by_name["Anil Seven"]
    assert anil["offset_days"] == 7 and anil["kind"] == "before"
    assert anil["subject"] == "Your Gym A membership ends in 7 days"
    assert anil["body"].startswith("Hi Anil,")
    assert anil["email_status"] is None
    assert by_name["Chetan Today"]["kind"] == "on_day"
    assert by_name["Divya Expired"]["kind"] == "after"

    # Looking ahead: tomorrow, Bina's membership is 2 days out (not an offset).
    tomorrow = await client.get(f"/api/reminders/due?day={days(1)}", headers=owner.headers)
    names = {i["member_name"] for i in tomorrow.json()["items"]}
    assert "Bina Three" not in names and "Esha Five" not in names


async def test_run_sends_emails_once(client: AsyncClient, owner: Account, scenario, outbox):
    res = await client.post("/api/reminders/run", headers=owner.headers)
    assert res.json() == {"due": 4, "emailed": 3, "failed": 0, "no_email": 1, "already_sent": 0}
    assert sorted(e.to for e in outbox.sent) == ["a@x.com", "c@x.com", "d@x.com"]
    assert all(e.from_name == "Gym A" for e in outbox.sent)

    again = await client.post("/api/reminders/run", headers=owner.headers)
    assert again.json()["emailed"] == 0 and again.json()["already_sent"] == 3
    assert len(outbox.sent) == 3

    due = (await client.get("/api/reminders/due", headers=owner.headers)).json()["items"]
    statuses = {i["member_name"]: i["email_status"] for i in due}
    assert statuses == {
        "Anil Seven": "sent",
        "Bina Three": None,
        "Chetan Today": "sent",
        "Divya Expired": "sent",
    }
    history = (await client.get("/api/reminders/history", headers=owner.headers)).json()
    assert {h["sent_by_name"] for h in history["items"]} == {"Owner"}  # manual run


async def test_failed_email_is_logged_and_retried(
    client: AsyncClient, owner: Account, scenario, outbox
):
    outbox.fail = True
    res = (await client.post("/api/reminders/run", headers=owner.headers)).json()
    assert res["failed"] == 3 and res["emailed"] == 0
    due = (await client.get("/api/reminders/due", headers=owner.headers)).json()["items"]
    anil = next(i for i in due if i["member_name"] == "Anil Seven")
    assert anil["email_status"] == "failed" and "SMTP said no" in anil["email_error"]

    outbox.fail = False
    res = (await client.post("/api/reminders/run", headers=owner.headers)).json()
    assert res["emailed"] == 3 and res["failed"] == 0


async def test_scheduler_respects_send_hour_and_enabled_flag(
    client: AsyncClient, owner: Account, scenario, outbox, sessions
):
    # Gym is in Asia/Kolkata (UTC+5:30) and sends from 09:00 local.
    local_day = today()
    early = datetime(local_day.year, local_day.month, local_day.day, 2, 0, tzinfo=UTC)  # 07:30 IST
    late = early + timedelta(hours=3)  # 10:30 IST

    assert await run_all_gyms(sessions, now=early) == {}
    assert outbox.sent == []

    results = await run_all_gyms(sessions, now=late)
    assert [r.emailed for r in results.values()] == [3]
    history = (await client.get("/api/reminders/history", headers=owner.headers)).json()
    assert {h["sent_by_name"] for h in history["items"]} == {None}  # automatic

    await client.patch("/api/reminders/settings", json={"enabled": False}, headers=owner.headers)
    assert await run_all_gyms(sessions, now=late) == {}


async def test_whatsapp_logging_and_history(client: AsyncClient, owner: Account, scenario):
    bina = scenario["in3_no_email"]
    ms_id = bina["memberships"][0]["id"]
    res = await client.post(
        "/api/reminders/whatsapp",
        json={"membership_id": ms_id, "offset_days": 3},
        headers=owner.headers,
    )
    assert res.status_code == 204
    # Logging twice updates the same entry.
    await client.post(
        "/api/reminders/whatsapp",
        json={"membership_id": ms_id, "offset_days": 3},
        headers=owner.headers,
    )
    due = (await client.get("/api/reminders/due", headers=owner.headers)).json()["items"]
    assert next(i for i in due if i["member_name"] == "Bina Three")["whatsapp_sent_at"]

    history = (await client.get("/api/reminders/history", headers=owner.headers)).json()
    assert history["total"] == 1
    entry = history["items"][0]
    assert entry["channel"] == "whatsapp" and entry["sent_by_name"] == "Owner"
    assert entry["member_name"] == "Bina Three" and entry["recipient"] == "9000000002"


async def test_digest_notification(client: AsyncClient, owner: Account, scenario, outbox):
    trainer = await invite_and_accept(client, owner, "coach@a.com", "trainer")
    await client.post("/api/reminders/run", headers=owner.headers)
    await client.post("/api/reminders/run", headers=owner.headers)  # no duplicate digest

    notes = (await client.get("/api/notifications", headers=owner.headers)).json()
    assert notes["unread"] == 1
    (note,) = notes["items"]
    assert note["title"] == "4 membership reminders today"
    assert "3 emailed automatically" in note["body"]
    assert "1 without email" in note["body"]
    assert note["link"] == "/reminders"

    assert (await client.get("/api/notifications", headers=trainer.headers)).json()["unread"] == 0

    await client.post("/api/notifications/read-all", headers=owner.headers)
    assert (await client.get("/api/notifications", headers=owner.headers)).json()["unread"] == 0


async def test_settings_and_custom_templates(client: AsyncClient, owner: Account, scenario):
    s = (await client.get("/api/reminders/settings", headers=owner.headers)).json()
    assert s["enabled"] is True and s["hour"] == 9 and s["offsets"] == [7, 3, 1, 0, -3]
    assert s["customized"] == [] and "first_name" in s["placeholders"]

    custom = {"subject": "Renew {plan_name}!", "body": "Hey {first_name}, {days} days to go."}
    res = await client.patch(
        "/api/reminders/settings",
        json={"templates": {"before": custom}, "offsets": [7, 7, 30], "hour": 18},
        headers=owner.headers,
    )
    s = res.json()
    assert s["customized"] == ["before"] and s["offsets"] == [30, 7] and s["hour"] == 18

    due = (await client.get("/api/reminders/due", headers=owner.headers)).json()["items"]
    anil = next(i for i in due if i["member_name"] == "Anil Seven")
    assert anil["subject"] == "Renew 10 days!" and anil["body"] == "Hey Anil, 7 days to go."
    assert {i["member_name"] for i in due} == {"Anil Seven"}  # only the 7-day offset is left

    preview = await client.post(
        "/api/reminders/preview", json={"kind": "after", "template": custom}, headers=owner.headers
    )
    assert preview.json()["body"] == "Hey Priya, 3 days to go."

    s = (
        await client.patch(
            "/api/reminders/settings", json={"templates": {"before": None}}, headers=owner.headers
        )
    ).json()
    assert s["customized"] == []


async def test_only_owner_changes_settings(client: AsyncClient, owner: Account):
    manager = await invite_and_accept(client, owner, "mgr@a.com", "manager")
    trainer = await invite_and_accept(client, owner, "coach@a.com", "trainer")
    res = await client.patch("/api/reminders/settings", json={"hour": 7}, headers=manager.headers)
    assert res.status_code == 403
    assert (await client.post("/api/reminders/run", headers=trainer.headers)).status_code == 403
    assert (await client.get("/api/reminders/due", headers=trainer.headers)).status_code == 403
    assert (await client.post("/api/reminders/run", headers=manager.headers)).status_code == 200


def test_render_leaves_unknown_and_unsafe_placeholders():
    out = render("Hi {first_name} {unknown} {first_name.__class__}", {"first_name": "Asha"})
    assert out == "Hi Asha {unknown} {first_name.__class__}"


async def test_reminders_are_isolated(
    client: AsyncClient, owner: Account, other_owner: Account, scenario, outbox
):
    h = other_owner.headers
    assert (await client.get("/api/reminders/due", headers=h)).json()["items"] == []
    res = await client.post(
        "/api/reminders/whatsapp",
        json={"membership_id": scenario["in7"]["memberships"][0]["id"], "offset_days": 7},
        headers=h,
    )
    assert res.status_code == 404
    assert (await client.post("/api/reminders/run", headers=h)).json()["due"] == 0
    assert outbox.sent == []
    await client.post("/api/reminders/run", headers=owner.headers)
    assert (await client.get("/api/reminders/history", headers=h)).json()["total"] == 0
    assert (await client.get("/api/notifications", headers=h)).json()["items"] == []
