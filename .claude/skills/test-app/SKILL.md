---
name: test-app
description: "Run the app behavior test suite. Drives Playwright MCP through the Storyteller app, exercises each behavior in the manifest, and produces a timestamped pass/fail report. Pass a test number to run a single test (e.g. /test-app 9)."
---

# App Behavior Test Suite Runner

Run the Storyteller app behavior test suite defined in `validation/app-behaviors.md`.

## Invocation

- `/test-app` — run all tests
- `/test-app N` — run only test N (skip dependency checks, useful for test-fix-retest loops)

If an argument is provided, parse it as a test id. Run only that single test — skip Phase 4 dependency checking (the user is explicitly targeting this test). Still produce a report, but it will contain only the one result entry.

## What This Skill Does

1. Ensures backend (port 8000) and frontend (port 3000) are running
2. Opens a headless browser to http://localhost:3000
3. Reads the behavior manifest and parses test ids, dependencies, and instructions
4. Executes tests via Playwright MCP (all tests, or a single specified test)
5. Produces a timestamped report in `validation/results/`

## Permissions

This skill performs many automated actions. To avoid blocking on permission prompts:
- **Do NOT ask for permission** to create directories (mkdir), write files, or run bash commands.
- **Do NOT ask for permission** for any Playwright MCP action (navigate, click, type, snapshot, screenshot, wait, evaluate, etc.).
- Proceed autonomously through all phases. Only stop if a server fails to start.

## Procedure

### Phase 1: Server Readiness

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

Wait up to 15 seconds for both to become healthy. If either fails to start, abort the test run and report the failure.

### Phase 2: Browser Setup

Navigate Playwright to `http://localhost:3000`. Take a snapshot to confirm the app loaded (look for "Story Controls" heading).

### Phase 3: Parse Manifest

Read `validation/app-behaviors.md`. For each test, extract:
- **id**: the number from the `## N.` heading
- **title**: the text after the number in the heading
- **depends_on**: list of test ids from the `depends_on:` line (`none` = no dependencies)
- **status**: if a `status:` line is present (e.g., `status: unimplemented`), note it
- **instructions**: all remaining text — the natural-language goal and hints

If running a single test (`/test-app N`), locate only that test's entry.

### Phase 4: Execute Tests

Create the results directory:
```bash
mkdir -p validation/results/$(date +%Y-%m-%d-%H%M%S)
```

For each test in order (or the single targeted test):

1. **Check dependencies** (skip this step if running a single test via `/test-app N`): If any dependency has status FAIL or SKIP, mark this test as ⊘ SKIP with reason "blocked by: N, M". Note: transitivity is handled naturally — a skipped test causes its dependents to skip too, cascading through the chain.

2. **Execute**: Follow the natural-language instructions using Playwright MCP tools:
   - Use `browser_snapshot` to read page state (preferred over screenshots for assertions)
   - Use `browser_click`, `browser_fill_form`, `browser_type`, `browser_press_key` to interact
   - Use `browser_wait_for` when waiting for elements to appear
   - Use `browser_navigate` for page reloads

3. **Timeouts**:
   - Streaming operations (SSE story generation): wait up to **60 seconds**. Use `browser_wait_for` with `time: 35` then check status via `browser_snapshot`. If still streaming, wait another 25 seconds.
   - UI interactions (dropdowns, buttons, panels): wait up to **10 seconds**

4. **Judge**: Based on what you observe in snapshots, determine if the expected behavior occurred.
   - For `status: unimplemented` tests: a failure is expected. Still report what happened but mark as ✗ FAIL (expected).

5. **On failure**: Take a screenshot and save it to the results folder. Zero-pad the test id to 3 digits:
   ```
   validation/results/<timestamp>/<NNN>-<title-slug>.png
   ```
   Example: `validation/results/2026-03-14-163045/003-select-corpus.png`

### Phase 5: Write Report

Save `validation/results/<timestamp>/results.md` with this format:

```markdown
# App Behavior Test Report
Run: YYYY-MM-DD HH:MM:SS
Browser: headless Chromium 1440x900

## Summary
Total: N | Passed: N | Failed: N | Skipped: N

## Results

### 1. Create username "agent-tester" — ✓ PASS
[Description of what was done and what was observed]

### N. Test title — ✗ FAIL
[Description of what was done, what was observed, how it differed from expectation]
See: NNN-title-slug.png

### N. Test title — ⊘ SKIP (blocked by: X, Y)
[No action taken — dependency X failed]
```

Each result entry MUST include:
- Test id and title
- Status symbol: ✓ PASS, ✗ FAIL, or ⊘ SKIP
- Natural-language description of what the agent did and observed
- Screenshot filename on failure

### Phase 6: Summary

After writing the report, output a brief summary to the user:
- Path to the results folder
- Total / passed / failed / skipped counts
- List of any failures with one-line descriptions

Do NOT shut down the servers when done.