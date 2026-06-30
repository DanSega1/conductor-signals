# Development

## Prerequisites

- Python 3.14+
- Docker / Docker Compose (optional)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Lint & Type Check

```bash
ruff check .
ruff format --check .
mypy app/
```

## Tests

```bash
pytest
pytest --cov=app
pytest --cov=app --cov-report=html
```

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## Run API

```bash
uvicorn app.api.app:app --reload
```

## Docker

```bash
docker compose up --build
```
