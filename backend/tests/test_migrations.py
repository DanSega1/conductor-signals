from __future__ import annotations

from pathlib import Path

from app.storage.duckdb import DuckDBRepository
from app.storage.migrations import MIGRATIONS


def test_migrations_run_on_init(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    try:
        applied = repo._get_applied_versions()
        expected = {v for v, _, _ in MIGRATIONS}
        assert applied == expected, (
            f"Expected migrations {expected}, got {applied}"
        )
    finally:
        repo.close()


def test_migrations_are_idempotent(db_path: Path) -> None:
    repo1 = DuckDBRepository(db_path)
    repo1.close()

    repo2 = DuckDBRepository(db_path)
    try:
        applied = repo2._get_applied_versions()
        expected = {v for v, _, _ in MIGRATIONS}
        assert applied == expected
    finally:
        repo2.close()


def test_features_table_exists(db_path: Path) -> None:
    repo = DuckDBRepository(db_path)
    try:
        tables = repo.query_sql(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        )
        table_names = tables["table_name"].to_list()
        assert "features" in table_names
    finally:
        repo.close()
