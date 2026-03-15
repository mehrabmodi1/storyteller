---
name: fix-tests
description: "Read the latest test report, fix all failing tests (bugs and unimplemented features), verify each fix, then run the full suite for regression safety."
---

# Fix Failing Tests

Read the most recent test report, fix every failing test, and verify the fixes.

Tests are feature specs. A `status: unimplemented` test is a feature request — implement the missing feature, don't skip it.

## Invocation

- `/fix-tests` — fix all failures from the latest full test report

## Permissions

This skill performs many automated actions. To avoid blocking on permission prompts:
- **Do NOT ask for permission** to create directories, write files, or run bash commands.
- **Do NOT ask for permission** for any Playwright MCP action (navigate, click, type, snapshot, screenshot, wait, evaluate, etc.).
- **Do NOT ask for permission** to edit code files (frontend or backend).
- Proceed autonomously through all phases. Only stop if a server fails to start or all retries are exhausted.

## Procedure

### Phase 1: Read Report

1. Find the most recent full test report:
   ```bash
   ls -d validation/results/*/ | sort | tail -1
   ```
   Read `results.md` from that directory.

2. Parse each test entry. The format is:
   ```
   ### N. Test title — ✗ FAIL
   [description]
   ```
   or:
   ```
   ### N. Test title — ✗ FAIL (expected)
   [description]
   ```

3. Build a failure list: every test with `✗ FAIL` in its status line (including `FAIL (expected)`). Record the test id, title, and failure description.

4. If no failures found, output "All tests passing — nothing to fix." and exit.

5. Output the failure list to the user before proceeding.

### Phase 2: Fix Loop

Process each failure sequentially.

#### Step 2.1: Server Readiness (once, at start)

Check if servers are already running:
```bash
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

If the backend is not responding, start it:
```bash
cd storyteller_backend && poetry run python -m api.main > /tmp/storyteller_backend.log 2>&1 &
```

If the frontend is not responding, start it:
```bash
cd storyteller_frontend && npm run dev > /tmp/storyteller_frontend.log 2>&1 &
```

Wait up to 15 seconds for both to become healthy. If either fails to start, abort and report the failure.

#### Step 2.2: For Each Failure (up to 3 attempts per test)

**a) Gather context:**
- Read the failure description from the test report (what was observed, how it differed from expectation)
- Read the test's full instructions from `validation/app-behaviors.md` (what the test expects)
- Explore the relevant codebase to understand the current implementation:
  - Frontend code: `storyteller_frontend/src/` (React components in `components/`, hooks in `hooks/`, services in `services/`, context in `context/`)
  - Backend code: `storyteller_backend/` (FastAPI routes in `api/routes/`, services in `services/`, models in `models/`)

**b) Implement the fix or feature:**
- For bug fixes: identify the root cause and fix it
- For unimplemented features (`status: unimplemented` in manifest): implement the feature as described by the test instructions
- Edit frontend and/or backend code as needed
- Keep changes minimal and focused — fix the specific issue, don't refactor surrounding code

**c) Handle backend code changes:**
- Frontend changes are picked up automatically by Vite HMR — no restart needed.
- **If any file under `storyteller_backend/` was edited**, restart the backend before retesting:
  ```bash
  pkill -f "python -m api.main" 2>/dev/null; sleep 1
  cd storyteller_backend && poetry run python -m api.main > /tmp/storyteller_backend.log 2>&1 &
  ```
  Wait up to 10 seconds for `curl -s http://localhost:8000/health` to succeed.

**d) Verify with single-test rerun:**
- Navigate Playwright to `http://localhost:3000`
- Wait for the app to load (look for "Story Controls" heading)
- **Replay prerequisite steps:** If the target test has `depends_on` dependencies, replay the necessary setup actions from those dependency tests to establish the required app state. For example:
  - To verify test 10 (Cancel choice node), first replay test 1 (create/select username), test 2 (select persona), test 3 (select corpus), test 5 (start journey, wait for stream), and test 9 (click a choice node to expand it)
  - Only replay the minimum chain needed — follow the `depends_on` path
- Execute the target test's instructions using Playwright MCP tools:
  - Use `browser_snapshot` to read page state (preferred over screenshots for assertions)
  - Use `browser_click`, `browser_fill_form`, `browser_type`, `browser_press_key` to interact
  - Use `browser_wait_for` when waiting for elements to appear
  - Use `browser_navigate` for page reloads
- **Timeouts:**
  - Streaming operations (SSE story generation): wait up to **60 seconds**. Use `browser_wait_for` with `time: 35` then check status via `browser_snapshot`. If still streaming, wait another 25 seconds.
  - UI interactions (dropdowns, buttons, panels): wait up to **10 seconds**
- Judge pass/fail based on observed behavior

**e) On failure (retry):**
- If the test still fails, analyze what went wrong
- Try a different approach
- Up to **3 attempts total** per test
- After 3 failed attempts, log as **unresolved** and move to the next failure

**f) Reset between tests:**
- Reload the page after each test verification to clear app state before the next fix cycle

### Phase 3: Full Suite Run

After all individual fixes are done, run the complete test suite to catch regressions.

Follow the exact same procedure as the `test-app` skill (reference `.claude/skills/test-app/SKILL.md`):

1. **Server readiness** — curl health checks, start if needed
2. **Browser setup** — navigate to `http://localhost:3000`, confirm app loaded
3. **Parse manifest** — read `validation/app-behaviors.md`, extract all tests
4. **Execute all tests** sequentially with dependency-based skip logic:
   - If a dependency failed or was skipped → mark as ⊘ SKIP
   - Otherwise execute via Playwright MCP, judge pass/fail
   - On failure: save screenshot to results folder
5. **Write report** — save to `validation/results/<timestamp>/results.md` with this format:
   ```markdown
   # App Behavior Test Report
   Run: YYYY-MM-DD HH:MM:SS
   Browser: headless Chromium 1440x900

   ## Summary
   Total: N | Passed: N | Failed: N | Skipped: N

   ## Results

   ### N. Test title — ✓ PASS / ✗ FAIL / ⊘ SKIP
   [Description of what was done and observed]
   ```

6. **Compare** against the original failure list from Phase 1:
   - Tests that were failing and now pass → **fixed**
   - Tests that were failing and still fail → **unresolved**
   - Tests that were passing and now fail → **regressions**

### Phase 4: Summary

Output a final summary to the user:

```
## Fix-Tests Summary

**Fixed:** N tests
- Test X: [title] — [one-line description of fix]

**Unresolved:** N tests
- Test X: [title] — [why it couldn't be fixed]

**Regressions:** N tests
- Test X: [title] — [was passing, now failing]

**Modified files:**
- path/to/file1
- path/to/file2

**New test report:** validation/results/<timestamp>/results.md
```

Do NOT shut down the servers when done.