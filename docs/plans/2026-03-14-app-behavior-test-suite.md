# App Behavior Test Suite — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an agent-driven behavioral test suite — a behavior manifest and a Claude Code skill (`test-app`) that drives Playwright MCP to exercise the Storyteller app and produce a pass/fail report.

**Architecture:** A markdown behavior manifest with lightweight dependency metadata, a Claude Code skill that reads/parses it and drives the browser, and timestamped result folders with reports and failure screenshots.

**Tech Stack:** Claude Code skills (SKILL.md), Playwright MCP, markdown manifests, Bash (server lifecycle)

**Spec:** `docs/specs/2026-03-14-app-behavior-test-suite-design.md`

---

## Chunk 1: Behavior Manifest

### Task 1: Create the behavior manifest file

**Files:**
- Create: `validation/app-behaviors.md`

- [ ] **Step 1: Create the validation directory**

```bash
mkdir -p validation/results
```

- [ ] **Step 2: Write the behavior manifest**

Create `validation/app-behaviors.md` with the full test list from the spec. Each test has a numbered heading, a `depends_on:` line, and natural-language instructions.

```markdown
# Storyteller — App Behavior Tests

This manifest describes the expected behaviors of the Storyteller app.
Each test is a natural-language instruction for a Claude Code agent driving
Playwright MCP in a headless browser. Tests declare dependencies — if a
dependency fails, dependent tests are skipped.

Username for all tests: `agent-tester`

---

## 1. Create username "agent-tester"
depends_on: none

Open the username dropdown, click "+ Add New", type "agent-tester", and
press Enter. Expect the dropdown to close and the button to display
"agent-tester".

## 2. Select a persona
depends_on: 1

Open the persona dropdown and select a persona. Expect the dropdown to
show the selected persona name and the UI theme colors to change
(background, buttons).

## 3. Select a corpus
depends_on: 1

Open the corpus dropdown and select a corpus. Expect the dropdown to show
the selected corpus name.

## 4. Verify dropdowns reflect selections
depends_on: 1, 2, 3

Take a snapshot of the page. Confirm all three dropdowns (username,
persona, corpus) display their selected values — not default/placeholder
text.

## 5. Start a new journey
depends_on: 1, 2, 3

Type a prompt (e.g. "Tell me the story of a brave warrior who questions
the meaning of duty") in the new journey input and click
"Start New Journey". Expect the reading panel to open with streaming text
and a status badge indicating streaming is in progress.

## 6. Verify reading panel shows streaming text
depends_on: 5

Wait for the stream to complete (up to 60 seconds). Observe the reading
panel. Expect accumulated story text (multiple paragraphs) and the status
badge to change to indicate completion. Match status text loosely — do not
rely on exact punctuation.

## 7. Verify graph renders story and choice nodes
depends_on: 5

After streaming completes, take a snapshot of the graph area. Expect at
least one story node (with narrative text) and multiple choice nodes
connected by edges.

## 8. Click a story node to open reading panel
depends_on: 7
status: unimplemented

Click on a story node in the graph. Expect the reading panel to open
displaying that node's story content. Note: this feature is not yet
implemented — expected to fail until the click-to-read handler is added
to story nodes.

## 9. Click a choice node to select it
depends_on: 7

Click on a choice node in the graph. Expect the node to expand, showing
an editable prompt textarea and "Continue Journey" / "Cancel" buttons.

## 10. Cancel choice node selection
depends_on: 9

With a choice node expanded, click the "Cancel" button. Expect the node
to collapse back to its default state — the textarea and buttons should
disappear.

## 11. Re-select choice node, edit prompt, and continue journey
depends_on: 10

Click a choice node again to expand it. Edit the text in the prompt
textarea (e.g. append " — but tell it from the antagonist's perspective")
and click "Continue Journey". Expect the reading panel to reopen with new
streaming story text.

## 12. Verify new story streams in reading panel
depends_on: 11

Wait for the continuation stream to complete (up to 60 seconds). Observe
the reading panel. Expect new story text accumulating and the status badge
showing streaming then complete.

## 13. Verify graph adds new nodes
depends_on: 11

After the continuation stream completes, take a snapshot of the graph.
Expect a new story node connected to the previously selected choice node,
with new choice nodes branching from it. The graph should now have more
nodes than after test 7.

## 14. Reload the page
depends_on: 5

Reload the browser page to clear in-memory state. Expect the app to load
with no username selected (dropdown shows "Select Username"), while
persona and corpus dropdowns show their default values from the API.

## 15. Select username "agent-tester" after reload
depends_on: 14

Open the username dropdown and select "agent-tester" from the list (the
username list persists in localStorage, but no username is pre-selected
after reload). Expect the dropdown to show "agent-tester".

## 16. Verify journey dropdown shows saved journeys
depends_on: 15

After selecting the username, check that the journey dropdown loads and
displays a list of saved journeys for "agent-tester". Expect at least one
journey entry from the earlier test run.

## 17. Load a saved journey
depends_on: 16

Select the most recent saved journey from the journey dropdown. Expect the
graph to render with the journey's nodes and edges.

## 18. Verify loaded journey graph
depends_on: 17

Take a snapshot of the loaded graph. Expect it to contain story and choice
nodes with correct connections — the structure should match what was
generated in the earlier test run.

## 19. Attempt empty prompt submission
depends_on: 1

Clear the journey prompt input and attempt to click "Start New Journey".
Expect the button to be disabled or the submission to be rejected — no
stream should start and no reading panel should appear.

## 20. Trigger a stream error
depends_on: 1
status: unimplemented

Attempt to start a journey with conditions that trigger a backend error
(e.g., select an invalid corpus if possible). Expect an error message to
appear in the UI with a "Dismiss" button. Note: the exact trigger
mechanism may need to be determined during implementation — this test
tracks error handling coverage.
```

- [ ] **Step 3: Commit the manifest**

```bash
git add validation/app-behaviors.md
git commit -m "feat: add app behavior test manifest with 20 test cases"
```

---

## Chunk 2: Claude Code Skill

### Task 2: Create the `test-app` skill

**Files:**
- Create: `.claude/skills/test-app/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills/test-app
```

- [ ] **Step 2: Write the skill file**

Create `.claude/skills/test-app/SKILL.md`:

```markdown
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

### Phase 4: Execute Tests

Create the results directory:
```bash
mkdir -p validation/results/$(date +%Y-%m-%d-%H%M%S)
```

For each test in order:

1. **Check dependencies**: If any dependency has status FAIL or SKIP, mark this test as ⊘ SKIP with reason "blocked by: N, M". Note: transitivity is handled naturally — a skipped test causes its dependents to skip too, cascading through the chain.

2. **Execute**: Follow the natural-language instructions using Playwright MCP tools:
   - Use `browser_snapshot` to read page state (preferred over screenshots for assertions)
   - Use `browser_click`, `browser_fill_form`, `browser_type`, `browser_press_key` to interact
   - Use `browser_wait_for` when waiting for elements to appear
   - Use `browser_navigate` for page reloads

3. **Timeouts**:
   - Streaming operations (SSE story generation): wait up to **60 seconds**
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
```

- [ ] **Step 3: Commit the skill**

```bash
git add .claude/skills/test-app/SKILL.md
git commit -m "feat: add test-app Claude Code skill for behavior testing"
```

---

## Chunk 3: Smoke Test

### Task 3: Run the skill to verify the full loop works

- [ ] **Step 1: Start the servers**

```bash
cd storyteller_backend && poetry run python -m api.main > /tmp/storyteller_backend.log 2>&1 &
cd storyteller_frontend && npm run dev > /tmp/storyteller_frontend.log 2>&1 &
```

Wait for health checks to pass.

- [ ] **Step 2: Invoke the skill**

Run `/test-app` to execute the full behavior test suite.

- [ ] **Step 3: Review the report**

Check the generated `validation/results/<timestamp>/results.md`. Verify:
- All 20 tests are listed
- Dependencies are resolved correctly (skips propagate)
- Pass/fail judgments match expected behavior
- Screenshots exist for failures
- Report is human-readable

- [ ] **Step 4: Fix any issues with the skill or manifest**

If the skill fails to parse the manifest, or tests don't execute correctly, iterate on the skill instructions or manifest format.

- [ ] **Step 5: Commit any fixes**

```bash
git add validation/ .claude/skills/test-app/
git commit -m "fix: refine test-app skill after smoke test"
```

- [ ] **Step 6: Copy the latest results report to Desktop for user review**

```bash
cp "$(ls -dt validation/results/*/results.md | head -1)" ~/Desktop/test-results.md
```
