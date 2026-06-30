from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from pytest import TempPathFactory

from app.storage import Repository


@pytest.fixture
def db_path(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("data") / "test.duckdb"


@pytest.fixture
def repo(db_path: Path) -> Generator[Repository]:
    repository = Repository(db_path)
    yield repository
    repository.close()
