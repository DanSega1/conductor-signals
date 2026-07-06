from __future__ import annotations

import urllib.parse
from pathlib import Path

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.collectors.oauth import OAuth2Client, OAuthTokenStore
from app.config import settings
from app.logging import logger
from app.settings import store

router = APIRouter(prefix="/auth", tags=["auth"])

PROVIDERS: dict[str, dict[str, str]] = {
    "google_health": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "client_id_attr": "google_client_id",
        "client_secret_attr": "google_client_secret",
        "scopes": (
            "https://www.googleapis.com/auth/fitness.activity.read"
            " https://www.googleapis.com/auth/fitness.body.read"
            " https://www.googleapis.com/auth/fitness.heart_rate.read"
            " https://www.googleapis.com/auth/fitness.sleep.read"
        ),
    },
    "calendar": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "client_id_attr": "calendar_client_id",
        "client_secret_attr": "calendar_client_secret",
        "scopes": "https://www.googleapis.com/auth/calendar.events.readonly",
    },
    "spotify": {
        "auth_url": "https://accounts.spotify.com/authorize",
        "token_url": "https://accounts.spotify.com/api/token",
        "client_id_attr": "spotify_client_id",
        "client_secret_attr": "spotify_client_secret",
        "scopes": "user-read-recently-played user-read-currently-playing",
    },
}

FRONTEND_URL = "http://localhost:5173"


def _get_credential(provider_key: str, attr_name: str) -> str:
    info = PROVIDERS[provider_key]
    env_attr = info[attr_name]
    env_val = getattr(settings, env_attr, None) or ""
    if env_val:
        return str(env_val)
    runtime = store.get_integration(provider_key)
    if attr_name == "client_id_attr":
        return runtime.get("client_id", "")
    return runtime.get("client_secret", "")


def _get_token_store(provider_key: str) -> OAuthTokenStore:
    data_dir = Path(settings.data_dir)
    return OAuthTokenStore(data_dir / "tokens" / f"{provider_key}.json")


@router.get("/status")
def auth_status() -> JSONResponse:
    statuses: dict[str, bool] = {}
    for provider_key in PROVIDERS:
        store = _get_token_store(provider_key)
        token = store.load()
        statuses[provider_key] = token is not None and not store.is_expired(token)
    return JSONResponse(content={"providers": statuses})


@router.get("/{provider}/login", response_model=None)
def auth_login(provider: str, request: Request) -> RedirectResponse | JSONResponse:
    if provider not in PROVIDERS:
        return JSONResponse(status_code=404, content={"error": "unknown_provider"})

    info = PROVIDERS[provider]
    client_id = _get_credential(provider, "client_id_attr")
    if not client_id:
        return JSONResponse(
            status_code=400,
            content={"error": f"{provider} client_id not configured"},
        )

    callback_url = str(request.base_url).rstrip("/") + f"/auth/{provider}/callback"
    scope_str = info["scopes"]

    params = (
        f"client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(callback_url)}"
        f"&scope={urllib.parse.quote(scope_str)}"
        f"&response_type=code"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    redirect_url = f"{info['auth_url']}?{params}"
    logger.info("oauth_redirect", provider=provider)
    return RedirectResponse(url=redirect_url)


@router.get("/{provider}/callback", response_model=None)
def auth_callback(
    provider: str,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse | JSONResponse:
    if provider not in PROVIDERS:
        return JSONResponse(status_code=404, content={"error": "unknown_provider"})

    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?auth={provider}&status=error&reason={error}"
        )

    if not code:
        return JSONResponse(status_code=400, content={"error": "missing_code"})

    info = PROVIDERS[provider]
    client_id = _get_credential(provider, "client_id_attr")
    client_secret = _get_credential(provider, "client_secret_attr")
    if not client_id or not client_secret:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?auth={provider}&status=error&reason=not_configured"
        )

    token_store = _get_token_store(provider)
    oauth = OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        token_url=info["token_url"],
        token_store=token_store,
    )

    oauth.exchange_code(code)

    store.set_integration(provider, {"_token": "true"})

    return RedirectResponse(
        url=f"{FRONTEND_URL}/settings?auth={provider}&status=success"
    )
