from __future__ import annotations

import httpx
import pytest
import respx

from app.llm import LLMClient

OPENROUTER_RESPONSE = {
    "choices": [{"message": {"content": "Found 3 trends this week."}}]
}


def test_llm_complete_returns_content() -> None:
    client = LLMClient(api_key="test-key", model="gpt-4o-mini")
    with respx.mock:
        respx.post("https://openrouter.ai/api/v1/chat/completions").respond(
            json=OPENROUTER_RESPONSE
        )
        result = client.complete(
            system_prompt="Analyze this data.",
            user_prompt="Current vs previous period data here.",
        )
    assert result == "Found 3 trends this week."


def test_llm_complete_empty_on_no_api_key() -> None:
    client = LLMClient(api_key="", model="gpt-4o-mini")
    result = client.complete(
        system_prompt="Analyze.",
        user_prompt="Data.",
    )
    assert result == ""


def test_llm_complete_raises_on_http_error() -> None:
    client = LLMClient(api_key="bad-key", model="gpt-4o-mini")
    with respx.mock:
        respx.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=401
        )
        with pytest.raises(httpx.HTTPStatusError):
            client.complete(
                system_prompt="Analyze.",
                user_prompt="Data.",
            )
