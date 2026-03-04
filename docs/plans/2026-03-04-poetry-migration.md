# Poetry Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace `requirements.txt` + root `.venv` with Poetry at the repo root, locking all transitive dependencies to prevent silent upgrades that can destroy ChromaDB data.

**Architecture:** A single `pyproject.toml` at the repo root replaces `storyteller_backend/requirements.txt`. Poetry 2.1.2 manages the venv in its global cache (`~/.cache/pypoetry/`). `poetry lock` resolves all version conflicts (including chromadb/duckdb). Startup commands switch to `poetry run`.

**Tech Stack:** Poetry 2.1.2 (`/Users/mehrabmodi/.local/bin/poetry`), Python 3.12

---

### Task 1: Create `pyproject.toml` at repo root

**Files:**
- Create: `pyproject.toml` (repo root)

**Step 1: Create the file**

Create `/Users/mehrabmodi/Documents/projects/storyteller_final/storyteller/pyproject.toml` with this exact content:

```toml
[tool.poetry]
name = "storyteller-backend"
version = "0.1.0"
description = "Storyteller interactive narrative backend"
authors = []
package-mode = false

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "0.115.5"
uvicorn = {version = "0.34.0", extras = ["standard"]}
sse-starlette = "2.2.1"
python-multipart = "0.0.20"
pydantic = "2.10.3"
pydantic-settings = "2.6.1"
python-dotenv = "1.0.1"
langchain = "0.3.13"
langchain-openai = "0.2.14"
langchain-core = "0.3.28"
langgraph = "0.2.59"
openai = "1.58.1"
chromadb = "1.3.7"
chroma-migrate = "0.0.7"
rank-bm25 = "0.2.2"
networkx = "3.4.2"

[tool.poetry.group.dev.dependencies]
pytest = "8.3.4"
pytest-asyncio = "0.24.0"
pytest-cov = "6.0.0"
httpx = "0.28.1"
black = "24.10.0"
ruff = "0.8.4"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 2: Validate TOML is parseable**

Run:
```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('valid')"
```
Expected: `valid`

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml for Poetry dependency management"
```

---

### Task 2: Run `poetry lock`

**Files:**
- Create: `poetry.lock` (generated)

**Step 1: Run poetry lock from repo root**

```bash
poetry lock
```

This resolves all transitive dependencies. It may take 1-2 minutes.

Expected: `poetry.lock` file created, no errors.

If chromadb 1.3.7 cannot be resolved, Poetry will report the conflict clearly. In that case, check which version IS resolvable:
```bash
poetry add chromadb --dry-run 2>&1 | head -20
```
Then update `pyproject.toml` to use that version and re-run `poetry lock`.

**Step 2: Verify lockfile was created**

```bash
wc -l poetry.lock
```
Expected: several thousand lines (lockfiles are large).

**Step 3: Commit**

```bash
git add poetry.lock
git commit -m "chore: add poetry.lock with resolved dependency tree"
```

---

### Task 3: Run `poetry install`

**Step 1: Install all dependencies**

```bash
poetry install
```

Expected: packages installed into Poetry's global cache, no errors.

**Step 2: Verify key imports work**

```bash
poetry run python -c "import fastapi, chromadb, langchain, pydantic_settings; print('all imports OK')"
```
Expected: `all imports OK`

**Step 3: Check chromadb version matches what was requested**

```bash
poetry run python -c "import chromadb; print(chromadb.__version__)"
```
Note the installed version. If different from 1.3.7, that is acceptable — Poetry found the highest compatible version. What matters is it's locked and won't change again.

---

### Task 4: Verify backend starts correctly

**Step 1: Start backend with poetry run**

From repo root, run in background:
```bash
cd storyteller_backend && poetry run uvicorn api.main:app --reload --port 8000
```

**Step 2: Health check**

```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", ...}`

**Step 3: Check personas endpoint (should return 6 personas)**

```bash
curl http://localhost:8000/api/personas | python3 -m json.tool | grep '"name"'
```
Expected: 6 persona names printed.

**Step 4: Check corpuses endpoint (this was crashing before)**

```bash
curl http://localhost:8000/api/corpuses
```
Note the result — it may still error due to the separate chroma_db_path issue (that is a different bug, not part of this task). What we're verifying here is that the server starts and basic routes work.

**Step 5: Stop the backend**

Kill the background process before proceeding.

---

### Task 5: Delete root `.venv` and `requirements.txt`

Only do this after Task 4 confirms the backend starts successfully.

**Step 1: Delete the root venv**

```bash
rm -rf /Users/mehrabmodi/Documents/projects/storyteller_final/storyteller/.venv
```

**Step 2: Delete requirements.txt**

```bash
rm storyteller_backend/requirements.txt
```

**Step 3: Verify nothing breaks**

```bash
poetry run python -c "import fastapi; print('still works')"
```
Expected: `still works`

**Step 4: Commit**

```bash
git add -u
git commit -m "chore: remove requirements.txt and root .venv after Poetry migration"
```

---

### Task 6: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (repo root)

**Step 1: Update the file**

Replace the entire CLAUDE.md content with:

```markdown
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
cd storyteller_backend && poetry run uvicorn api.main:app --reload --port 8000
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

**⚠️ NEVER run `pip install -r requirements.txt` or `pip install` to upgrade packages.**
ChromaDB version changes trigger database migrations that **permanently destroy embedded vector data** in `data/chroma_db/`. Always use `poetry install` or `poetry add`.
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for Poetry — replace .venv paths, add safety warning"
```

---

### Task 7: Update `.gitignore`

**Step 1: Check current .gitignore**

Read `.gitignore` and verify it contains `data/` (to keep chroma_db out of git). Also ensure `.venv` is listed (in case Poetry ever creates one in-project).

**Step 2: Add `.venv` if not already present**

```bash
grep -q "^\.venv" .gitignore || echo ".venv" >> .gitignore
```

**Step 3: Commit if changed**

```bash
git diff .gitignore
# If changed:
git add .gitignore
git commit -m "chore: ensure .venv is gitignored"
```
