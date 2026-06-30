from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.collectors.oauth import OAuth2Client, OAuthTokenStore
from app.config import settings
from app.logging import logger
from app.schemas import ObservationCreate


def _min_from(
    summary: dict[str, Any], key: str, default: int = 0
) -> int:
    val = summary.get(key)
    if isinstance(val, dict):
        return val.get("minutes", default) or default
    return default


class FitbitCollector(CollectorCapability):
    collector_source = "fitbit"
    collector_category = "health"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        data_dir = Path(settings.data_dir)
        token_store = OAuthTokenStore(data_dir / "tokens" / "fitbit.json")
        self._oauth = OAuth2Client(
            client_id=settings.fitbit_client_id,
            client_secret=settings.fitbit_client_secret,
            token_url="https://api.fitbit.com/oauth2/token",
            token_store=token_store,
        )
        self._client = HttpClient(
            base_url="https://api.fitbit.com/1/user/-",
            timeout=15.0,
        )

    def _get_token(self) -> str:
        return self._oauth.get_access_token()

    def _heart_value(self, heart: dict[str, Any], key: str, default: Any = 0) -> Any:
        return (
            heart.get("activities-heart", [{}])[0]
            .get("value", {})
            .get(key, default)
        )

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        today = now.strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        token = self._get_token()
        observations: list[ObservationCreate] = []

        for date_str in [yesterday, today]:
            observations.extend(
                self._collect_sleep(date_str, token)
            )
            observations.extend(
                self._collect_hrv(date_str, token)
            )
            observations.extend(
                self._collect_heart_rate(date_str, token)
            )
            observations.extend(
                self._collect_activity(date_str, token)
            )

        return observations

    def _collect_sleep(
        self, date_str: str, token: str
    ) -> list[ObservationCreate]:
        try:
            sleep = self._client.get(
                f"/sleep/date/{date_str}.json", auth_token=token
            )
            summary = sleep.get("summary", {})
            if not summary:
                return []
            return [
                ObservationCreate(
                    timestamp=datetime.fromisoformat(date_str),
                    source="fitbit",
                    category="health",
                    entity="sleep",
                    features={
                        "score": summary.get("score", 0) or 0,
                        "duration_minutes": summary.get("totalMinutesAsleep", 0) or 0,
                        "efficiency": summary.get("efficiency", 0) or 0,
                        "restless_count": summary.get("restlessCount", 0) or 0,
                        "awake_count": summary.get("awakeCount", 0) or 0,
                        "rem_minutes": _min_from(summary, "rem"),
                        "deep_minutes": _min_from(summary, "deep"),
                        "light_minutes": _min_from(summary, "light"),
                    },
                    metadata={"date": date_str},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning(
                "fitbit_sleep_failed", date=date_str, error=str(e)
            )
            return []

    def _collect_hrv(
        self, date_str: str, token: str
    ) -> list[ObservationCreate]:
        try:
            hrv = self._client.get(
                f"/hrv/date/{date_str}.json", auth_token=token
            )
            hrv_summary = hrv.get("summary", {})
            if not hrv_summary:
                return []
            return [
                ObservationCreate(
                    timestamp=datetime.fromisoformat(date_str),
                    source="fitbit",
                    category="health",
                    entity="hrv",
                    features={
                        "daily_rmssd": hrv_summary.get("dailyRmssd", 0) or 0,
                        "deep_rmssd": hrv_summary.get("deepRmssd", 0) or 0,
                    },
                    metadata={"date": date_str},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning(
                "fitbit_hrv_failed", date=date_str, error=str(e)
            )
            return []

    def _collect_heart_rate(
        self, date_str: str, token: str
    ) -> list[ObservationCreate]:
        try:
            heart = self._client.get(
                f"/heart/date/{date_str}/1d.json", auth_token=token
            )
            heart_zones = self._heart_value(heart, "heartRateZones", [])
            resting = self._heart_value(heart, "restingHeartRate", 0)
            features: dict[str, Any] = {
                "resting_heart_rate": resting or 0,
            }
            for zone in heart_zones:
                name = zone.get("name", "").lower().replace(" ", "_")
                features[f"{name}_minutes"] = zone.get("minutes", 0)
                features[f"{name}_calories"] = zone.get("caloriesOut", 0)

            return [
                ObservationCreate(
                    timestamp=datetime.fromisoformat(date_str),
                    source="fitbit",
                    category="health",
                    entity="heart_rate",
                    features=features,
                    metadata={"date": date_str},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning(
                "fitbit_heart_failed", date=date_str, error=str(e)
            )
            return []

    def _collect_activity(
        self, date_str: str, token: str
    ) -> list[ObservationCreate]:
        try:
            activity = self._client.get(
                f"/activities/date/{date_str}.json", auth_token=token
            )
            summary = activity.get("summary", {})
            if not summary:
                return []

            distances = summary.get("distances")
            distance = 0
            if distances:
                distance = distances[0].get("distance", 0)

            return [
                ObservationCreate(
                    timestamp=datetime.fromisoformat(date_str),
                    source="fitbit",
                    category="health",
                    entity="activity",
                    features={
                        "steps": summary.get("steps", 0) or 0,
                        "calories": summary.get("caloriesOut", 0) or 0,
                        "distance_meters": distance,
                        "active_minutes": summary.get("fairlyActiveMinutes", 0)
                        + summary.get("veryActiveMinutes", 0),
                        "sedentary_minutes": summary.get("sedentaryMinutes", 0),
                        "floors": summary.get("floors", 0) or 0,
                        "elevation_meters": summary.get("elevation", 0) or 0,
                    },
                    metadata={"date": date_str},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning(
                "fitbit_activity_failed", date=date_str, error=str(e)
            )
            return []
