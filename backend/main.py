import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db_bootstrap import bootstrap_on_startup
from app.ingestion.scheduler import start_scheduler, stop_scheduler

from app.api.auth import (
    router as auth_router,
)

from app.api.overview import (
    router as business_router,
)

from app.api.agriculture import (
    router as agriculture_router,
)

from app.api.global_exposure import (
    router as global_exposure_router,
)

from app.api.global_events import (
    router as global_events_router,
)

from app.api.market import (
    router as market_router,
)

from app.api.routes import (
    router as routes_router,
)

from app.api.demo import (
    router as demo_router,
)

from app.api.copilot import (
    router as copilot_router,
)

from app.api.approvals import (
    router as approvals_router,
)

from app.api.agents import (
    router as agents_router,
)

from app.api.connections import (
    router as connections_router,
    readiness_router,
)

from app.api.shipments import (
    router as shipments_router,
)

from app.api.webhooks import (
    router as webhooks_router,
)

from app.api.merge import (
    router as merge_router,
)

from app.api.intelligence import (
    router as intelligence_router,
)

from app.api.scenarios import (
    router as scenarios_router,
)

from app.api.audit import (
    router as audit_router,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_on_startup()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(
    title="HEX Business AI",
    version="0.1.0",
    lifespan=lifespan,
)


# FRONTEND_URL may be a comma-separated list of exact origins.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
for raw in os.getenv("FRONTEND_URL", "").split(","):
    origin = raw.strip().rstrip("/")
    if origin and origin not in allowed_origins:
        allowed_origins.append(origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Vercel preview deployments: https://<project>-<hash>-<scope>.vercel.app
    allow_origin_regex=os.getenv(
        "FRONTEND_ORIGIN_REGEX",
        r"https://.*\.vercel\.app",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Referrer-Policy", "strict-origin-when-cross-origin"
    )
    return response


app.include_router(
    auth_router
)

app.include_router(
    business_router
)

app.include_router(
    agriculture_router
)

app.include_router(
    global_exposure_router
)

app.include_router(
    global_events_router
)

app.include_router(
    market_router
)

app.include_router(
    routes_router
)

app.include_router(
    demo_router
)

app.include_router(
    copilot_router
)

app.include_router(
    approvals_router
)

app.include_router(
    agents_router
)

app.include_router(
    connections_router
)

app.include_router(
    readiness_router
)

app.include_router(
    shipments_router
)

app.include_router(
    webhooks_router
)

app.include_router(
    merge_router
)

app.include_router(
    intelligence_router
)

app.include_router(
    scenarios_router
)

app.include_router(
    audit_router
)

@app.get("/")
def root():
    return {
        "message":
            "HEX Business AI backend is running"
    }


@app.get("/health")
def health():
    """Liveness + config sanity for the deploy platform's health check."""

    from app.config import missing_settings

    missing = missing_settings()
    return {
        "status": "ok" if not missing else "degraded",
        "missing_settings": missing,
    }