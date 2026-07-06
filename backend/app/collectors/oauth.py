from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.logging import logger


class OAuthTokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any] | None:
        if not self._path.exists():
            return None
        import json
        data: dict[str, Any] = json.loads(self._path.read_text())
        return data

    def save(self, token: dict[str, Any]) -> None:
        import json
        self._path.write_text(json.dumps(token, indent=2, default=str))

    def is_expired(self, token: dict[str, Any]) -> bool:
        expires_at = token.get("expires_at")
        if expires_at is None:
            created = token.get("created_at")
            if created is None:
                return True
            expires_in = token.get("expires_in", 3600)
            expires_at_dt = (
                created
                if isinstance(created, datetime)
                else datetime.fromisoformat(created)
            )
            return datetime.now(UTC) > expires_at_dt + timedelta(seconds=expires_in - 60)
        expiry = (
            expires_at
            if isinstance(expires_at, datetime)
            else datetime.fromisoformat(expires_at)
        )
        return datetime.now(UTC) > expiry - timedelta(seconds=60)


class OAuth2Client:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        token_store: OAuthTokenStore,
        scopes: list[str] | None = None,
        redirect_uri: str = "http://localhost:8000/auth/callback",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._token_store = token_store
        self._scopes = scopes or []
        self._redirect_uri = redirect_uri

    def get_auth_url(self, auth_url: str, state: str) -> str:
        params: list[tuple[str, str | int | float | bool]] = [
            ("client_id", self._client_id),
            ("redirect_uri", self._redirect_uri),
            ("response_type", "code"),
            ("state", state),
        ]
        for s in self._scopes:
            params.append(("scope", s))
        qs = httpx.QueryParams(params)  # type: ignore[arg-type]
        return f"{auth_url}?{qs}"

    def exchange_code(self, code: str) -> dict[str, Any]:
        response = httpx.post(
            self._token_url,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self._redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        token: dict[str, Any] = response.json()
        token["created_at"] = datetime.now(UTC).isoformat()
        self._token_store.save(token)
        return token

    def refresh_token(self) -> dict[str, Any]:
        token = self._token_store.load()
        if token is None:
            raise RuntimeError("No token to refresh")
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("No refresh token available")
        logger.info("refreshing_token")
        response = httpx.post(
            self._token_url,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        new_token = {**token, **response.json()}
        new_token["created_at"] = datetime.now(UTC).isoformat()
        self._token_store.save(new_token)
        return new_token

    def get_access_token(self) -> str:
        token = self._token_store.load()
        if token is None:
            raise RuntimeError("No token available. Complete OAuth flow first.")
        if self._token_store.is_expired(token):
            token = self.refresh_token()
        return str(token["access_token"])

    def get_headers(self) -> dict[str, str]:
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
