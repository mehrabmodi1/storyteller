# Storyteller — Claude Code Guide

## Project Overview

Interactive storytelling app. Users create branching narrative journeys visualised as a graph.

- **Backend:** FastAPI + uvicorn (port 8000) — Python 3.12, LangGraph/LangChain, ChromaDB
- **Frontend:** React 18 + Vite (port 3000) — TypeScript, ReactFlow, Tailwind CSS

---

## Starting the Dev Servers

Always start both servers as background processes before interacting with the app.

**Backend (port 8000):**
```bash
cd storyteller_backend && poetry run python -m api.main
```
If `poetry run` fails with `No such file or directory: 'python'` (common in sandboxed shells), resolve the venv python directly:
```bash
VENV_PYTHON=$(poetry config virtualenvs.path)/$(ls $(poetry config virtualenvs.path) | grep storyteller)/bin/python
cd storyteller_backend && $VENV_PYTHON -m api.main
```

**Frontend (port 3000, HMR enabled):**
```bash
cd storyteller_frontend && npm run dev
```

**Verify backend is up:**
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", ...}`

Frontend is ready when port 3000 responds.

---

## Browser Automation (Playwright MCP)

Playwright MCP is configured in `.mcp.json`. It is available automatically in every Claude Code session for this project — no setup needed.

Use browser tools to navigate, screenshot, click, and fill forms:
- Navigate to `http://localhost:3000` after starting servers
- Take screenshots to verify UI state
- Vite HMR means code edits reflect in the browser immediately — no server restart needed

---

## Project Structure

```
storyteller/
├── pyproject.toml          # Poetry dependency management
├── poetry.lock             # Locked dependency tree — do not edit manually
├── storyteller_backend/    # FastAPI app
│   ├── api/                # main.py entry point, routes/ subdir
│   ├── services/           # LangGraph story generation
│   ├── models/             # Pydantic models
│   └── data/               # corpus_registry.json (chroma_db is at repo root data/)
├── storyteller_frontend/   # React/Vite app
│   └── src/
│       ├── components/     # graph/, dropdowns/, debug/
│       ├── hooks/          # useSSE, useELKLayout, useLocalStorage
│       ├── services/       # api.ts — all backend calls
│       └── context/        # AppContext — global state
├── data/                   # ChromaDB vector databases (NOT gitignored, DO NOT DELETE)
├── .mcp.json               # Playwright MCP config
├── CLAUDE.md               # This file
└── docs/plans/             # Design docs and implementation plans
```

---

## Python / Poetry Environment

Dependencies are managed with **Poetry 2.x**. The venv lives in Poetry's global cache.

```bash
poetry install          # install all deps (respects lockfile — safe)
poetry add <package>    # add a new dep (explicit, auditable)
poetry run python       # run Python in the project env
poetry run pytest       # run tests
```

**NEVER run `pip install -r requirements.txt` or `pip install` to upgrade packages.**
ChromaDB version changes trigger database migrations that **permanently destroy embedded vector data** in `data/chroma_db/`. Always use `poetry install` or `poetry add`.
