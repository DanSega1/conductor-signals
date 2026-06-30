from __future__ import annotations

import polars as pl

from app.storage import Repository


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
            filters.append(f"source = '{source}'")
        if entity:
            filters.append(f"entity = '{entity}'")
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
        sql = f"""
            SELECT
                'current' AS period,
                DATE(timestamp) AS date,
                features,
                metadata
            FROM observations
            WHERE entity = '{entity}'
              AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY

            UNION ALL

            SELECT
                'previous' AS period,
                DATE(timestamp) AS date,
                features,
                metadata
            FROM observations
            WHERE entity = '{entity}'
              AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{2 * days}' DAY
              AND timestamp < CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY date DESC
        """
        return self._query(sql)

    def year_over_year(self, entity: str, feature: str) -> pl.DataFrame:
        sql = f"""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DAY FROM timestamp) AS day,
                EXTRACT(YEAR FROM timestamp) AS year,
                features->>'$.{feature}' AS {feature}
            FROM observations
            WHERE entity = '{entity}'
              AND json_type(features, '$.{feature}') != 'NULL'
            ORDER BY year, month, day
        """
        return self._query(sql)

    def recurring_patterns(self, entity: str, feature: str) -> pl.DataFrame:
        sql = f"""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DOW FROM timestamp) AS day_of_week,
                AVG(CAST(features->>'$.{feature}' AS DOUBLE)) AS avg_value,
                COUNT(*) AS sample_count
            FROM observations
            WHERE entity = '{entity}'
              AND json_type(features, '$.{feature}') != 'NULL'
            GROUP BY month, day_of_week
            ORDER BY month, day_of_week
        """
        return self._query(sql)

    def recent_observations(self, limit: int = 50) -> list[dict[str, object]]:
        df = self._query(
            f"""
            SELECT timestamp, source, category, entity, features, metadata
            FROM observations
            ORDER BY timestamp DESC
            LIMIT {limit}
            """
        )
        return df.to_dicts()
