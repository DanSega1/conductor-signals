from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.config import settings
from app.schemas import ObservationCreate


class HardcoverCollector(CollectorCapability):
    collector_source = "hardcover"
    collector_category = "media"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        self._client = HttpClient(
            base_url="https://api.hardcover.app/v1",
            headers={"Authorization": f"Bearer {settings.hardcover_api_key}"},
            timeout=15.0,
        )

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        observations: list[ObservationCreate] = []

        reading_response = self._client.get("/me/reading", params={"limit": 10})
        reading_data = reading_response.get("data", reading_response.get("reading", []))

        for item in reading_data:
            book = item.get("book", item.get("work", {}))
            observations.append(
                ObservationCreate(
                    timestamp=now,
                    source="hardcover",
                    category="media",
                    entity="currently_reading",
                    features={
                        "progress": item.get("progress", 0),
                        "pages_read": item.get("pages_read", 0),
                    },
                    metadata={
                        "title": book.get("title", "Unknown"),
                        "author": book.get("author", book.get("authors", "Unknown")),
                        "book_id": str(book.get("id", "")),
                        "status": item.get("status", "reading"),
                    },
                )
            )

        finished_response = self._client.get(
            "/me/reading",
            params={"limit": 10, "status": "finished"},
        )
        finished_data = finished_response.get(
            "data", finished_response.get("reading", [])
        )

        for item in finished_data[:5]:
            book = item.get("book", item.get("work", {}))
            date_finished = item.get("date_finished")
            timestamp = datetime.fromisoformat(date_finished) if date_finished else now
            observations.append(
                ObservationCreate(
                    timestamp=timestamp,
                    source="hardcover",
                    category="media",
                    entity="book_finished",
                    features={
                        "rating": item.get("rating", 0),
                        "pages_read": item.get("pages_read", 0),
                    },
                    metadata={
                        "title": book.get("title", "Unknown"),
                        "author": book.get("author", book.get("authors", "Unknown")),
                        "book_id": str(book.get("id", "")),
                    },
                )
            )

        return observations
