from __future__ import annotations

import json

import polars as pl
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.analytics.engine import AnalyticsEngine
from app.storage import Repository

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_repo() -> Repository:
    return Repository()


def get_engine(
    repo: Repository = Depends(get_repo),  # noqa: B008
) -> AnalyticsEngine:
    return AnalyticsEngine(repo)


def _try_parse(val: object) -> object:
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            return val
    return val


def _df_response(df: pl.DataFrame) -> JSONResponse:
    rows = [{k: _try_parse(v) for k, v in row.items()} for row in df.to_dicts()]
    return JSONResponse(content=json.loads(json.dumps(rows, default=str)))


@router.get("/comparison")
def period_comparison(
    entity: str,
    days: int = 7,
    engine: AnalyticsEngine = Depends(get_engine),  # noqa: B008
) -> JSONResponse:
    return _df_response(engine.period_comparison(entity, days))


@router.get("/year-over-year")
def year_over_year(
    entity: str,
    feature: str,
    engine: AnalyticsEngine = Depends(get_engine),  # noqa: B008
) -> JSONResponse:
    return _df_response(engine.year_over_year(entity, feature))


@router.get("/recurring")
def recurring_patterns(
    entity: str,
    feature: str,
    engine: AnalyticsEngine = Depends(get_engine),  # noqa: B008
) -> JSONResponse:
    return _df_response(engine.recurring_patterns(entity, feature))


@router.get("/recent")
def recent_observations(
    limit: int = 50,
    engine: AnalyticsEngine = Depends(get_engine),  # noqa: B008
) -> JSONResponse:
    return _df_response(engine.recent_observations(limit))
