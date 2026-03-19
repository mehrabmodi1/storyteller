---
name: fix-tests
description: "Read the latest test report, fix all failing tests (bugs and unimplemented features), verify each fix, then run the full suite for regression safety."
---

# Fix Failing Tests

Read the most recent test report, fix every failing test, and verify the fixes.

Tests are feature specs. A `status: unimplemented` test is a feature request — implement the missing feature, don't skip it.

## Invocation

- `/fix-tests` — fix all failures from the latest full test report

### Ralph Loop (continuous iteration)

For fully autonomous iteration until all tests pass:

```
/ralph-loop "Run /fix-tests. Output <promise>ALL TESTS PASSING</promise> when the full suite run in Phase 3 shows zero failures." --max-iterations 5
```

Each ralph iteration starts fresh context but reads the latest test report from disk, so progress carries across iterations automatically. Use this when context gets crowded or fixes span multiple iteration cycles.

## Permissions

This skill performs many automated actions. To avoid blocking on permission prompts:
- **Do NOT ask for permission** to create directories, write files, or run bash commands.
- **Do NOT ask for permission** for any Playwright MCP action (navigate, click, type, snapshot, screenshot, wait, evaluate, etc.).
- **Do NOT ask for permission** to edit code files (frontend or backend).
- Proceed autonomously through all phases. Only stop if a server fails to start or all retries are exhausted.

## CRITICAL: Interaction Rules — Simulate a Real User

The agent MUST interact with the app exactly as a human user would. This is non-negotiable.

### Assertions: Screenshots Only

- **NEVER use `browser_snapshot` to judge whether a test passed or failed.** Snapshots read the DOM/accessibility tree directly, which can show state that isn't visually rendered or hide bugs that are visually apparent.
- **ALWAYS use `browser_take_screenshot`** and visually inspect the screenshot image to determine what the app looks like and whether the expected behavior occurred.
- `browser_snapshot` may ONLY be used for one purpose: **finding element `ref` values** needed to target clicks, typing, and other interactions. Never use it for assertions.

### Text Input: Real Keystrokes

- **NEVER use `browser_type` with `slowly: false` (the default) or `browser_fill_form`** for typing into text fields. These methods set the value atomically, bypassing keystroke event handlers and masking real input bugs.
- **ALWAYS use `browser_type` with `slowly: true`** to type one character at a time, triggering the same key events a real user would.
- Exception: for long prompts (>100 chars), you may use regular `browser_type` for speed, but then verify the field content via screenshot.

### Clicking and Navigation

- Use `browser_click` for all interactions — this simulates real mouse clicks.
- Use `browser_press_key` for keyboard actions (Enter, Escape, etc.).
- Use `browser_navigate` for page loads/reloads.
- Do NOT use `browser_evaluate` to programmatically trigger actions (e.g. `element.click()` via JS). The agent must click via the Playwright input pipeline, not the DOM API.

### Graph Panning and Zooming

- **Pan the graph canvas:** Click and drag on an empty area of the graph (not on any node). Use `browser_click` at a point with no nodes, hold, then `browser_drag` to the desired position. This scrolls the viewport to reveal off-screen nodes.
- **Zoom out:** Use `browser_press_key` with scroll-down (or use `browser_evaluate` with `wheel` events on the graph canvas) to zoom out. Zooming out 3-4 levels lets you see the full tree structure in one screenshot.
- **Zoom in:** Scroll up on the graph canvas to zoom in on a specific area.
- **When to pan/zoom:** If a test requires interacting with nodes that are not visible in the current viewport (e.g. navigating back to earlier nodes, verifying full graph structure), pan and/or zoom out first. Take a screenshot after panning to confirm the target nodes are visible before clicking them.

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

4. **Check for a prior fix-log:** Read `fix-log.md` from the same results directory if it exists. This contains root cause analysis, planned fixes, and implementation notes from a previous fix-tests run against this same test report. For each failing test:
   - If the fix-log shows a fix was **planned but never implemented** (has a "Planned fix" entry but no "Implemented" entry) — that fix still needs to be done. Prioritise it.
   - If the fix-log shows a fix was **implemented but the test still fails** — the fix was insufficient or wrong. Do not repeat the same approach; try a different strategy.
   - If the fix-log shows **no entry** for a test — it hasn't been analysed yet.
   Output a brief summary of what the fix-log tells you before proceeding.

5. If no failures found, output "All tests passing — nothing to fix." and exit.

6. Output the failure list to the user before proceeding.

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

**a.1) Log analysis to the fix-log:**
- Write to `validation/results/<timestamp>/fix-log.md` — the same results directory as the test report being fixed
- Append an entry for this test under a `## Test N: <title>` heading
- Record: root cause analysis, which files are involved, and the planned fix
- Use this format:
  ```markdown
  ## Test N: <title>
  **Attempt:** N/3
  **Root cause:** <one-paragraph analysis>
  **Files involved:** <list of files>
  **Planned fix:** <what you intend to change>
  ```
- Update the same test's section on retry attempts rather than duplicating — add a new `**Attempt:**` block

**b) Implement the fix or feature:**
- For bug fixes: identify the root cause and fix it
- For unimplemented features (`status: unimplemented` in manifest): implement the feature as described by the test instructions
- Edit frontend and/or backend code as needed
- Keep changes minimal and focused — fix the specific issue, don't refactor surrounding code

**b.1) GATE — Verify code was actually changed before proceeding:**
- Run `git diff --stat` and confirm at least one file was modified
- If no files were changed, you have NOT implemented the fix — go back to step (b)
- Do NOT proceed to verification (step d) without passing this gate
- Analyzing the problem and planning a fix is not the same as implementing it — you must have actually edited files

**b.2) Log implementation to the fix-log:**
- Append to the current test's section in `validation/results/<timestamp>/fix-log.md`:
  ```markdown
  **Implemented:** <one-line summary of what was changed>
  **Files changed:** <output of git diff --stat>
  ```

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
- Wait for the app to load — take a screenshot to confirm "Story Controls" heading is visible
- **Replay prerequisite steps:** If the target test has `depends_on` dependencies, replay the necessary setup actions from those dependency tests to establish the required app state. For example:
  - To verify test 10 (Cancel choice node), first replay test 1 (create/select username), test 2 (select persona), test 3 (select corpus), test 5 (start journey, wait for stream), and test 9 (click a choice node to expand it)
  - Only replay the minimum chain needed — follow the `depends_on` path
- Execute the target test's instructions using Playwright MCP tools:
  - Use `browser_snapshot` ONLY to find element refs for clicking/typing targets
  - Use `browser_click` to click elements (by ref)
  - Use `browser_type` with `slowly: true` for all text input
  - Use `browser_press_key` for keyboard actions
  - Use `browser_wait_for` when waiting for elements or time to pass
  - Use `browser_navigate` for page reloads
- **Timeouts:**
  - Streaming operations (SSE story generation): wait up to **60 seconds**. **IMPORTANT: Do NOT use `browser_wait_for` with a `text` parameter for streaming — it has a 5-second default timeout that will expire before the stream finishes.** Instead, use `browser_wait_for` with `time: 40` (a pure time-based wait), then take a screenshot to check if streaming is complete. If still streaming, wait another 20 seconds with `time: 20` and screenshot again.
  - UI interactions (dropdowns, buttons, panels): wait up to **10 seconds**
  - Dropdown loading (personas, corpuses, journeys): after page load, use `browser_wait_for` with `time: 3` before interacting with dropdowns
- **Judge pass/fail by taking a screenshot and visually inspecting it** — not by reading the DOM snapshot

**e) On failure (retry):**
- If the test still fails, analyze what went wrong
- Try a different approach
- Up to **3 attempts total** per test
- After 3 failed attempts, log as **unresolved** and move to the next failure

**f) Reset between tests:**
- Reload the page after each test verification to clear app state before the next fix cycle

### Phase 3: Full Suite Run

After all individual fixes are done, run the complete test suite to catch regressions.

Follow the exact same procedure as the `test-app` skill (reference `.claude/skills/test-app/SKILL.md`), including all interaction rules (screenshots for assertions, `slowly: true` for typing, no `browser_evaluate` for actions):

1. **Server readiness** — curl health checks, start if needed
2. **Browser setup** — navigate to `http://localhost:3000`, confirm app loaded via screenshot
3. **Parse manifest** — read `validation/app-behaviors.md`, extract all tests
4. **Execute all tests** sequentially with dependency-based skip logic:
   - If a dependency failed or was skipped → mark as ⊘ SKIP
   - Otherwise execute via Playwright MCP, judge pass/fail via screenshots
   - Save screenshot for every executed test
5. **Write report** — save to `validation/results/<timestamp>/results.md` with this format:
   ```markdown
   # App Behavior Test Report
   Run: YYYY-MM-DD HH:MM:SS
   Browser: headless Chromium 1440x900

   ## Summary
   Total: N | Passed: N | Failed: N | Skipped: N

   ## Results

   ### N. Test title — ✓ PASS / ✗ FAIL / ⊘ SKIP
   [Description of what was done and observed in the screenshot]
   See: NNN-title-slug.png
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
