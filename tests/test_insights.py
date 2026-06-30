from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.insights.generator import InsightGenerator
from app.schemas import ObservationCreate
from app.storage import DuckDBRepository


def _seed_observations(repo: DuckDBRepository) -> None:
    repo.store_observation(
        ObservationCreate(
            timestamp=datetime.fromisoformat("2026-06-30T12:00:00"),
            source="fitbit", category="health", entity="sleep",
            features={"duration_minutes": 420, "score": 85},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=datetime.fromisoformat("2026-06-25T12:00:00"),
            source="fitbit", category="health", entity="sleep",
            features={"duration_minutes": 360, "score": 70},
        )
    )
    repo.store_observation(
        ObservationCreate(
            timestamp=datetime.fromisoformat("2025-12-25T12:00:00"),
            source="spotify", category="media", entity="track_played",
            metadata={"track": "Xmas Song", "artist": "Holiday"},
        )
    )


def test_generate_returns_insights(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    _seed_observations(repo)
    generator = InsightGenerator(repository=repo)

    with patch.object(generator._llm, "complete") as mock:
        mock.return_value = (
            '{"insights": [{"title": "Sleep trend",'
            '"description": "Sleep dropped 14% versus last week.",'
            '"confidence": 0.8}]}'
        )
        results = generator.generate()

    assert len(results) == 1
    assert results[0].title == "Sleep trend"
    assert results[0].source == "llm"


def test_generate_and_store_stores_insight(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    _seed_observations(repo)
    generator = InsightGenerator(repository=repo)

    with patch.object(generator._llm, "complete") as mock:
        mock.return_value = (
            '{"insights": [{"title": "Test insight",'
            '"description": "Test desc.",'
            '"confidence": 0.9}]}'
        )
        count = generator.generate_and_store()

    assert count == 1


def test_generate_returns_empty_on_empty_observations(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    generator = InsightGenerator(repository=repo)

    with patch.object(generator._llm, "complete") as mock:
        results = generator.generate()

    assert results == []
    mock.assert_not_called()


def test_generate_returns_empty_on_empty_llm_response(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    _seed_observations(repo)
    generator = InsightGenerator(repository=repo)

    with patch.object(generator._llm, "complete") as mock:
        mock.return_value = ""
        results = generator.generate()

    assert results == []


def test_generate_handles_malformed_json(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    _seed_observations(repo)
    generator = InsightGenerator(repository=repo)

    with patch.object(generator._llm, "complete") as mock:
        mock.return_value = "not json at all"
        results = generator.generate()

    assert results == []
