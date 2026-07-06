from __future__ import annotations

import httpx

from app.config import settings
from app.logging import logger

DEFAULT_MODEL = "gpt-4o-mini"


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        self._api_key = api_key or settings.llm_api_key or ""
        self._model = model or settings.llm_model or DEFAULT_MODEL
        self._base_url = base_url.rstrip("/")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        if not self._api_key:
            logger.warning("llm_no_api_key", provider="openrouter")
            return ""

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        content: str | None = data["choices"][0]["message"]["content"]
        return content or ""
