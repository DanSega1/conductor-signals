from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.config import settings
from app.schemas import ObservationCreate


class HomeAssistantCollector(CollectorCapability):
    collector_source = "home_assistant"
    collector_category = "home"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        self._client = HttpClient(
            base_url=settings.homeassistant_url.rstrip("/") + "/api",
            headers={
                "Authorization": f"Bearer {settings.homeassistant_token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        observations: list[ObservationCreate] = []

        states: list[dict[str, Any]] = self._client.get("/states")
        tracked_domains = {
            "sensor", "binary_sensor", "climate",
            "light", "switch", "cover",
        }

        for entity in states:
            entity_id: str = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else ""

            if domain not in tracked_domains:
                continue

            state = entity.get("state", "")
            attributes = entity.get("attributes", {})

            features: dict[str, Any] = {"state": state}

            numeric = _parse_numeric(state)
            if numeric is not None:
                features["value"] = numeric
                unit = attributes.get("unit_of_measurement")
                if unit:
                    features["unit"] = unit

            for attr in ["temperature", "humidity", "battery_level", "illuminance",
                          "pressure", "wind_speed", "power_consumption", "energy",
                          "current", "voltage", "speed", "position"]:
                val = attributes.get(attr)
                if val is not None:
                    features[attr] = val

            name = attributes.get("friendly_name", entity_id)
            area = attributes.get("area_id", attributes.get("area", ""))

            observations.append(
                ObservationCreate(
                    timestamp=now,
                    source="home_assistant",
                    category="home",
                    entity=domain,
                    features=features,
                    metadata={
                        "entity_id": entity_id,
                        "name": name,
                        "area": area,
                        "domain": domain,
                        "device_class": attributes.get("device_class", ""),
                        "last_changed": entity.get("last_changed", ""),
                    },
                )
            )

        return observations


def _parse_numeric(value: str) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
