import contextlib

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers all tables)
from app.core.config import settings
from app.core.scheduler import run_scheduler
from app.modules.ai_plans.router import router as ai_plans_router
from app.modules.auth.router import router as auth_router
from app.modules.checkups.router import router as checkups_router
from app.modules.finance.router import router as finance_router
from app.modules.gyms.router import router as gyms_router
from app.modules.leads.router import router as leads_router
from app.modules.members.router import router as members_router
from app.modules.notifications.router import router as notifications_router
from app.modules.plans.router import router as plans_router
from app.modules.public.router import router as public_router
from app.modules.reminders.router import router as reminders_router


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.scheduler == "inprocess":
        async with run_scheduler():
            yield
    else:
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api")

    @api.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(auth_router)
    api.include_router(gyms_router)
    api.include_router(plans_router)
    api.include_router(members_router)
    api.include_router(checkups_router)
    api.include_router(ai_plans_router)
    api.include_router(leads_router)
    api.include_router(finance_router)
    api.include_router(public_router)
    api.include_router(reminders_router)
    api.include_router(notifications_router)
    app.include_router(api)
    return app


app = create_app()
