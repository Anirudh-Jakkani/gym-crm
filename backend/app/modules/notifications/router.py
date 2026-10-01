import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, update

from app.core.db import utcnow
from app.core.deps import CurrentContext, DbSession
from app.core.schemas import ORMModel
from app.modules.notifications.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(ORMModel):
    id: uuid.UUID
    kind: str
    title: str
    body: str | None
    link: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread: int


def _mine(ctx: CurrentContext):
    return (Notification.gym_id == ctx.gym_id, Notification.user_id == ctx.user.id)


@router.get("", response_model=NotificationList)
async def list_notifications(ctx: CurrentContext, db: DbSession, limit: int = 20):
    items = (
        await db.scalars(
            select(Notification)
            .where(*_mine(ctx))
            .order_by(Notification.created_at.desc())
            .limit(min(max(limit, 1), 50))
        )
    ).all()
    unread = await db.scalar(
        select(func.count()).where(*_mine(ctx), Notification.read_at.is_(None))
    )
    return NotificationList(items=items, unread=unread or 0)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notification_id: uuid.UUID, ctx: CurrentContext, db: DbSession) -> None:
    n = await db.scalar(select(Notification).where(*_mine(ctx), Notification.id == notification_id))
    if n is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    n.read_at = n.read_at or utcnow()
    await db.commit()


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(ctx: CurrentContext, db: DbSession) -> None:
    await db.execute(
        update(Notification)
        .where(*_mine(ctx), Notification.read_at.is_(None))
        .values(read_at=utcnow())
    )
    await db.commit()
