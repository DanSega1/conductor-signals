from __future__ import annotations

import time
from typing import Any

import httpx

from app.logging import logger


class HttpClient:
    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._timeout = timeout
        self._max_retries = max_retries

    def _url(self, path: str) -> str:
        if self._base_url:
            return f"{self._base_url}/{path.lstrip('/')}"
        return path

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    def _request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        auth_token: str | None = None,
    ) -> Any:
        url = self._url(path)
        all_headers = {**self._headers}
        if headers:
            all_headers.update(headers)
        if auth_token and "Authorization" not in all_headers:
            all_headers["Authorization"] = f"Bearer {auth_token}"

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = httpx.request(
                    method=method,
                    url=url,
                    headers=all_headers or None,
                    params=params,
                    json=data,
                    timeout=self._timeout,
                )
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                if response.status_code == 204:
                    return {}
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                logger.warning(
                    "http_retry",
                    attempt=attempt + 1,
                    status=e.response.status_code,
                    url=url,
                )
        raise last_error or RuntimeError(
            f"Request failed after {self._max_retries} retries"
        )
