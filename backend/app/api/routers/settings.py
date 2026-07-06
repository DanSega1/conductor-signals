from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.llm.client import PROVIDER_BASE_URLS, get_runtime_config, update_runtime_config
from app.logging import logger

router = APIRouter(prefix="/settings", tags=["settings"])


class LLMSettingsRequest(BaseModel):
    provider: str = "openrouter"
    api_key: str = ""
    model: str = ""
    base_url: str = ""


@router.get("/llm")
def get_llm_settings() -> JSONResponse:
    config = get_runtime_config()
    return JSONResponse(
        content={
            "provider": config.get("provider", "openrouter"),
            "api_key": "••••••••" if config.get("api_key") else "",
            "model": config.get("model", ""),
            "base_url": config.get("base_url", ""),
            "available_providers": list(PROVIDER_BASE_URLS.keys()),
        }
    )


@router.put("/llm")
def set_llm_settings(body: LLMSettingsRequest) -> JSONResponse:
    from app.llm.client import PROVIDER_BASE_URLS

    provider = body.provider
    base_url = body.base_url or PROVIDER_BASE_URLS.get(provider, "")  # type: ignore[call-overload]
    model = body.model

    update_runtime_config(
        provider=provider,
        api_key=body.api_key,
        model=model,
        base_url=base_url,
    )

    logger.info("llm_settings_updated", provider=provider, model=model)

    return JSONResponse(
        content={
            "status": "ok",
            "provider": provider,
            "model": model,
            "base_url": base_url,
        }
    )
