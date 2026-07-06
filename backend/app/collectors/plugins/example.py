"""
Example collector plugin.

Drop this file (or your own) in collectors/plugins/ and it will
be auto-discovered by the CollectorRegistry at startup.

Steps to create a collector:
  1. Subclass CollectorCapability
  2. Set collector_source (unique identifier)
  3. Set collector_category (grouping category)
  4. Implement collect() -> list[ObservationCreate]
  5. Enable via OBSERVATORY_COLLECTOR_{SOURCE}_ENABLED=true

No imports to add, no config to wire.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.collectors import CollectorCapability, CollectorInput
from app.schemas import ObservationCreate


class ExampleCollector(CollectorCapability):
    collector_source = "example"
    collector_category = "custom"

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        return [
            ObservationCreate(
                timestamp=datetime.now(UTC),
                source="example",
                category="custom",
                entity="sample_metric",
                features={"value": 42, "unit": "units"},
                metadata={"note": "This is an example observation from a plugin collector."},
            )
        ]
