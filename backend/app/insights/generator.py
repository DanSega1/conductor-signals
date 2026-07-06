from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.analytics.engine import AnalyticsEngine
from app.insights.prompts import SYSTEM_PROMPT
from app.llm import LLMClient
from app.logging import logger
from app.schemas import InsightCreate
from app.storage import Repository


class InsightGenerator:
    def __init__(
        self,
        repository: Repository,
        llm_client: LLMClient | None = None,
        analytics: AnalyticsEngine | None = None,
    ) -> None:
        self._repo = repository
        self._llm = llm_client or LLMClient()
        self._analytics = analytics or AnalyticsEngine(repository)

    def generate(self) -> list[InsightCreate]:
        context = self._build_context()
        total = len(context["current"]) + len(context["previous"])
        if total == 0:
            logger.info("insight_no_observations")
            return []

        prompt = self._build_prompt(context)
        raw = self._llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        if not raw:
            return []

        return self._parse_response(raw)

    def _build_context(self) -> dict[str, list[dict[str, object]]]:
        return {
            "current": self._analytics.recent_observations(limit=50).to_dicts(),
            "previous": self._period_observations(7, 14),
            "year_over_year": self._year_over_year_samples(),
            "recurring": self._recurring_samples(),
        }

    def _period_observations(
        self, start_days: int, end_days: int
    ) -> list[dict[str, object]]:
        df = self._analytics._query(
            f"""
            SELECT timestamp, source, category, entity, features, metadata
            FROM observations
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{end_days}' DAY
              AND timestamp < CURRENT_TIMESTAMP - INTERVAL '{start_days}' DAY
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        return df.to_dicts()

    def _year_over_year_samples(self) -> list[dict[str, object]]:
        df = self._analytics._query("""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(YEAR FROM timestamp) AS year,
                entity,
                features
            FROM observations
            WHERE CAST(features AS VARCHAR) != '{}'
            ORDER BY timestamp DESC
            LIMIT 30
        """)
        return df.to_dicts()

    def _recurring_samples(self) -> list[dict[str, object]]:
        df = self._analytics._query("""
            SELECT
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DOW FROM timestamp) AS day_of_week,
                entity,
                COUNT(*) AS count
            FROM observations
            GROUP BY month, day_of_week, entity
            ORDER BY count DESC
            LIMIT 20
        """)
        return df.to_dicts()

    def _build_prompt(self, context: dict[str, list[dict[str, object]]]) -> str:
        parts: list[str] = ["# Current period (last 7 days)\n"]
        for obs in context["current"]:
            parts.append(self._format_obs(obs))

        parts.append("\n# Previous period (7-14 days ago)\n")
        for obs in context["previous"]:
            parts.append(self._format_obs(obs))

        parts.append("\n# Year-over-year samples\n")
        for obs in context["year_over_year"]:
            parts.append(
                f"  month={obs.get('month')}, year={obs.get('year')}, "
                f"entity={obs.get('entity')}, features={obs.get('features')}"
            )

        parts.append("\n# Recurring patterns (month x day_of_week)\n")
        for obs in context["recurring"]:
            parts.append(
                f"  month={obs.get('month')}, dow={obs.get('day_of_week')}, "
                f"entity={obs.get('entity')}, count={obs.get('count')}"
            )

        return "\n".join(parts)

    def _format_obs(self, obs: dict[str, object]) -> str:
        return (
            f"  [{obs.get('timestamp')}] {obs.get('source')}/{obs.get('entity')}: "
            f"features={obs.get('features')}, metadata={obs.get('metadata')}"
        )

    def _parse_response(self, raw: str) -> list[InsightCreate]:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                cleaned = cleaned.rsplit("```", 1)[0].strip()
            data: dict[str, Any] = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            logger.warning("insight_parse_failed", raw=raw[:200])
            return []

        now = datetime.now(UTC)
        results: list[InsightCreate] = []
        for item in data.get("insights", []):
            results.append(
                InsightCreate(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    source="llm",
                    confidence=float(item.get("confidence", 0.5)),
                    timestamp=now,
                    metadata={"llm_raw": raw},
                )
            )
        return results

    def generate_and_store(self) -> int:
        insights = self.generate()
        for insight in insights:
            self._repo.store_insight(insight)
        logger.info("insights_stored", count=len(insights))
        return len(insights)
