from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.weather import WeatherCollector
from app.config import settings
from app.storage import DuckDBRepository

CURRENT_RESPONSE = {
    "main": {"temp": 22.5, "feels_like": 21.0, "humidity": 65, "pressure": 1013},
    "wind": {"speed": 4.2},
    "clouds": {"all": 40},
    "visibility": 10000,
    "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
    "name": "TestCity",
    "sys": {"country": "US", "sunrise": 1680000000, "sunset": 1680040000},
}

FORECAST_RESPONSE = {
    "list": [
        {"dt": 1680000000, "main": {"temp": 22.0}},
        {"dt": 1680003600, "main": {"temp": 24.0}},
        {"dt": 1680086400, "main": {"temp": 20.0}},
    ]
}


def _set_env(monkeypatch: Any) -> None:
    monkeypatch.setattr(settings, "weather_api_key", "test-key")
    monkeypatch.setattr(settings, "weather_lat", 40.7128)
    monkeypatch.setattr(settings, "weather_lon", -74.0060)


def _make_collector(db_path: Path, monkeypatch: Any) -> WeatherCollector:
    _set_env(monkeypatch)
    repo = DuckDBRepository(db_path)
    return WeatherCollector(repository=repo)


@pytest.mark.respx(base_url="https://api.openweathermap.org")
def test_weather_collector_current_and_forecast(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/data/2\.5/weather.*").respond(json=CURRENT_RESPONSE)
    respx_mock.get(path__regex=r"/data/2\.5/forecast.*").respond(json=FORECAST_RESPONSE)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    assert len(observations) >= 2
    entities = {o.entity for o in observations}
    assert "current_conditions" in entities
    assert "forecast" in entities

    current = next(o for o in observations if o.entity == "current_conditions")
    assert current.features["temperature"] == 22.5
    assert current.source == "weather"
    assert current.category == "environment"


@pytest.mark.respx(base_url="https://api.openweathermap.org")
def test_weather_collector_api_error(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r"/data/2\.5/weather.*").respond(status_code=401)

    collector = _make_collector(db_path, monkeypatch)
    with pytest.raises(httpx.HTTPStatusError):
        collector.collect(CollectorInput())
