from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import polars as pl

from app.schemas import Insight, InsightCreate, Observation, ObservationCreate


class AbstractRepository(ABC):
    @abstractmethod
    def store_observation(self, data: ObservationCreate) -> Observation: ...

    @abstractmethod
    def store_insight(self, data: InsightCreate) -> Insight: ...

    @abstractmethod
    def get_observations(
        self,
        source: str | None = None,
        entity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Observation]: ...

    @abstractmethod
    def get_timeline(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> list[Observation]: ...

    @abstractmethod
    def query_sql(self, sql: str) -> pl.DataFrame: ...

    @abstractmethod
    def store_parquet(self, df: pl.DataFrame, path: Path) -> None: ...

    @abstractmethod
    def read_parquet(self, path: Path) -> pl.DataFrame: ...

    @abstractmethod
    def close(self) -> None: ...
