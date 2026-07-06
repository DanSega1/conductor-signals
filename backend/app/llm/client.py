from __future__ import annotations

from typing import Literal

import httpx

from app.config import settings
from app.logging import logger

Provider = Literal["openrouter", "openai", "anthropic", "ollama"]

PROVIDER_BASE_URLS: dict[Provider, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "ollama": "http://localhost:11434/v1",
}

DEFAULT_MODEL: dict[Provider, str] = {
    "openrouter": "gpt-4o-mini",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-haiku-20240307",
    "ollama": "llama3.2",
}

_RUNTIME_CONFIG: dict[str, str] = {}


def update_runtime_config(provider: str, api_key: str, model: str, base_url: str) -> None:
    _RUNTIME_CONFIG["provider"] = provider
    _RUNTIME_CONFIG["api_key"] = api_key
    _RUNTIME_CONFIG["model"] = model
    _RUNTIME_CONFIG["base_url"] = base_url


def get_runtime_config() -> dict[str, str]:
    return dict(_RUNTIME_CONFIG)


class LLMClient:
    def __init__(
        self,
        provider: Provider | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        if _RUNTIME_CONFIG and provider is None:
            provider_str = _RUNTIME_CONFIG.get("provider", "openrouter")
            provider = provider_str  # type: ignore[assignment]

        self._provider: Provider = provider or settings.llm_provider or "openrouter"  # type: ignore[assignment]

        self._api_key = (
            api_key
            or _RUNTIME_CONFIG.get("api_key")
            or settings.llm_api_key
            or ""
        )

        self._model = (
            model
            or _RUNTIME_CONFIG.get("model")
            or settings.llm_model
            or DEFAULT_MODEL.get(self._provider, "gpt-4o-mini")
        )

        self._base_url = (
            base_url
            or _RUNTIME_CONFIG.get("base_url")
            or PROVIDER_BASE_URLS.get(self._provider, "https://openrouter.ai/api/v1")
        )

    @property
    def provider(self) -> Provider:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        if not self._api_key and self._provider != "ollama":
            logger.warning("llm_no_api_key", provider=self._provider)
            return ""

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers=self._build_headers(),
            json=self._build_payload(system_prompt, user_prompt, temperature, max_tokens),
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        content: str | None = data["choices"][0]["message"]["content"]
        return content or ""

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            if self._provider == "anthropic":
                headers["x-api-key"] = self._api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _build_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self._provider == "anthropic":
            payload["messages"] = [
                {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"},
            ]
        return payload
