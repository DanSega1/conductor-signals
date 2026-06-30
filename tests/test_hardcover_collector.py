from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.hardcover import HardcoverCollector
from app.config import settings
from app.storage import DuckDBRepository

CURRENTLY_READING = {
    "data": [
        {
            "book": {"title": "Test Book", "author": "Test Author", "id": "123"},
            "progress": 45,
            "pages_read": 150,
            "status": "reading",
        }
    ]
}

FINISHED_BOOKS: dict[str, Any] = {"data": []}


def _set_env(monkeypatch: Any) -> None:
    monkeypatch.setattr(settings, "hardcover_api_key", "test-key")


def _make_collector(db_path: Path, monkeypatch: Any) -> HardcoverCollector:
    _set_env(monkeypatch)
    repo = DuckDBRepository(db_path)
    return HardcoverCollector(repository=repo)


@pytest.mark.respx(base_url="https://api.hardcover.app")
def test_hardcover_collector_current_reading(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/v1/me/reading.*").respond(json=CURRENTLY_READING)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    entities = {o.entity for o in observations}
    assert "currently_reading" in entities


@pytest.mark.respx(base_url="https://api.hardcover.app")
def test_hardcover_collector_api_error(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/v1/me/reading.*").respond(status_code=401)

    collector = _make_collector(db_path, monkeypatch)
    with pytest.raises(httpx.HTTPStatusError):
        collector.collect(CollectorInput())
