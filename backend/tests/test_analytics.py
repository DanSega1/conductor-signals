from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from app.analytics.engine import AnalyticsEngine
from app.schemas import ObservationCreate
from app.storage import DuckDBRepository


@pytest.fixture
def seeded_repo(db_path: Path) -> DuckDBRepository:
    repo = DuckDBRepository(db_path)
    ts = datetime.fromisoformat("2026-06-30T12:00:00")
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="fitbit", category="health", entity="sleep",
            features={"duration_minutes": 420, "score": 85},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="fitbit", category="health", entity="hrv",
            features={"daily_rmssd": 42.5},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="fitbit", category="health", entity="activity",
            features={"steps": 8500},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="spotify", category="media", entity="track_played",
            metadata={"track": "Test Song", "artist": "Test Artist"},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="weather", category="environment",
            entity="current_conditions",
            features={"temperature": 22.5, "humidity": 65},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=ts, source="calendar", category="schedule", entity="event",
            metadata={"title": "Meeting"},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=datetime.fromisoformat("2025-12-25T12:00:00"),
            source="spotify", category="media", entity="track_played",
            metadata={"track": "Xmas Song", "artist": "Xmas Artist"},
        )
    )
    return repo


def test_period_summary(seeded_repo: DuckDBRepository) -> None:
    engine = AnalyticsEngine(seeded_repo)
    df = engine.period_summary(days=365)
    assert isinstance(df, pl.DataFrame)
    assert not df.is_empty()


def test_period_comparison(seeded_repo: DuckDBRepository) -> None:
    engine = AnalyticsEngine(seeded_repo)
    df = engine.period_comparison(entity="activity", days=7)
    assert isinstance(df, pl.DataFrame)
    assert "period" in df.columns


def test_year_over_year(seeded_repo: DuckDBRepository) -> None:
    engine = AnalyticsEngine(seeded_repo)
    df = engine.year_over_year(entity="activity", feature="steps")
    assert isinstance(df, pl.DataFrame)
    assert "steps" in df.columns
    assert "year" in df.columns


def test_recurring_patterns(seeded_repo: DuckDBRepository) -> None:
    engine = AnalyticsEngine(seeded_repo)
    df = engine.recurring_patterns(entity="track_played", feature="duration_ms")
    assert isinstance(df, pl.DataFrame)
    assert "month" in df.columns
    assert "day_of_week" in df.columns
    assert "avg_value" in df.columns


def test_recent_observations(seeded_repo: DuckDBRepository) -> None:
    engine = AnalyticsEngine(seeded_repo)
    result = engine.recent_observations(limit=10)
    assert isinstance(result, pl.DataFrame)
    assert result.height > 0
    assert "source" in result.columns
