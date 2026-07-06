from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.fitbit import FitbitCollector
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

SLEEP_RESPONSE = {
    "summary": {
        "score": 85,
        "totalMinutesAsleep": 420,
        "efficiency": 95,
        "restlessCount": 5,
        "awakeCount": 2,
        "rem": {"minutes": 90},
        "deep": {"minutes": 120},
        "light": {"minutes": 210},
    }
}

HRV_RESPONSE = {
    "summary": {
        "dailyRmssd": 42.5,
        "deepRmssd": 38.0,
    }
}

HEART_RESPONSE = {
    "activities-heart": [
        {
            "value": {
                "restingHeartRate": 62,
                "heartRateZones": [
                    {"name": "Out of Range", "minutes": 1200, "caloriesOut": 1800},
                    {"name": "Fat Burn", "minutes": 30, "caloriesOut": 150},
                    {"name": "Cardio", "minutes": 15, "caloriesOut": 100},
                    {"name": "Peak", "minutes": 5, "caloriesOut": 50},
                ],
            }
        }
    ]
}

EMPTY_SLEEP: dict[str, Any] = {"summary": {}}
EMPTY_HEART: dict[str, Any] = {"activities-heart": [{"value": {}}]}
EMPTY_HRV: dict[str, Any] = {"summary": {}}

ACTIVITY_RESPONSE = {
    "summary": {
        "steps": 8500,
        "caloriesOut": 2100,
        "distances": [{"activity": "total", "distance": 6.5}],
        "fairlyActiveMinutes": 25,
        "veryActiveMinutes": 15,
        "sedentaryMinutes": 480,
        "floors": 8,
        "elevation": 24.0,
    }
}


def _set_env(monkeypatch: Any, data_dir: str) -> None:
    monkeypatch.setattr(settings, "fitbit_client_id", "test-id")
    monkeypatch.setattr(settings, "fitbit_client_secret", "test-secret")
    monkeypatch.setattr(settings, "data_dir", data_dir)


def _make_collector(db_path: Path, monkeypatch: Any) -> FitbitCollector:
    data_dir = str(db_path.parent)
    _set_env(monkeypatch, data_dir)
    repo = DuckDBRepository(db_path)
    store = OAuthTokenStore(db_path.parent / "tokens" / "fitbit.json")
    store.save(TOKEN)
    return FitbitCollector(repository=repo)


@pytest.mark.respx(base_url="https://api.fitbit.com")
def test_fitbit_collector_all_entities(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r".*sleep.*").respond(json=SLEEP_RESPONSE)
    respx_mock.get(path__regex=r".*hrv.*").respond(json=HRV_RESPONSE)
    respx_mock.get(path__regex=r".*heart.*").respond(json=HEART_RESPONSE)
    respx_mock.get(path__regex=r".*activities.*").respond(json=ACTIVITY_RESPONSE)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    entities = {o.entity for o in observations}
    assert "sleep" in entities
    assert "hrv" in entities
    assert "heart_rate" in entities
    assert "activity" in entities


@pytest.mark.respx(base_url="https://api.fitbit.com")
def test_fitbit_collector_handles_empty_data(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r".*sleep.*").respond(json=EMPTY_SLEEP)
    respx_mock.get(path__regex=r".*hrv.*").respond(json=EMPTY_HRV)
    respx_mock.get(path__regex=r".*heart.*").respond(status_code=404)
    respx_mock.get(path__regex=r".*activities.*").respond(json=EMPTY_SLEEP)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())
    assert observations == []
