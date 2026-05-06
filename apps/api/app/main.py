import contextlib
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.middleware.request_id import RequestIdMiddleware
from app.routers import (
    admin,
    contributors,
    health,
    logs,
    planters,
    scores,
    search,
    seed_types,
    stats,
    tags,
    users,
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="Works Logue API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Registered AFTER CORS so it sits OUTER on FastAPI's LIFO stack: every request
# (including CORS preflight) gets a request_id bound to structlog contextvars.
app.add_middleware(RequestIdMiddleware)

app.include_router(health.router)
app.include_router(users.router, prefix="/api/v1")
app.include_router(planters.router, prefix="/api/v1")
app.include_router(seed_types.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(contributors.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
