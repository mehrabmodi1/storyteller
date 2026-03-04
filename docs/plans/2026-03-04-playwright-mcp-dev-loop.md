# Playwright MCP Dev/Test Feedback Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Configure Playwright MCP and document server startup so any Claude Code agent can run the full stack and visually interact with the frontend browser.

**Architecture:** A `.mcp.json` at the repo root registers the Playwright MCP server project-wide. A `CLAUDE.md` at the repo root gives any agent the server startup commands and context needed to begin work without reading through the codebase.

**Tech Stack:** `@playwright/mcp` (npx, no install needed), FastAPI/uvicorn (Python 3.12 `.venv`), Vite (npm)

---

### Task 1: Create `.mcp.json`

**Files:**
- Create: `.mcp.json` (repo root)

**Step 1: Create the file**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    }
  }
}
```

Save to: `/path/to/storyteller/.mcp.json`

**Step 2: Validate JSON**

Run:
```bash
python3 -c "import json; json.load(open('.mcp.json')); print('valid')"
```
Expected: `valid`

**Step 3: Commit**

```bash
git add .mcp.json
git commit -m "feat: add Playwright MCP config for browser automation"
```

---

### Task 2: Create `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md` (repo root)

**Step 1: Create the file**

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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with server startup and project guide for agents"
```

---

### Task 3: Verify Playwright MCP is Registered

**Step 1: Check MCP server list**

Run:
```bash
claude mcp list
```
Expected output includes `playwright` server entry.

**Step 2: Smoke-test browser tools (optional, in-session)**

If in a Claude Code session with MCP active, use the `browser_navigate` tool to open `http://example.com` and `browser_screenshot` to confirm a screenshot is returned. This confirms the full chain works.

**Step 3: Commit memory note**

Save a memory note documenting server commands and Playwright MCP availability for this project (see MEMORY.md).
