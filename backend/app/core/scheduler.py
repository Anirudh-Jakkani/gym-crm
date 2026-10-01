"""In-process scheduler for local development / single-instance deployments.

Production should set SCHEDULER=celery and run `celery -A app.worker worker -B` instead.
Running both at once is still safe: every job is idempotent.
"""

import asyncio
import contextlib
import logging

from app.core.db import SessionLocal

log = logging.getLogger("gym_crm.scheduler")

INTERVAL_SECONDS = 15 * 60
STARTUP_DELAY_SECONDS = 20


async def _loop() -> None:
    from app.modules.reminders.service import run_all_gyms

    await asyncio.sleep(STARTUP_DELAY_SECONDS)
    while True:
        try:
            results = await run_all_gyms(SessionLocal)
            sent = sum(r.emailed for r in results.values())
            if sent:
                log.info("Reminder run: %d emails sent across %d gyms", sent, len(results))
        except Exception:
            log.exception("Scheduled reminder run failed")
        await asyncio.sleep(INTERVAL_SECONDS)


@contextlib.asynccontextmanager
async def run_scheduler():
    task = asyncio.create_task(_loop(), name="reminder-scheduler")
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
