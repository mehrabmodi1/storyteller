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

Navigate Playwright to `http://localhost:3000`. Take a screenshot to confirm the app loaded (look for "Story Controls" heading visible in the image).

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
   - Use `browser_snapshot` ONLY to find element refs for clicking/typing targets
   - Use `browser_click` to click elements (by ref)
   - Use `browser_type` with `slowly: true` for all text input
   - Use `browser_press_key` for keyboard actions
   - Use `browser_wait_for` when waiting for elements or time to pass
   - Use `browser_navigate` for page reloads

3. **Timeouts**:
   - Streaming operations (SSE story generation): wait up to **60 seconds**. **IMPORTANT: Do NOT use `browser_wait_for` with a `text` parameter for streaming — it has a 5-second default timeout that will expire before the stream finishes.** Instead, use `browser_wait_for` with `time: 40` (a pure time-based wait), then take a screenshot to check if streaming is complete. If still streaming, wait another 20 seconds with `time: 20` and screenshot again.
   - UI interactions (dropdowns, buttons, panels): wait up to **10 seconds**
   - Dropdown loading (personas, corpuses, journeys): after page load, use `browser_wait_for` with `time: 3` before interacting with dropdowns

4. **Judge**: **Take a screenshot and visually inspect it** to determine if the expected behavior occurred. Do NOT rely on `browser_snapshot` for pass/fail decisions.
   - **STRICT PASS/FAIL RULE**: ANY divergence from the expected behavior described in the test instructions is a FAIL. No exceptions. If the test says "edit the prompt text" and the text doesn't change in the screenshot, that's a FAIL — even if the DOM shows the new text. If the test says "nodes should remain visible" and they disappear in the screenshot, that's a FAIL. Do not rationalize partial successes. Do not speculate about causes — just describe exactly what you see in the screenshot and how it differs from what was expected.
   - For `status: unimplemented` tests: a failure is expected. Still report what happened but mark as ✗ FAIL (expected).

5. **Save screenshot**: Save the screenshot to the results folder. Zero-pad the test id to 3 digits:
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
[Description of what was done and what was observed in the screenshot]
See: 001-create-username.png

### N. Test title — ✗ FAIL
[Description of what was done, what was observed in the screenshot, how it differed from expectation]
See: NNN-title-slug.png

### N. Test title — ⊘ SKIP (blocked by: X, Y)
[No action taken — dependency X failed]
```

Each result entry MUST include:
- Test id and title
- Status symbol: ✓ PASS, ✗ FAIL, or ⊘ SKIP
- Natural-language description of what the agent did and observed **in the screenshot**
- Screenshot filename (for every executed test, not just failures)

### Phase 6: Summary

After writing the report, output a brief summary to the user:
- Path to the results folder
- Total / passed / failed / skipped counts
- List of any failures with one-line descriptions

Do NOT shut down the servers when done.
