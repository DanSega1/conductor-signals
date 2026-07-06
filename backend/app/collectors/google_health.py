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
from app.settings import store


class GoogleHealthCollector(CollectorCapability):
    collector_source = "google_health"
    collector_category = "health"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        data_dir = Path(settings.data_dir)
        token_store = OAuthTokenStore(data_dir / "tokens" / "google_health.json")
        runtime = store.get_integration("google_health")
        client_id = runtime.get("client_id") or settings.google_client_id or ""
        client_secret = runtime.get("client_secret") or settings.google_client_secret or ""
        self._oauth = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_url="https://oauth2.googleapis.com/token",
            token_store=token_store,
            scopes=[
                "https://www.googleapis.com/auth/fitness.activity.read",
                "https://www.googleapis.com/auth/fitness.body.read",
                "https://www.googleapis.com/auth/fitness.heart_rate.read",
                "https://www.googleapis.com/auth/fitness.sleep.read",
            ],
        )
        self._client = HttpClient(
            base_url="https://www.googleapis.com/fitness/v1/users/me",
            timeout=15.0,
        )

    def _get_token(self) -> str:
        return self._oauth.get_access_token()

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        token = self._get_token()
        observations: list[ObservationCreate] = []

        observations.extend(self._collect_sleep(yesterday, token))
        observations.extend(self._collect_heart_rate(yesterday, token))
        observations.extend(self._collect_steps(yesterday, token))
        observations.extend(self._collect_weight(yesterday, token))

        return observations

    def _aggregate(
        self, token: str, data_source_id: str, start: datetime, end: datetime
    ) -> Any:
        body = {
            "aggregateBy": [{"dataSourceId": data_source_id}],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": int(start.timestamp() * 1000),
            "endTimeMillis": int(end.timestamp() * 1000),
        }
        resp = self._client.post(
            "/dataset:aggregate",
            data=body,
            auth_token=token,
        )
        return resp

    def _collect_sleep(
        self, day: datetime, token: str
    ) -> list[ObservationCreate]:
        try:
            end = day.replace(hour=23, minute=59, second=59)
            start = day.replace(hour=0, minute=0, second=0)
            data = self._aggregate(
                token,
                "derived:com.google.sleep.segment:com.google.android.gms:merge_sleep",
                start,
                end,
            )
            buckets = data.get("bucket", [])
            total_sleep_ms = 0
            for bucket in buckets:
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        for val in point.get("value", []):
                            fp_val = val.get("fpVal", 0)
                            if fp_val > 0:
                                total_sleep_ms += int(fp_val)

            if total_sleep_ms == 0:
                return []

            return [
                ObservationCreate(
                    timestamp=day,
                    source="google_health",
                    category="health",
                    entity="sleep",
                    features={
                        "duration_minutes": total_sleep_ms / 60000,
                        "duration_hours": round(total_sleep_ms / 3600000, 2),
                    },
                    metadata={"date": day.strftime("%Y-%m-%d")},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning("google_health_sleep_failed", error=str(e))
            return []

    def _collect_heart_rate(
        self, day: datetime, token: str
    ) -> list[ObservationCreate]:
        try:
            end = day.replace(hour=23, minute=59, second=59)
            start = day.replace(hour=0, minute=0, second=0)
            data = self._aggregate(
                token,
                "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm",
                start,
                end,
            )
            buckets = data.get("bucket", [])
            bpm_values: list[float] = []
            for bucket in buckets:
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        for val in point.get("value", []):
                            fp_val = val.get("fpVal", 0)
                            if fp_val > 0:
                                bpm_values.append(fp_val)

            if not bpm_values:
                return []

            return [
                ObservationCreate(
                    timestamp=day,
                    source="google_health",
                    category="health",
                    entity="heart_rate",
                    features={
                        "avg_bpm": round(sum(bpm_values) / len(bpm_values), 1),
                        "min_bpm": round(min(bpm_values), 1),
                        "max_bpm": round(max(bpm_values), 1),
                        "samples": len(bpm_values),
                    },
                    metadata={"date": day.strftime("%Y-%m-%d")},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning("google_health_heart_rate_failed", error=str(e))
            return []

    def _collect_steps(
        self, day: datetime, token: str
    ) -> list[ObservationCreate]:
        try:
            end = day.replace(hour=23, minute=59, second=59)
            start = day.replace(hour=0, minute=0, second=0)
            data = self._aggregate(
                token,
                "derived:com.google.step_count.delta:com.google.android.gms:merge_step_delta",
                start,
                end,
            )
            buckets = data.get("bucket", [])
            total_steps = 0
            for bucket in buckets:
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        for val in point.get("value", []):
                            int_val = val.get("intVal", 0)
                            if int_val > 0:
                                total_steps += int_val

            if total_steps == 0:
                return []

            return [
                ObservationCreate(
                    timestamp=day,
                    source="google_health",
                    category="health",
                    entity="steps",
                    features={"steps": total_steps},
                    metadata={"date": day.strftime("%Y-%m-%d")},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning("google_health_steps_failed", error=str(e))
            return []

    def _collect_weight(
        self, day: datetime, token: str
    ) -> list[ObservationCreate]:
        try:
            end = day.replace(hour=23, minute=59, second=59)
            start = day.replace(hour=0, minute=0, second=0)
            data = self._aggregate(
                token,
                "derived:com.google.weight:com.google.android.gms:merge_weight",
                start,
                end,
            )
            buckets = data.get("bucket", [])
            weights: list[float] = []
            for bucket in buckets:
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        for val in point.get("value", []):
                            fp_val = val.get("fpVal", 0)
                            if fp_val > 0:
                                weights.append(fp_val)

            if not weights:
                return []

            return [
                ObservationCreate(
                    timestamp=day,
                    source="google_health",
                    category="health",
                    entity="weight",
                    features={
                        "weight_kg": round(sum(weights) / len(weights), 2),
                    },
                    metadata={"date": day.strftime("%Y-%m-%d")},
                )
            ]
        except httpx.HTTPStatusError as e:
            logger.warning("google_health_weight_failed", error=str(e))
            return []
