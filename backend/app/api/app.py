from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import (
    analytics_router,
    auth_router,
    chat_router,
    insights_router,
    settings_router,
)
from app.logging import configure_logging, logger
from app.storage import Repository

configure_logging()


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator[None]:
    logger.info("starting_up")
    yield
    logger.info("shutting_down")


app = FastAPI(
    title="Conductor Observatory",
    version="0.1.0",
    description="Personal observability platform built on Conductor Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router)
app.include_router(insights_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(auth_router)


def get_repository() -> Repository:
    return Repository()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "ok",
            "version": "0.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@app.get("/timeline")
def get_timeline(
    limit: int = 200,
    repo: Repository = Depends(get_repository),  # noqa: B008
) -> JSONResponse:
    observations = repo.get_timeline(limit=limit)
    return JSONResponse(content=[obs.model_dump(mode="json") for obs in observations])


@app.get("/observations")
def get_observations(
    source: str | None = None,
    entity: str | None = None,
    limit: int = 100,
    offset: int = 0,
    repo: Repository = Depends(get_repository),  # noqa: B008
) -> JSONResponse:
    observations = repo.get_observations(
        source=source, entity=entity, limit=limit, offset=offset
    )
    return JSONResponse(content=[obs.model_dump(mode="json") for obs in observations])
