# Conductor Observatory — Architecture

## Overview

Lightweight observability platform for one person running on a Raspberry Pi 5.

Collects metadata from trusted services, normalizes into a timeline, derives metrics, and provides explainable insights via SQL and LLM-assisted querying.

## Data Flow

```
Collectors
  |
  v
Normalizer
  |
  v
Observation Store
  |
  v
DuckDB
  |
  v
Analytics (SQL + Polars)
  |
  v
Insights
  |
  v
AI Query Layer (LLM summarizes, does NOT discover facts)
  |
  v
Notifications (Discord / Telegram / Email)
```

## Storage Layer

The storage layer provides an abstract interface (`AbstractRepository`) implemented by `DuckDBRepository`.

### Architecture

```
app/storage/
  base.py         — AbstractRepository ABC
  duckdb.py       — DuckDBRepository implementation
  migrations.py   — Versioned schema migrations
  repository.py   — Alias for DuckDBRepository
```

### Migrations

Migrations are versioned, idempotent SQL steps stored in `migrations.py`. On connect, `DuckDBRepository` checks a `_migrations` table and applies any pending migrations.

Current migrations:
- **v1**: Create `observations` and `insights` tables with indexes
- **v2**: Create `features` table for normalized feature storage

### Storage Strategy

| Layer | Retention | Format |
|-------|-----------|--------|
| Raw payloads | 30-90 days | JSON |
| Observations | Forever | DuckDB / Parquet |
| Derived metrics | Forever | Parquet |
| Insights | Forever | DuckDB / Parquet |

### Key Classes

- `AbstractRepository` — ABC with `store_observation`, `get_observations`, `get_timeline`, `query_sql`, `store_parquet`, `read_parquet`, `close`
- `DuckDBRepository` — DuckDB-backed implementation with schema migrations
- `Repository` — Convenience alias for `DuckDBRepository`

## Key Principles

- Metadata first — avoid storing raw data
- Every insight must be reproducible through SQL
- LLM explains, does NOT discover facts
- Deterministic analytics only — no ML
- Local-first, cloud only for AI providers and external APIs

## Directory Layout

```
app/          — Application code
  collectors/ — Data source integrations
  analytics/  — SQL + Polars analytics
  storage/    — DuckDB + Parquet repositories
  schemas/    — Pydantic models
  api/        — FastAPI endpoints
  workflows/  — Conductor workflow definitions
data/         — Persistent data
  raw/        — Per-source raw payloads
  derived/    — Daily/weekly rollups
  analytics/  — Analytical outputs
  insights/   — Generated insights
tests/        — Test suite
docker/       — Docker build files
docs/         — Documentation
scripts/      — Utility scripts
```
