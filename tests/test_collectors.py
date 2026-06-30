from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from engine.interfaces.task import TaskSubmission

from app.collectors import CollectorCapability
from app.collectors.base import CollectorInput
from app.engine import ConductorEngine
from app.schemas import ObservationCreate


class FakeCollector(CollectorCapability):
    @property
    def collector_source(self) -> str:
        return "test_source"

    @property
    def collector_category(self) -> str:
        return "test_category"

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        return [
            ObservationCreate(
                timestamp=datetime.now(UTC),
                source=self.collector_source,
                category=self.collector_category,
                entity="test_entity",
                features={"value": 1},
            )
        ]


def test_collector_capability_registers_and_runs(db_path: Path) -> None:
    engine = ConductorEngine(data_dir=db_path.parent)
    engine.register_collector(FakeCollector)

    submission = TaskSubmission(
        name="test-collect",
        capability="test_source",
        input={"force": False},
    )
    task = engine.supervisor.run_submission(submission)
    assert task.status == "completed"
    assert task.result is not None
    assert task.result.output["source"] == "test_source"
    assert task.result.output["collected"] == 1


def test_collector_capability_has_descriptor() -> None:
    from app.config import settings
    from app.storage import DuckDBRepository

    repo = DuckDBRepository(settings.database_path)
    collector = FakeCollector(repository=repo)
    desc = collector.descriptor
    assert desc.name == "test_source"
    assert "test_source" in desc.description
