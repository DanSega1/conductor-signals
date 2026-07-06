from __future__ import annotations

from datetime import UTC, datetime

from app.schemas import ObservationCreate
from app.storage import Repository


def test_store_and_retrieve_observation(repo: Repository) -> None:
    data = ObservationCreate(
        timestamp=datetime.now(UTC),
        source="test",
        category="test_category",
        entity="test_entity",
        features={"value": 42},
        metadata={"note": "hello"},
    )
    obs = repo.store_observation(data)
    assert obs.id is not None
    assert obs.source == "test"

    retrieved = repo.get_observations(source="test")
    assert len(retrieved) == 1
    assert retrieved[0].id == obs.id
    assert retrieved[0].features["value"] == 42


def test_get_timeline_returns_observations(repo: Repository) -> None:
    data = ObservationCreate(
        timestamp=datetime.now(UTC),
        source="test",
        category="test",
        entity="test",
    )
    repo.store_observation(data)

    timeline = repo.get_timeline()
    assert len(timeline) >= 1


def test_empty_timeline(repo: Repository) -> None:
    timeline = repo.get_timeline()
    assert timeline == []


def test_query_sql(repo: Repository) -> None:
    data = ObservationCreate(
        timestamp=datetime.now(UTC),
        source="sql_test",
        category="test",
        entity="widget",
        features={"count": 10},
    )
    repo.store_observation(data)

    df = repo.query_sql("SELECT source, entity FROM observations WHERE source = 'sql_test'")
    assert len(df) == 1
    assert df["source"][0] == "sql_test"
    assert df["entity"][0] == "widget"
