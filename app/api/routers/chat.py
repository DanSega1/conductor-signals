from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.llm import LLMClient
from app.logging import logger
from app.storage import Repository

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def get_repo() -> Repository:
    return Repository()


def get_llm() -> LLMClient:
    return LLMClient()


@router.post("")
def chat(
    body: ChatRequest,
    repo: Repository = Depends(get_repo),  # noqa: B008
    llm: LLMClient = Depends(get_llm),  # noqa: B008
) -> JSONResponse:
    observations = repo.get_timeline(limit=30)
    insights = repo.get_insights(limit=10)

    obs_block = "\n".join(
        f"  [{o.timestamp}] {o.source}/{o.entity}: {o.features}"
        for o in observations
    ) if observations else "  (none)"

    ins_block = "\n".join(
        f"  [{i.timestamp}] {i.title}: {i.description} (confidence={i.confidence})"
        for i in insights
    ) if insights else "  (none)"

    system = (
        "You are Conductor Observatory, a personal life observability assistant. "
        "You answer questions about someone's personal data (health, reading, music, "
        "weather, calendar events, home status). Use the provided context to answer "
        "factually. If the context doesn't contain the answer, say so. Be concise "
        "and helpful."
    )

    user = (
        f"Here is the recent context from my observability platform:\n\n"
        f"## Recent Observations\n{obs_block}\n\n"
        f"## Recent Insights\n{ins_block}\n\n"
        f"## My Question\n{body.message}"
    )

    logger.info("chat_request", message_length=len(body.message))
    response = llm.complete(system_prompt=system, user_prompt=user)
    logger.info("chat_response", response_length=len(response))

    return JSONResponse(content={"response": response})
