from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.loader import load_builtin_capabilities
from engine.runtime.store import LocalTaskStore
from engine.supervisor.service import TaskSupervisor

from app.collectors.base import CollectorCapability
from app.config import settings


class ConductorEngine:
    def __init__(
        self,
        data_dir: Path | None = None,
    ) -> None:
        data_dir = data_dir or settings.data_dir
        workdir = data_dir / "conductor"
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
