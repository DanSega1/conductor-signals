from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import respx

from app.collectors.base import CollectorInput
from app.collectors.oauth import OAuthTokenStore
from app.collectors.spotify import SpotifyCollector
from app.config import settings
from app.storage import DuckDBRepository

TOKEN = {
    "access_token": "test-access-token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "test-refresh-token",
    "created_at": datetime.now(UTC).isoformat(),
}

CURRENTLY_PLAYING = {
    "is_playing": True,
    "progress_ms": 60000,
    "item": {
        "name": "Test Track",
        "id": "track1",
        "duration_ms": 200000,
        "artists": [{"name": "Test Artist"}],
        "album": {"name": "Test Album"},
        "popularity": 75,
    },
}

RECENTLY_PLAYED = {
    "items": [
        {
            "track": {
                "name": "Recent Track",
                "id": "track2",
                "duration_ms": 180000,
                "artists": [{"name": "Recent Artist"}],
                "album": {"name": "Recent Album"},
                "popularity": 60,
            },
            "played_at": "2026-06-30T10:00:00.000Z",
            "context": {"type": "playlist"},
        }
    ]
}


def _set_env(monkeypatch: Any, data_dir: str) -> None:
    monkeypatch.setattr(settings, "spotify_client_id", "test-id")
    monkeypatch.setattr(settings, "spotify_client_secret", "test-secret")
    monkeypatch.setattr(settings, "data_dir", data_dir)


def _make_collector(db_path: Path, monkeypatch: Any) -> SpotifyCollector:
    data_dir = str(db_path.parent)
    _set_env(monkeypatch, data_dir)
    repo = DuckDBRepository(db_path)
    store = OAuthTokenStore(db_path.parent / "tokens" / "spotify.json")
    store.save(TOKEN)
    return SpotifyCollector(repository=repo)


@pytest.mark.respx(base_url="https://api.spotify.com")
def test_spotify_collector_current_and_recent(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r".*currently-playing").respond(json=CURRENTLY_PLAYING)
    respx_mock.get(path__regex=r".*recently-played.*").respond(json=RECENTLY_PLAYED)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    entities = {o.entity for o in observations}
    assert "currently_playing" in entities
    assert "track_played" in entities


@pytest.mark.respx(base_url="https://api.spotify.com")
def test_spotify_collector_no_current_playing(
    respx_mock: respx.MockRouter,
    db_path: Path,
    monkeypatch: Any,
) -> None:
    respx_mock.get(path__regex=r".*currently-playing").respond(status_code=204)
    respx_mock.get(path__regex=r".*recently-played.*").respond(json=RECENTLY_PLAYED)

    collector = _make_collector(db_path, monkeypatch)
    observations = collector.collect(CollectorInput())

    entities = {o.entity for o in observations}
    assert "currently_playing" not in entities
    assert "track_played" in entities
