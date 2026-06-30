from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.homeassistant import HomeAssistantCollector
from app.config import settings
from app.storage import DuckDBRepository

STATES_RESPONSE = [
    {
        "entity_id": "sensor.temperature",
        "state": "22.5",
        "attributes": {
            "friendly_name": "Living Room Temperature",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        },
        "last_changed": "2026-06-30T10:00:00+00:00",
    },
    {
        "entity_id": "sensor.humidity",
        "state": "55",
        "attributes": {
            "friendly_name": "Living Room Humidity",
            "unit_of_measurement": "%",
            "device_class": "humidity",
        },
        "last_changed": "2026-06-30T10:00:00+00:00",
    },
    {
        "entity_id": "binary_sensor.motion",
        "state": "on",
        "attributes": {
            "friendly_name": "Hallway Motion",
            "device_class": "motion",
        },
        "last_changed": "2026-06-30T10:05:00+00:00",
    },
    {
        "entity_id": "light.living_room",
        "state": "off",
        "attributes": {
            "friendly_name": "Living Room Light",
        },
        "last_changed": "2026-06-30T09:00:00+00:00",
    },
    {
        "entity_id": "switch.fan",
        "state": "on",
        "attributes": {
            "friendly_name": "Ceiling Fan",
        },
        "last_changed": "2026-06-30T08:00:00+00:00",
    },
    {
        "entity_id": "zone.home",
        "state": "0",
        "attributes": {
            "friendly_name": "Home",
        },
        "last_changed": "2026-06-30T00:00:00+00:00",
    },
]


def _set_env(monkeypatch: Any) -> None:
    monkeypatch.setattr(settings, "homeassistant_url", "http://ha.local:8123")
    monkeypatch.setattr(settings, "homeassistant_token", "test-token")


def _make_collector(db_path: Path, monkeypatch: Any) -> HomeAssistantCollector:
    _set_env(monkeypatch)
    repo = DuckDBRepository(db_path)
    return HomeAssistantCollector(repository=repo)


@pytest.mark.respx(base_url="http://ha.local:8123")
def test_home_assistant_collector_tracked_domains(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get("/api/states").respond(json=STATES_RESPONSE)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    entities = {o.entity for o in observations}
    assert "sensor" in entities
    assert "binary_sensor" in entities
    assert "light" in entities
    assert "switch" in entities
    assert "zone" not in entities

    temp = next(o for o in observations if o.entity == "sensor")
    assert temp.features["value"] == 22.5


@pytest.mark.respx(base_url="http://ha.local:8123")
def test_home_assistant_collector_empty(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get("/api/states").respond(json=[])

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())
    assert observations == []
