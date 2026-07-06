from __future__ import annotations

import re

import polars as pl

from app.storage import Repository


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-.$]", "", name)


class AnalyticsEngine:
    def __init__(self, repository: Repository) -> None:
        self._repo = repository

    def _query(self, sql: str) -> pl.DataFrame:
        return self._repo.query_sql(sql)

    def period_summary(
        self, source: str | None = None, entity: str | None = None, days: int = 7
    ) -> pl.DataFrame:
        filters = ["1=1"]
        if source:
            filters.append(f"source = '{_safe(source)}'")
        if entity:
            filters.append(f"entity = '{_safe(entity)}'")
        where = " AND ".join(filters)
        sql = f"""
            SELECT
                DATE(timestamp) AS date,
                source,
                entity,
                features,
                metadata
            FROM observations
            WHERE {where}
              AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY timestamp DESC
        """
        return self._query(sql)

    def period_comparison(self, entity: str, days: int = 7) -> pl.DataFrame:
        safe_entity = _safe(entity)
        sql = f"""
            SELECT
                'current' AS period,
                DATE(timestamp) AS date,
                features,
                metadata
            FROM observations
            WHERE entity = '{safe_entity}'
              AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY

            UNION ALL

            SELECT
                'previous' AS period,
                DATE(timestamp) AS date,
                features,
                metadata
            FROM observations
            WHERE entity = '{safe_entity}'
              AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{2 * days}' DAY
              AND timestamp < CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY date DESC
        """
        return self._query(sql)

    def year_over_year(self, entity: str, feature: str) -> pl.DataFrame:
        safe_entity = _safe(entity)
        safe_feat = _safe(feature)
        sql = f"""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DAY FROM timestamp) AS day,
                EXTRACT(YEAR FROM timestamp) AS year,
                features->>'$.{safe_feat}' AS {safe_feat}
            FROM observations
            WHERE entity = '{safe_entity}'
              AND json_type(features, '$.{safe_feat}') != 'NULL'
            ORDER BY year, month, day
        """
        return self._query(sql)

    def recurring_patterns(self, entity: str, feature: str) -> pl.DataFrame:
        safe_entity = _safe(entity)
        safe_feat = _safe(feature)
        sql = f"""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DOW FROM timestamp) AS day_of_week,
                AVG(CAST(features->>'$.{safe_feat}' AS DOUBLE)) AS avg_value,
                COUNT(*) AS sample_count
            FROM observations
            WHERE entity = '{safe_entity}'
              AND json_type(features, '$.{safe_feat}') != 'NULL'
            GROUP BY month, day_of_week
            ORDER BY month, day_of_week
        """
        return self._query(sql)

    def recent_observations(self, limit: int = 50) -> pl.DataFrame:
        return self._query(
            f"""
            SELECT timestamp, source, category, entity, features, metadata
            FROM observations
            ORDER BY timestamp DESC
            LIMIT {limit}
            """
        )
