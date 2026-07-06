from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OBSERVATORY_",

    )

    data_dir: Path = Path("data")

    storage_backend: Literal["duckdb", "parquet"] = "duckdb"
    database_path: Path = Path("data/observatory.duckdb")

    log_level: str = "INFO"
    log_json: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    conductor_workdir: str = "conductor"
    conductor_task_store: Literal["local", "sqlite"] = "local"

    collector_fitbit_enabled: bool = False
    collector_calendar_enabled: bool = False
    collector_spotify_enabled: bool = False
    collector_weather_enabled: bool = False
    collector_homeassistant_enabled: bool = False
    collector_hardcover_enabled: bool = False

    fitbit_client_id: str = ""
    fitbit_client_secret: str = ""

    calendar_client_id: str = ""
    calendar_client_secret: str = ""
    calendar_id: str = "primary"

    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    weather_api_key: str = ""
    weather_lat: float = 0.0
    weather_lon: float = 0.0
    weather_units: str = "metric"

    hardcover_api_key: str = ""

    homeassistant_url: str = ""
    homeassistant_token: str = ""


settings = Settings()
