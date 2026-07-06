from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.insights.generator import InsightGenerator
from app.llm import LLMClient
from app.storage import Repository

router = APIRouter(prefix="/insights", tags=["insights"])


def get_repo() -> Repository:
    return Repository()


def get_generator(
    repo: Repository = Depends(get_repo),  # noqa: B008
) -> InsightGenerator:
    return InsightGenerator(repository=repo, llm_client=LLMClient())


@router.get("")
def list_insights(
    limit: int = 50,
    offset: int = 0,
    repo: Repository = Depends(get_repo),  # noqa: B008
) -> JSONResponse:
    insights = repo.get_insights(limit=limit, offset=offset)
    return JSONResponse(content=[i.model_dump(mode="json") for i in insights])


@router.post("/generate")
def generate_insights(
    generator: InsightGenerator = Depends(get_generator),  # noqa: B008
) -> JSONResponse:
    count = generator.generate_and_store()
    return JSONResponse(content={"generated": count})
