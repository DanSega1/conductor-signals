from __future__ import annotations

from abc import abstractmethod
from datetime import UTC, datetime
from typing import Any

from engine.interfaces.capability import (
    Capability,
    CapabilityContext,
    CapabilityDescriptor,
    CapabilityResult,
    RiskLevel,
)
from pydantic import BaseModel

from app.schemas import ObservationCreate
from app.storage import AbstractRepository


class CollectorInput(BaseModel):
    force: bool = False


class CollectorCapability(Capability):  # type: ignore[misc]
    input_model = CollectorInput

    def __init__(
        self,
        repository: AbstractRepository,
        **config: Any,
    ) -> None:
        super().__init__(**config)
        self._repository = repository

    @property
    @abstractmethod
    def collector_source(self) -> str: ...

    @property
    @abstractmethod
    def collector_category(self) -> str: ...

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.collector_source,
            description=f"Collects {self.collector_source} observations",
            risk_level=RiskLevel.LOW,
        )

    @abstractmethod
    def collect(self, payload: CollectorInput) -> list[ObservationCreate]: ...

    def execute(
        self,
        payload: BaseModel | dict[str, Any],
        context: CapabilityContext,  # noqa: ARG002
    ) -> CapabilityResult:
        if isinstance(payload, dict):
            payload = CollectorInput(**payload)
        assert isinstance(payload, CollectorInput)
        observations = self.collect(payload)
        stored = [self._repository.store_observation(obs) for obs in observations]
        return CapabilityResult(
            output={
                "source": self.collector_source,
                "collected": len(stored),
                "observations": [o.model_dump(mode="json") for o in stored],
            },
            metadata={
                "source": self.collector_source,
                "count": len(stored),
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
