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
cd storyteller_backend && ../.venv/bin/uvicorn api.main:app --reload --port 8000
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
├── storyteller_backend/    # FastAPI app
│   ├── api/                # Routes, main.py entry point
│   ├── services/           # LangGraph story generation
│   ├── models/             # Pydantic models
│   └── .venv/              # ← Use storyteller/.venv (root), not this one
├── storyteller_frontend/   # React/Vite app
│   └── src/
│       ├── components/     # graph/, dropdowns/, debug/
│       ├── hooks/          # useSSE, useELKLayout, useLocalStorage
│       ├── services/       # api.ts — all backend calls
│       └── context/        # AppContext — global state
├── .mcp.json               # Playwright MCP config
├── CLAUDE.md               # This file
└── docs/plans/             # Design docs and implementation plans
```

---

## Python Environment

Root `.venv` uses Python 3.12. Always activate or reference it explicitly:
```bash
../.venv/bin/python      # from storyteller_backend/
./.venv/bin/python       # from repo root
```

There is also a `storyteller_backend/.venv_bk` — ignore this, it is a backup.
