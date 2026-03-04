# Design: Playwright MCP Dev/Test Feedback Loop

**Date:** 2026-03-04
**Status:** Approved

## Goal

Enable any Claude Code agent working in this repo to:
1. Start the backend and frontend servers
2. Visually interact with the running app via a browser (screenshots, clicks, form fills)
3. Make code changes and verify them via Vite HMR — without restarting servers

## Architecture

```
Claude Code session
├── Bash tool          → start/stop backend + frontend as background processes
├── Playwright MCP     → full browser automation (navigate, screenshot, click, type)
└── Edit/Write tools   → code changes that Vite HMR picks up automatically
```

### Components

**Playwright MCP (`@playwright/mcp`)**
- Configured in `.mcp.json` at repo root (project-scoped, git-tracked)
- Runs in headless mode by default
- Provides browser tools: `browser_navigate`, `browser_screenshot`, `browser_click`, `browser_type`, `browser_snapshot`, etc.
- Available automatically to any Claude Code agent opening this project

**Backend server**
- FastAPI + uvicorn on port 8000
- Uses the root `.venv` (Python 3.12)
- `--reload` flag enables hot-reload on Python file changes
- Health check: `GET http://localhost:8000/health`

**Frontend server**
- Vite dev server on port 3000
- HMR enabled — React component changes reflect immediately in browser
- Proxies `/api` to backend at `localhost:8000`

## Startup Commands

```bash
# Backend
cd storyteller_backend && ../.venv/bin/uvicorn api.main:app --reload --port 8000

# Frontend
cd storyteller_frontend && npm run dev
```

Both run as background processes. Poll health endpoints before interacting.

## The Feedback Loop

```
receive task
    ↓
start servers (background) → verify health
    ↓
playwright: navigate to http://localhost:3000
playwright: screenshot → assess current state
    ↓
interact (click choices, fill prompts, trigger streaming, etc.)
    ↓
works? → done / report
bug or change needed? → edit file → Vite HMR auto-reloads
    ↓
playwright: screenshot → verify
    ↓
repeat
```

## Configuration Files

### `.mcp.json` (repo root)
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

### `CLAUDE.md` additions
- Document server startup commands
- Note Playwright MCP availability
- Note health check endpoint

## Out of Scope

- Automated test suite (Jest/Vitest) — separate concern
- CI/CD integration — future work
- Persistent server management (servers start per-session as needed)
