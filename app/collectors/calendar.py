from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.collectors.oauth import OAuth2Client, OAuthTokenStore
from app.config import settings
from app.schemas import ObservationCreate


class CalendarCollector(CollectorCapability):
    collector_source = "calendar"
    collector_category = "schedule"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        data_dir = Path(settings.data_dir)
        token_store = OAuthTokenStore(data_dir / "tokens" / "calendar.json")
        self._oauth = OAuth2Client(
            client_id=settings.calendar_client_id,
            client_secret=settings.calendar_client_secret,
            token_url="https://oauth2.googleapis.com/token",
            token_store=token_store,
            scopes=["https://www.googleapis.com/auth/calendar.events.readonly"],
        )
        self._client = HttpClient(
            base_url="https://www.googleapis.com/calendar/v3",
            timeout=15.0,
        )
        self._calendar_id = settings.calendar_id

    def _get_token(self) -> str:
        return self._oauth.get_access_token()

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        token = self._get_token()

        response = self._client.get(
            f"/calendars/{self._calendar_id}/events",
            params={
                "timeMin": now.isoformat(),
                "timeMax": now.replace(hour=23, minute=59, second=59).isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 50,
            },
            auth_token=token,
        )

        observations: list[ObservationCreate] = []
        events = response.get("items", [])

        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            start_dt = start.get("dateTime") or start.get("date", now.isoformat())
            end_dt = end.get("dateTime") or end.get("date", now.isoformat())

            observations.append(
                ObservationCreate(
                    timestamp=datetime.fromisoformat(start_dt.replace("Z", "+00:00")),
                    source="calendar",
                    category="schedule",
                    entity="event",
                    features={
                        "duration_minutes": _duration_minutes(start_dt, end_dt),
                    },
                    metadata={
                        "title": event.get("summary", "(No title)"),
                        "description": (event.get("description") or "")[:500],
                        "location": event.get("location", ""),
                        "creator": event.get("creator", {}).get("email", ""),
                        "status": event.get("status", "confirmed"),
                        "is_all_day": "date" in start,
                    },
                )
            )

        return observations


def _duration_minutes(start: str, end: str) -> float:
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return (e - s).total_seconds() / 60
    except (ValueError, TypeError):
        return 0.0
