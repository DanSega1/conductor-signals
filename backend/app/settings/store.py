from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from app.config import settings as env_settings

_DATA_DIR = Path(env_settings.data_dir)
_SETTINGS_PATH = _DATA_DIR / "settings.json"
_lock = Lock()


def _load() -> dict[str, Any]:
    if not _SETTINGS_PATH.exists():
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text("{}")
        return {}
    try:
        return dict(json.loads(_SETTINGS_PATH.read_text()))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict[str, Any]) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2, default=str))


class RuntimeSettings:
    def get_integration(self, source: str) -> dict[str, str]:
        with _lock:
            data = _load()
            return dict(data.get("integrations", {}).get(source, {}))

    def set_integration(self, source: str, values: dict[str, str]) -> None:
        with _lock:
            data = _load()
            integrations = data.setdefault("integrations", {})
            existing = dict(integrations.get(source, {}))
            existing.update({k: v for k, v in values.items() if v})
            integrations[source] = existing
            _save(data)

    def get_all_integrations(self) -> dict[str, dict[str, str]]:
        with _lock:
            data = _load()
            return dict(data.get("integrations", {}))

    def resolve(self, source: str, field_map: dict[str, str]) -> dict[str, str]:
        runtime = self.get_integration(source)
        result: dict[str, str] = {}
        for env_name, runtime_key in field_map.items():
            val = runtime.get(runtime_key) or getattr(env_settings, env_name, None) or ""
            result[runtime_key] = str(val) if val is not None else ""
        return result


store = RuntimeSettings()
