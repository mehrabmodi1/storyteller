# App Behavior Test Suite — Design Spec

## Overview

An agent-driven behavioral test suite for the Storyteller app. A Claude Code skill (`test-app`) reads a natural-language behavior manifest, drives the app via Playwright MCP, and produces a pass/fail report describing what worked and what didn't.

These are not programmatic unit tests. They are natural-language behavior descriptions executed by a Claude Code agent in a closed-loop browser environment. LLM-generated content is non-deterministic, but app behaviors (streaming triggers, node rendering, panel visibility) are deterministic and verifiable.

## Goals

1. **Regression safety** — catch breakage after code changes
2. **Feature completion guide** — failing tests highlight unfinished work
3. **Living documentation** — the manifest doubles as a human-readable spec of intended app behavior

## Architecture

Three components:

### 1. Behavior Manifest (`validation/app-behaviors.md`)

An ordered list of test cases in markdown. Each test has:
- A numbered heading (serves as the test id)
- A `depends_on:` line listing prerequisite test numbers (or `none`)
- Natural-language goal and hints (hybrid format — intent + rough direction)

Format:

```markdown
## 1. Create a new username
depends_on: none

Create username "agent-tester" using the username dropdown.
Expect the dropdown button to display "agent-tester" after creation.
```

The agent parses the test number and `depends_on` line as structured data. Everything else is interpreted as a natural-language instruction.

### 2. Claude Code Skill (`test-app`)

A skill that:

1. **Checks servers** — hits `localhost:8000/health` and `localhost:3000`. Starts them as background processes only if not already running.
2. **Opens browser** — navigates Playwright to `http://localhost:3000`.
3. **Reads manifest** — parses `validation/app-behaviors.md`, extracts test ids, titles, dependencies, and instructions.
4. **Runs tests sequentially** — for each test:
   - If any dependency failed or was skipped → mark as ⊘ SKIP
   - Otherwise, execute the instruction via Playwright MCP (snapshot, click, type, wait, screenshot)
   - Observe the result, judge pass/fail based on expected behavior
   - On failure: save a screenshot to the run's result folder
5. **Writes report** — saves to `validation/results/<timestamp>/results.md`.
6. **Leaves servers running** when done.

**Timeouts:** The agent should wait up to 60 seconds for streaming operations to complete (story generation via SSE). For non-streaming UI interactions (dropdown opens, button clicks), a 10-second timeout is sufficient. If a timeout is exceeded, the test fails.

**Directory creation:** The skill should create `validation/results/<timestamp>/` if it does not exist.

### 3. Test Report

Each run produces a timestamped folder:

```
validation/
├── app-behaviors.md
└── results/
    └── 2026-03-14-163045/
        ├── results.md
        ├── 005-start-new-journey.png
        └── 007-continue-journey.png
```

Screenshots are named `<test-id>-<title-slug>.png` and only saved on failure. A clean run contains only `results.md`.

Report format:

```markdown
# App Behavior Test Report
Run: 2026-03-14 16:30:45
Browser: headless Chromium 1440x900

## Summary
Total: 20 | Passed: 16 | Failed: 2 | Skipped: 2

## Results

### 1. Create a new username — ✓ PASS
Opened username dropdown, clicked "+ Add New", typed "agent-tester",
pressed Enter. Dropdown closed and button now shows "agent-tester".

### 3. Select corpus — ✗ FAIL
Clicked corpus dropdown. Showed "Loading..." for 10+ seconds with
no options appearing. See: 003-select-corpus.png

### 4. Start new journey — ⊘ SKIP (blocked by: 3)
```

Each entry includes: test id, title, status, and a natural-language description of what the agent did and observed.

## Test Data Strategy

- All tests use the username `agent-tester`.
- Each run starts a new journey — no cleanup of previous test data.
- Test journeys accumulate as a historical record of app development.

## Dependency & Skip Logic

Tests declare dependencies via `depends_on:`. If test N fails, any test listing N as a direct or transitive dependency is skipped. All non-dependent tests still run, giving maximum coverage per run.

## Behavior Manifest — Full Test List

### Setup & Controls

**1. Create username "agent-tester"**
`depends_on: none`
Open the username dropdown, add a new username "agent-tester". Expect the dropdown button to show "agent-tester".

**2. Select a persona**
`depends_on: 1`
Open the persona dropdown and select a persona. Expect the dropdown to show the selected persona name and the UI theme to change.

**3. Select a corpus**
`depends_on: 1`
Open the corpus dropdown and select a corpus. Expect the dropdown to show the selected corpus name.

**4. Verify dropdowns reflect selections**
`depends_on: 1, 2, 3`
Confirm all three dropdowns (username, persona, corpus) display their selected values.

### New Journey Flow

**5. Start a new journey**
`depends_on: 1, 2, 3`
Type an opening prompt in the new journey input and click "Start New Journey". Expect the reading panel to open with streaming text and a "Streaming..." status badge.

**6. Verify reading panel shows streaming text**
`depends_on: 5`
Observe the reading panel during/after streaming. Expect accumulated story text and the status badge to change to "Complete" when done. Note: match the status text loosely — do not rely on exact punctuation.

**7. Verify graph renders story and choice nodes**
`depends_on: 5`
After streaming completes, check the graph visualization. Expect at least one story node and multiple choice nodes connected by edges.

**8. Click a story node to open reading panel**
`depends_on: 7`
`status: unimplemented`
Click on a story node in the graph. Expect the reading panel to open displaying that node's story content. Note: this feature is not yet implemented — this test tracks a missing feature (Goal 2: feature completion guide). Expected to fail until the click-to-read handler is added to story nodes.

### Continue Journey Flow

**9. Click a choice node to select it**
`depends_on: 7`
Click on a choice node in the graph. Expect the node to expand showing an editable prompt textarea and "Continue Journey" / "Cancel" buttons.

**10. Cancel choice node selection**
`depends_on: 9`
With a choice node expanded, click the "Cancel" button. Expect the node to collapse back to its default state and the textarea to disappear.

**11. Re-select choice node, edit prompt, and continue journey**
`depends_on: 10`
Click a choice node again to expand it. Edit the text in the choice prompt textarea and click "Continue Journey". Expect the reading panel to reopen with new streaming story text.

**12. Verify new story streams in reading panel**
`depends_on: 11`
Observe the reading panel during the continuation stream. Expect new story text accumulating and the status badge showing streaming then complete.

**13. Verify graph adds new nodes**
`depends_on: 11`
After the continuation stream completes, check the graph. Expect a new story node connected to the previously selected choice node, with new choice nodes branching from it.

### Load Saved Journey

**14. Reload the page**
`depends_on: 5`
Reload the browser page to clear in-memory state. Expect the app to load with no username selected (dropdown shows default "Select Username"), while persona and corpus dropdowns show their default values from the API.

**15. Select username "agent-tester" after reload**
`depends_on: 14`
Open the username dropdown and select "agent-tester" (the username list persists in localStorage, but no username is pre-selected after reload). Expect the dropdown to show "agent-tester".

**16. Verify journey dropdown shows saved journeys**
`depends_on: 15`
After selecting the username, check that the journey dropdown loads and displays a list of saved journeys for "agent-tester". Expect at least one journey entry from the earlier test run.

**17. Load a saved journey**
`depends_on: 16`
Select the most recent saved journey from the journey dropdown. Expect the graph to render with the journey's nodes and edges.

**18. Verify loaded journey graph**
`depends_on: 17`
Inspect the loaded graph. Expect it to contain the story and choice nodes from the earlier test run, with correct connections.

### Error Handling

**19. Attempt empty prompt submission**
`depends_on: 1`
Clear the journey prompt input and attempt to click "Start New Journey". Expect the button to be disabled or the submission to be rejected — no stream should start.

**20. Trigger a stream error**
`depends_on: 1`
`status: unimplemented`
Attempt to start a journey with conditions that trigger a backend error (e.g., select an invalid corpus if possible, or test with servers in a known error state). Expect an error message to appear in the UI with a "Dismiss" button. Note: the exact trigger mechanism may need to be determined during implementation — this test tracks error handling coverage.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Test format | Natural language with minimal structured metadata (markdown + `depends_on`) | Human-readable as documentation; trivially parseable for dependency resolution. YAML fallback if parsing proves unreliable. |
| Execution model | Sequential with dependency-based skip logic | Mirrors real user flow; skips blocked tests but runs everything else for maximum coverage. |
| Test data | Leave in place, new journey per run | Journeys serve as historical record of app state during development. |
| Server lifecycle | Detect and reuse running servers; start only if needed | Works both standalone and mid-session. |
| LLM content | Real generation, not mocked | Tests verify actual end-to-end behavior including streaming. |
| Viewport | 1440x900 headless Chromium | Standard desktop resolution; configured in `.mcp.json`. |