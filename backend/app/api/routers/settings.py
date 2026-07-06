from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.llm.client import PROVIDER_BASE_URLS, get_runtime_config, update_runtime_config
from app.logging import logger
from app.settings import INTEGRATION_DEFINITIONS, store

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


class IntegrationUpdate(BaseModel):
    values: dict[str, str] = {}


@router.get("/integrations")
def list_integrations() -> JSONResponse:
    runtime = store.get_all_integrations()
    result = []
    for definition in INTEGRATION_DEFINITIONS:
        source = definition.source
        runtime_vals = runtime.get(source, {})
        resolved = store.resolve(source, _field_map(source))
        result.append(
            {
                "source": source,
                "label": definition.label,
                "auth_type": definition.auth_type,
                "doc_url": definition.doc_url,
                "fields": [
                    {
                        "key": f.key,
                        "label": f.label,
                        "type": f.type,
                        "placeholder": f.placeholder,
                        "options": f.options,
                        "required": f.required,
                        "configured": bool(resolved.get(f.key)),
                    }
                    for f in definition.fields
                ],
                "oauth_scopes": definition.oauth_scopes or "",
                "connected": bool(runtime_vals.get("_token")),
            }
        )
    return JSONResponse(content={"integrations": result})


@router.put("/integrations/{source}")
def update_integration(source: str, body: IntegrationUpdate) -> JSONResponse:
    match = [d for d in INTEGRATION_DEFINITIONS if d.source == source]
    if not match:
        return JSONResponse(status_code=404, content={"error": "unknown_source"})
    store.set_integration(source, body.values)
    logger.info("integration_updated", source=source)
    return JSONResponse(content={"status": "ok", "source": source})


ENV_FIELD_MAP: dict[str, dict[str, str]] = {
    "weather": {
        "weather_api_key": "api_key",
        "weather_lat": "lat",
        "weather_lon": "lon",
        "weather_units": "units",
    },
    "hardcover": {"hardcover_api_key": "api_key"},
    "homeassistant": {"homeassistant_url": "url", "homeassistant_token": "token"},
    "google_health": {"google_client_id": "client_id", "google_client_secret": "client_secret"},
    "calendar": {"calendar_client_id": "client_id", "calendar_client_secret": "client_secret"},
    "spotify": {"spotify_client_id": "client_id", "spotify_client_secret": "client_secret"},
}


def _field_map(source: str) -> dict[str, str]:
    return ENV_FIELD_MAP.get(source, {})
