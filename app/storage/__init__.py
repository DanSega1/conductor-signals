from app.storage.base import AbstractRepository
from app.storage.duckdb import DuckDBRepository

Repository = DuckDBRepository

__all__ = [
    "AbstractRepository",
    "DuckDBRepository",
    "Repository",
]
