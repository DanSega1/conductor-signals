from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.loader import load_builtin_capabilities
from engine.runtime.store import LocalTaskStore
from engine.supervisor.service import TaskSupervisor

from app.collectors import CollectorCapability
from app.collectors.registry import CollectorRegistry
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

        plugin_dir = Path(__file__).parent / "collectors" / "plugins"
        discovered = CollectorRegistry.discover_plugins(plugin_dir)
        if discovered:
            logger.info("plugins_discovered", count=discovered)

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
        for source, collector_cls in CollectorRegistry.enabled_collectors(settings).items():
            logger.info("collector_enabled", source=source)
            self.register_collector(collector_cls)
