from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import duckdb
import polars as pl

from app.config import settings
from app.schemas import Observation, ObservationCreate


class Repository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE,
                source VARCHAR,
                category VARCHAR,
                entity VARCHAR,
                features JSON,
                metadata JSON,
                version INTEGER DEFAULT 1
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id VARCHAR PRIMARY KEY,
                title VARCHAR,
                description VARCHAR,
                source VARCHAR,
                confidence DOUBLE,
                timestamp TIMESTAMP WITH TIME ZONE,
                metadata JSON
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_source
            ON observations (source)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_timestamp
            ON observations (timestamp)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_entity
            ON observations (entity)
        """)

    def store_observation(self, data: ObservationCreate) -> Observation:
        observation = Observation(
            id=str(uuid4()),
            timestamp=data.timestamp,
            source=data.source,
            category=data.category,
            entity=data.entity,
            features=data.features,
            metadata={
                **data.metadata,
                "stored_at": datetime.now(UTC).isoformat(),
            },
        )
        self._conn.execute(
            """
            INSERT OR REPLACE INTO observations
            (id, timestamp, source, category, entity, features, metadata, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                observation.id,
                observation.timestamp,
                observation.source,
                observation.category,
                observation.entity,
                observation.features,
                observation.metadata,
                observation.version,
            ],
        )
        return observation

    def get_observations(
        self,
        source: str | None = None,
        entity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Observation]:
        query = "SELECT * FROM observations WHERE 1=1"
        params: list[Any] = []

        if source:
            query += " AND source = ?"
            params.append(source)
        if entity:
            query += " AND entity = ?"
            params.append(entity)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_observation(row) for row in rows]

    def get_timeline(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> list[Observation]:
        query = "SELECT * FROM observations WHERE 1=1"
        params: list[Any] = []

        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_observation(row) for row in rows]

    def query_sql(self, sql: str) -> pl.DataFrame:
        result = pl.from_arrow(self._conn.execute(sql).to_arrow_table())
        return cast(pl.DataFrame, result)

    def store_parquet(self, df: pl.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(str(path))

    def read_parquet(self, path: Path) -> pl.DataFrame:
        return pl.read_parquet(str(path))

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_observation(row: tuple[Any, ...]) -> Observation:
        features = json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {})
        metadata = json.loads(row[6]) if isinstance(row[6], str) else (row[6] or {})
        return Observation(
            id=row[0],
            timestamp=row[1],
            source=row[2],
            category=row[3],
            entity=row[4],
            features=features,
            metadata=metadata,
            version=row[7],
        )
