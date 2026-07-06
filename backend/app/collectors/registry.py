from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from app.logging import logger

if TYPE_CHECKING:
    from app.collectors.base import CollectorCapability


class CollectorRegistry:
    _collectors: ClassVar[dict[str, type[CollectorCapability]]] = {}

    @classmethod
    def register(cls, collector_cls: type[CollectorCapability]) -> None:
        source: str = collector_cls.__dict__.get("collector_source", "")
        if source in cls._collectors:
            logger.warning("collector_overwrite", source=source)
        cls._collectors[source] = collector_cls
        logger.debug("collector_registered", source=source)

    @classmethod
    def get(cls, source: str) -> type[CollectorCapability] | None:
        return cls._collectors.get(source)

    @classmethod
    def all(cls) -> dict[str, type[CollectorCapability]]:
        return dict(cls._collectors)

    @classmethod
    def discover_plugins(cls, plugin_dir: str | Path) -> int:
        plugin_dir = Path(plugin_dir)
        if not plugin_dir.is_dir():
            return 0

        count = 0
        for path in sorted(plugin_dir.iterdir()):
            if path.suffix != ".py" or path.name.startswith("_"):
                continue
            if path.stem in cls._collectors:
                continue
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    path.stem, str(path)
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    count += 1
            except Exception:
                logger.exception("plugin_load_failed", path=str(path))
        return count

    @classmethod
    def enabled_collectors(
        cls, settings: Any
    ) -> dict[str, type[CollectorCapability]]:
        result: dict[str, type[CollectorCapability]] = {}
        for source, collector_cls in cls._collectors.items():
            flag = getattr(
                settings,
                f"collector_{source}_enabled",
                None,
            )
            if flag:
                result[source] = collector_cls
        return result
