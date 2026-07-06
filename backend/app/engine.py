from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.loader import load_builtin_capabilities
from engine.runtime.store import LocalTaskStore
from engine.supervisor.service import TaskSupervisor

from app.collectors import (
    CalendarCollector,
    CollectorCapability,
    FitbitCollector,
    HardcoverCollector,
    HomeAssistantCollector,
    SpotifyCollector,
    WeatherCollector,
)
from app.config import settings
from app.logging import logger


class ConductorEngine:
    def __init__(
        self,
        data_dir: Path | None = None,
    ) -> None:
        data_dir = data_dir or settings.data_dir
        workdir = data_dir / settings.conductor_workdir
        workdir.mkdir(parents=True, exist_ok=True)

        registry = load_builtin_capabilities()

        store = LocalTaskStore(str(workdir / "tasks.json"))

        supervisor = TaskSupervisor(
            registry=registry,
            store=store,
            workdir=str(workdir),
        )

        self._registry = registry
        self._store = store
        self._supervisor = supervisor
        self._workdir = workdir
        self._register_enabled_collectors()

    @property
    def supervisor(self) -> TaskSupervisor:
        return self._supervisor

    def register_collector(
        self,
        capability_class: type[CollectorCapability],
        **kwargs: Any,
    ) -> CollectorCapability:
        from app.storage import DuckDBRepository

        repo = DuckDBRepository()
        instance = capability_class(repository=repo, **kwargs)
        self._registry.register(instance)
        return instance

    def _register_enabled_collectors(self) -> None:
        collectors: list[type[CollectorCapability]] = []

        if settings.collector_weather_enabled:
            collectors.append(WeatherCollector)
            logger.info("collector_enabled", source="weather")

        if settings.collector_hardcover_enabled:
            collectors.append(HardcoverCollector)
            logger.info("collector_enabled", source="hardcover")

        if settings.collector_spotify_enabled:
            collectors.append(SpotifyCollector)
            logger.info("collector_enabled", source="spotify")

        if settings.collector_calendar_enabled:
            collectors.append(CalendarCollector)
            logger.info("collector_enabled", source="calendar")

        if settings.collector_fitbit_enabled:
            collectors.append(FitbitCollector)
            logger.info("collector_enabled", source="fitbit")

        if settings.collector_homeassistant_enabled:
            collectors.append(HomeAssistantCollector)
            logger.info("collector_enabled", source="home_assistant")

        for collector_class in collectors:
            self.register_collector(collector_class)
