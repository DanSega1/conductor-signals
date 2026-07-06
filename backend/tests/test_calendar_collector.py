from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.calendar import CalendarCollector
from app.collectors.oauth import OAuthTokenStore
from app.config import settings
from app.storage import DuckDBRepository

TOKEN = {
    "access_token": "test-access-token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "test-refresh-token",
    "created_at": datetime.now(UTC).isoformat(),
}

EVENTS_RESPONSE = {
    "items": [
        {
            "summary": "Test Event",
            "start": {"dateTime": "2026-06-30T10:00:00+00:00"},
            "end": {"dateTime": "2026-06-30T11:00:00+00:00"},
            "description": "A test event",
            "location": "Office",
            "creator": {"email": "test@example.com"},
            "status": "confirmed",
        }
    ]
}


def _set_env(monkeypatch: Any, data_dir: str) -> None:
    monkeypatch.setattr(settings, "calendar_client_id", "test-id")
    monkeypatch.setattr(settings, "calendar_client_secret", "test-secret")
    monkeypatch.setattr(settings, "calendar_id", "primary")
    monkeypatch.setattr(settings, "data_dir", data_dir)


def _make_collector(db_path: Path, monkeypatch: Any) -> CalendarCollector:
    data_dir = str(db_path.parent)
    _set_env(monkeypatch, data_dir)
    repo = DuckDBRepository(db_path)
    store = OAuthTokenStore(db_path.parent / "tokens" / "calendar.json")
    store.save(TOKEN)
    return CalendarCollector(repository=repo)


@pytest.mark.respx(base_url="https://www.googleapis.com")
def test_calendar_collector_events(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/calendar/v3/calendars/.*/events.*").respond(
        json=EVENTS_RESPONSE
    )

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    assert len(observations) == 1
    obs = observations[0]
    assert obs.entity == "event"
    assert obs.features["duration_minutes"] == 60
    assert obs.metadata["title"] == "Test Event"
    assert obs.source == "calendar"


@pytest.mark.respx(base_url="https://www.googleapis.com")
def test_calendar_collector_empty(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/calendar/v3/calendars/.*/events.*").respond(
        json={"items": []}
    )

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())
    assert observations == []
