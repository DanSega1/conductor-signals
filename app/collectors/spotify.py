from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.collectors.oauth import OAuth2Client, OAuthTokenStore
from app.config import settings
from app.logging import logger
from app.schemas import ObservationCreate


class SpotifyCollector(CollectorCapability):
    collector_source = "spotify"
    collector_category = "media"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        data_dir = Path(settings.data_dir)
        token_store = OAuthTokenStore(data_dir / "tokens" / "spotify.json")
        self._oauth = OAuth2Client(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            token_url="https://accounts.spotify.com/api/token",
            token_store=token_store,
            scopes=["user-read-recently-played", "user-read-currently-playing"],
        )
        self._client = HttpClient(
            base_url="https://api.spotify.com/v1",
            timeout=15.0,
        )

    def _get_token(self) -> str:
        return self._oauth.get_access_token()

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)
        observations: list[ObservationCreate] = []

        token = self._get_token()

        try:
            current = self._client.get(
                "/me/player/currently-playing",
                auth_token=token,
            )
            if current and current.get("item"):
                item = current["item"]
                observations.append(
                    ObservationCreate(
                        timestamp=now,
                        source="spotify",
                        category="media",
                        entity="currently_playing",
                        features={
                            "progress_ms": current.get("progress_ms", 0),
                            "duration_ms": item.get("duration_ms", 0),
                            "is_playing": current.get("is_playing", False),
                        },
                        metadata={
                            "track": item.get("name", "Unknown"),
                            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
                            "album": item.get("album", {}).get("name", ""),
                            "track_id": item.get("id", ""),
                        },
                    )
                )
        except Exception as e:
            logger.warning("spotify_current_playing_failed", error=str(e))

        try:
            recent = self._client.get(
                "/me/player/recently-played",
                params={"limit": 10},
                auth_token=token,
            )
            recent_items = recent.get("items", [])
            for entry in recent_items:
                track = entry.get("track", {})
                played_at = entry.get("played_at")
                observations.append(
                    ObservationCreate(
                        timestamp=(
                            datetime.fromisoformat(
                                played_at.replace("Z", "+00:00")
                            )
                            if played_at
                            else now
                        ),
                        source="spotify",
                        category="media",
                        entity="track_played",
                        features={},
                        metadata={
                            "track": track.get("name", "Unknown"),
                            "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                            "album": track.get("album", {}).get("name", ""),
                            "track_id": track.get("id", ""),
                            "duration_ms": track.get("duration_ms", 0),
                            "popularity": track.get("popularity", 0),
                            "context": entry.get("context", {}).get("type", ""),
                        },
                    )
                )
        except Exception as e:
            logger.warning("spotify_recently_played_failed", error=str(e))

        return observations
