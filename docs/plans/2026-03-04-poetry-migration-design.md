# Poetry Migration Design

**Date:** 2026-03-04
**Status:** Approved

## Problem

`pip install -r requirements.txt` without a lockfile allows package upgrades that can trigger ChromaDB migrations, silently wiping embedded vector data. A chromadb version bump during a routine pip install destroyed the corpus embeddings today.

## Goal

Replace `requirements.txt` + root `.venv` with Poetry at the repo root. Poetry's lockfile (`poetry.lock`) pins every transitive dependency, preventing silent upgrades.

## Architecture

```
storyteller/
├── pyproject.toml          ← replaces storyteller_backend/requirements.txt
├── poetry.lock             ← generated; pins all transitive deps
├── storyteller_backend/
│   └── requirements.txt    ← deleted after migration verified
└── storyteller_frontend/   ← untouched
```

- Poetry venv lives in **global cache** (`~/.cache/pypoetry/virtualenvs/`)
- Root `.venv` is deleted
- Python constraint: `^3.12`

## Dependency Groups

**Main** (`[tool.poetry.dependencies]`): all runtime deps from requirements.txt
**Dev** (`[tool.poetry.group.dev.dependencies]`): pytest, pytest-asyncio, pytest-cov, httpx, black, ruff

Key notes:
- `chromadb = "1.3.7"` specified; `poetry lock` resolves whether this is achievable
- `duckdb` is NOT added (transitive dep that caused the original version conflict)
- `uvicorn` specified with `standard` extras

## Startup Commands (post-migration)

```bash
# Backend
cd storyteller_backend && poetry run uvicorn api.main:app --reload --port 8000

# Python
poetry run python

# Install deps (safe — uses lockfile)
poetry install

# Update a single dep (explicit, auditable)
poetry add package@version
```

CLAUDE.md is updated to reflect `poetry run` commands and remove `.venv` path references.

## Safety Note

**Never run `pip install -r requirements.txt` on this project.** ChromaDB upgrades can trigger database migrations that destroy embedded vector data. Always use `poetry install` (respects lockfile) or `poetry add <package>` (explicit, single package).
