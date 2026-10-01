"""Unauthenticated endpoints. Everything here is reachable by anyone holding a link, so it
returns the minimum needed and never internal IDs, staff details or photos."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.ratelimit import RateLimiter
from app.modules.ai_plans.content import PlanContent
from app.modules.ai_plans.models import AIPlan, PlanStatus
from app.modules.auth.models import User
from app.modules.checkups.models import CheckUp
from app.modules.gyms.models import Gym
from app.modules.members.models import Member
from app.modules.members.service import days_left, gym_today
from app.modules.members.status import Status, membership_status, pick_current

router = APIRouter(prefix="/public", tags=["public"])

preview_limiter = RateLimiter(limit=60, window_seconds=60)


class PublicGym(BaseModel):
    name: str
    brand_color: str
    logo_url: str | None
    phone: str | None


class PublicMembership(BaseModel):
    plan_name: str
    status: Status
    start_date: date
    end_date: date
    days_left: int | None
    frozen_until: date | None
    renewal_starts: date | None


class Point(BaseModel):
    date: date
    value: float


class PublicProgress(BaseModel):
    checkups: int
    latest_date: date
    weight_kg: float | None
    body_fat_pct: float | None
    bmi: float | None
    waist_cm: float | None
    weight_change_kg: float | None  # since the first check-up
    first_date: date
    weight_series: list[Point]


class PublicMemberPage(BaseModel):
    gym: PublicGym
    member_name: str
    first_name: str
    trainer_name: str | None
    membership: PublicMembership | None
    plan: PlanContent | None
    plan_updated_at: datetime | None
    progress: PublicProgress | None


NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "This link isn't valid anymore")


@router.get(
    "/members/{token}",
    response_model=PublicMemberPage,
    dependencies=[Depends(preview_limiter)],
)
async def member_page(token: str, response: Response, db: DbSession):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Referrer-Policy"] = "no-referrer"
    if len(token) < 20:
        raise NOT_FOUND
    member = await db.scalar(
        select(Member)
        .where(Member.preview_token == token)
        .options(selectinload(Member.memberships))
    )
    # Disabled links look exactly like unknown ones.
    if member is None or not member.preview_enabled:
        raise NOT_FOUND

    gym = await db.get_one(Gym, member.gym_id)
    today = await gym_today(db, gym.id)

    current = pick_current(member.memberships, today)
    membership = None
    if current:
        renewal = min(
            (
                m.start_date
                for m in member.memberships
                if m.cancelled_at is None and m.start_date > current.end_date
            ),
            default=None,
        )
        state = membership_status(current, today)
        membership = PublicMembership(
            plan_name=current.plan_name,
            status=state,
            start_date=current.start_date,
            end_date=current.end_date,
            days_left=days_left(current, today),
            frozen_until=current.freeze_end if state == Status.FROZEN else None,
            renewal_starts=renewal,
        )

    plan = await db.scalar(
        select(AIPlan).where(AIPlan.member_id == member.id, AIPlan.status == PlanStatus.PUBLISHED)
    )
    trainer_name = (
        await db.scalar(select(User.name).where(User.id == member.trainer_id))
        if member.trainer_id
        else None
    )

    checkups = (
        await db.scalars(
            select(CheckUp).where(CheckUp.member_id == member.id).order_by(CheckUp.recorded_on)
        )
    ).all()
    progress = None
    if checkups:
        first, last = checkups[0], checkups[-1]
        weights = [c for c in checkups if c.weight_kg is not None]
        progress = PublicProgress(
            checkups=len(checkups),
            latest_date=last.recorded_on,
            weight_kg=last.weight_kg,
            body_fat_pct=last.body_fat_pct,
            bmi=last.bmi,
            waist_cm=last.waist_cm,
            weight_change_kg=round(weights[-1].weight_kg - weights[0].weight_kg, 1)
            if len(weights) > 1
            else None,
            first_date=first.recorded_on,
            weight_series=[Point(date=c.recorded_on, value=c.weight_kg) for c in weights],
        )

    return PublicMemberPage(
        gym=PublicGym(
            name=gym.name, brand_color=gym.brand_color, logo_url=gym.logo_url, phone=gym.phone
        ),
        member_name=member.name,
        first_name=member.name.split()[0],
        trainer_name=trainer_name,
        membership=membership,
        plan=PlanContent.model_validate(plan.content) if plan and plan.content else None,
        plan_updated_at=(plan.updated_at if plan else None),
        progress=progress,
    )
