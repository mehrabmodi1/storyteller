# Validation Documentation

Engineering reference for the Storyteller behavior-driven test system — natural-language test manifests executed by Claude Code agents via Playwright MCP and direct API calls.

---

## Overview

This project uses an unconventional testing approach: instead of coded test scripts (Selenium, Cypress, pytest), tests are written as **natural-language behavior descriptions** that a Claude Code agent interprets and executes at runtime. The agent drives a real browser via Playwright MCP, interacts with the app exactly as a user would, takes screenshots to judge pass/fail, and produces human-readable reports.

The same manifests serve a dual purpose: they are both **regression tests** for existing behavior and **feature specs** for new functionality. A test marked `status: unimplemented` is a feature request — the `/fix-tests` skill reads the failure and implements the missing feature.

---

## Directory Structure

```
validation/
├── app-behaviors.md            # End-to-end UI test manifest (38 tests)
├── BE-behaviours.md            # Backend API test manifest (33 tests)
├── DOCUMENTATION.md            # This file
└── results/                    # Timestamped test run outputs
    ├── 2026-03-22-213356/      # Example run
    │   ├── results.md          # Pass/fail report
    │   ├── fix-log.md          # Root cause analysis + fixes (if /fix-tests was run)
    │   ├── 001-activate-username.png
    │   ├── 005-start-new-journey.png
    │   └── ...                 # Screenshot per executed test
    └── .../                    # Previous runs (kept for history)
```

---

## Test Manifests

### `app-behaviors.md` — End-to-End UI Tests

38 tests covering the full user journey through the Storyteller frontend. Each test is a natural-language instruction for a Claude Code agent driving Playwright MCP in a headless browser.

**Test format:**

```markdown
## N. Test title
depends_on: 1, 5
status: unimplemented          (optional — means feature doesn't exist yet)

Natural-language description of what to do, what to expect, and how to
judge pass/fail. May include specific UI elements, expected text, or
visual criteria (e.g. "no overlapping nodes").
```

**Test categories:**

| Range | Category | Examples |
|-------|----------|---------|
| 1-4 | Setup & dropdowns | Create username, select persona/corpus, verify selections |
| 5-7 | Story generation | Start journey, verify streaming, check graph nodes |
| 8-10 | Node interaction | Click story node, expand/cancel choice node |
| 11-13 | Journey continuation | Edit choice, continue story, verify new nodes |
| 14-17 | Layout & branching | Node layout quality, multi-branch graph integrity |
| 18-21 | Deep branching | Navigate between branches, verify 5-node tree |
| 22-26 | Persistence & reload | Page reload, journey dropdown, load saved graph |
| 27-29 | Edge cases | Empty prompt, stream error, corpus switching |
| 30-32 | Feature specs | Backend user discovery, placeholder nodes, images |
| 33-38 | Row mode | Toggle modes, depth navigation, horizontal scroll |

**Dependency system:** Tests declare `depends_on: N, M`. If any dependency fails, the dependent test is skipped (`SKIP (blocked by: N)`). This creates a cascading tree — a failure in test 5 (start journey) cascades to skip tests 6-21.

### `BE-behaviours.md` — Backend API Tests

33 tests covering the backend API via direct HTTP calls (no browser). Exercises story generation, guardrails, persistence, persona behavior, edge cases.

**Test categories:**

| Range | Category | Examples |
|-------|----------|---------|
| BE-1 to BE-3 | Health & config | Health check, list corpuses/personas |
| BE-4 to BE-8 | Core story flow | Generate story, verify summary, continue journey, path context |
| BE-9 to BE-11 | Story length | Short (1 para), long (8 para), invalid count |
| BE-12 to BE-17 | Guardrails | Legitimate dark themes pass, malicious prompts rejected, prompt injection blocked |
| BE-18 to BE-19 | Retrieval | Corpus-scoped content, nonexistent corpus error |
| BE-20 to BE-22 | Persistence | List/load journeys, survive server restart |
| BE-23 to BE-25 | Persona | Tone comparison, choice node voice, no-persona fallback |
| BE-26 to BE-33 | Edge cases | Empty prompt, invalid choice_id, concurrent requests, guardrails on continuation |

---

## Claude Code Skills

Two skills in `.claude/skills/` automate the test-fix loop.

### `/test-app` — Run the Test Suite

**Location:** `.claude/skills/test-app/SKILL.md`

**Invocation:**
- `/test-app` — run all 38 tests
- `/test-app N` — run only test N (skips dependency checks)

**What it does:**

1. **Server readiness** — Checks backend (port 8000) and frontend (port 3000), starts them if needed
2. **Browser setup** — Opens headless Chromium to `http://localhost:3000`
3. **Parse manifest** — Reads `validation/app-behaviors.md`, extracts test IDs, dependencies, instructions
4. **Execute tests** — For each test in order:
   - Check dependencies (skip if any failed)
   - Follow the natural-language instructions using Playwright MCP
   - Take screenshots to judge pass/fail
   - Save screenshots to `validation/results/<timestamp>/`
5. **Write report** — Produces `results.md` with per-test entries (pass/fail/skip + description + screenshot path)

**Interaction rules** (enforced by the skill):

| Rule | Why |
|------|-----|
| Screenshots for assertions, never DOM snapshots | DOM can show state that isn't visually rendered |
| `browser_type` with `slowly: true` for all text input | Atomic set bypasses keystroke handlers, masks bugs |
| `browser_click` for all interactions, not `browser_evaluate` | Must simulate real user input pipeline |
| 60-second timeout for streaming operations | SSE story generation takes 30-50 seconds |

### `/fix-tests` — Fix All Failures

**Location:** `.claude/skills/fix-tests/SKILL.md`

**Invocation:**
- `/fix-tests` — fix all failures from the latest test report

**What it does:**

1. **Read report** — Finds the most recent `results.md`, parses all `FAIL` entries
2. **Check fix-log** — If a prior fix attempt exists, reads it to avoid repeating failed approaches
3. **For each failure** (up to 3 attempts per test):
   - Reads the test instructions from the manifest
   - Explores the codebase to understand current implementation
   - Logs root cause analysis to `fix-log.md`
   - Implements the fix (bug fix) or feature (`status: unimplemented` tests)
   - Verifies with a single-test rerun via Playwright
   - If still failing, tries a different approach (up to 3 attempts)
4. **Full suite run** — After all individual fixes, runs the complete test suite to catch regressions
5. **Summary** — Reports fixed, unresolved, and regressed tests

**Fix-log format** (persisted to `validation/results/<timestamp>/fix-log.md`):

```markdown
## Test N: <title>
**Attempt:** 1/3
**Root cause:** <analysis>
**Files involved:** <list>
**Planned fix:** <what to change>
**Implemented:** <what was changed>
**Files changed:** <git diff --stat>
```

This log carries context across iterations — if `/fix-tests` runs out of context window and is restarted, the new session reads the fix-log to understand what was already tried.

---

## The Development Workflow

### Writing a new feature as a test

1. **Add a test** to `app-behaviors.md` describing the desired behavior:

```markdown
## 32. Verify story nodes display generated images
depends_on: 7
status: unimplemented

After a journey has been generated and the graph is visible, examine each
story node. Expect every story node to display a generated image...

Note: implementation requires the backend to generate images during story
creation and return image URLs in the story response...
```

The `status: unimplemented` flag tells the test runner this is expected to fail. The `Note:` paragraph gives implementation hints.

2. **Run `/test-app`** — the new test fails as expected. The report records what happened (e.g., "no images visible in story nodes").

3. **Run `/fix-tests`** — the agent reads the failure, implements the feature across frontend and backend, and verifies it works.

### Test as specification

Each test serves as a living specification. The natural-language format means:

- **Non-engineers can read and write tests** — no programming knowledge required
- **Tests describe intent, not implementation** — "expect the reading panel to show streaming text" rather than `expect(panel.textContent).toBeTruthy()`
- **Implementation hints are optional** — the `Note:` sections guide the agent but don't constrain it
- **Visual assertions catch visual bugs** — screenshots reveal layout issues, missing images, and rendering glitches that DOM assertions miss

### Continuous iteration with Ralph Loop

For fully autonomous iteration until all tests pass:

```
/ralph-loop "Run /fix-tests. Output <promise>ALL TESTS PASSING</promise> when the full suite shows zero failures." --max-iterations 5
```

Each iteration starts with fresh context but reads the latest test report and fix-log from disk, so progress carries across iterations automatically.

---

## Test Results

### Report format

```markdown
# App Behavior Test Report
Run: 2026-03-22 21:33:56
Browser: headless Chromium 1440x900

## Summary
Total: 38 | Passed: 37 | Failed: 0 | Skipped: 1

## Results

### 1. Activate username "agent-tester" — PASS
"agent-tester" pre-selected from localStorage on page load.
See: 001-activate-username.png

### N. Test title — FAIL
[What was done, what was observed in the screenshot, how it differs from expectation]
See: NNN-title-slug.png

### N. Test title — SKIP (blocked by: X, Y)
[Dependency X failed]
```

### Evidence trail

Every test run produces:
- **`results.md`** — Pass/fail report with natural-language descriptions
- **Screenshots** — One PNG per executed test, showing exactly what the agent saw
- **`fix-log.md`** (if `/fix-tests` ran) — Root cause analysis, planned fixes, implementation notes

This creates an auditable history of what was tested, what broke, and how it was fixed.

### Current state

As of the latest full run (2026-03-22): **37 of 38 tests passing**, 1 skipped (manual server restart verification).

---

## Features Built Via This Workflow

The following features were implemented by writing a failing test first, then running `/fix-tests`:

| Feature | Test(s) | What happened |
|---------|---------|---------------|
| **Placeholder nodes** | Test 31 | Agent implemented optimistic node insertion on stream start, spinner animation, click-to-reopen reading panel |
| **Image generation** | Test 32 | Agent wired DALL-E integration, local image storage, URL resolution, and frontend image rendering |
| **Row mode visualization** | Tests 33-38 | Agent built the row layout engine, depth navigation, scale/opacity falloff, choice windowing |
| **Backend user discovery** | Test 30 | Agent added `GET /api/list_users` endpoint and frontend merge with localStorage |
| **Stream error handling** | Test 28 | Agent added `__test_error__` corpus trigger and frontend error banner with dismiss |
| **Prompt guardrails** | BE-12 to BE-17 | Agent implemented OpenAI moderation + custom intent classifier, parallel execution, fail-closed design |
| **Graph sync recovery** | Test 14, BE-28 | Agent added `graph_id` parameter and disk reload fallback when in-memory state is stale |
| **Edited choice persistence** | Test 15 | Agent ensured choice node label updates propagate through graph save/load cycle |

---

## Extending the Test Suite

### Adding a UI test

1. Add a new `## N.` section to `app-behaviors.md`
2. Set `depends_on:` to the tests that establish prerequisite state
3. Add `status: unimplemented` if the feature doesn't exist yet
4. Describe the expected behavior in plain English — be specific about what to click, what to expect, and what constitutes failure
5. Optionally add a `Note:` paragraph with implementation hints

### Adding a backend test

1. Add a new `### BE-N.` section to `BE-behaviours.md`
2. Include the exact HTTP method, URL, and expected response
3. Set `depends_on:` to any prerequisite tests

### Guidelines for writing good tests

- **Be visually specific** — "expect the node to have a dashed border and spinning icon" not "expect a loading state"
- **Describe failure clearly** — "If the node still shows the original text, this is a FAIL"
- **Chain dependencies tightly** — each test should build on the minimum set of prerequisites
- **Include implementation hints** for complex features — these guide the agent without constraining the solution
- **One behavior per test** — don't combine "verify streaming" and "verify graph nodes" in a single test
