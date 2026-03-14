# Fix-Tests Skill — Design Spec

## Overview

A Claude Code skill (`fix-tests`) that reads the most recent full test report, identifies all failing tests, autonomously fixes each one by editing frontend/backend code, verifies each fix with a single-test rerun, then runs the full suite to catch regressions.

Tests serve as feature specs. A `status: unimplemented` test is a feature request — the skill implements the missing feature, not just fixes bugs.

## Goals

1. **Close the loop** — test failures and unimplemented features get resolved without manual intervention
2. **Tests as feature specs** — users can add desired features as test entries in `app-behaviors.md` and invoke `/fix-tests` to implement them
3. **Regression safety** — a full suite run after all fixes catches unintended breakage

## Invocation

- `/fix-tests` — read the latest full report, fix all failures, run full suite

## Architecture

Single self-contained skill with 4 sequential phases. No inter-skill dependencies — the skill runs Playwright MCP inline rather than invoking `test-app`.

### Phase 1: Read Report

1. Find the most recent test report: sort `validation/results/*/` directories by name (lexicographic = chronological), take the latest.
2. Read `validation/results/<latest>/results.md`.
3. Parse each test entry. Format is stable:
   ```
   ### N. Test title — ✗ FAIL
   [description of what happened]
   ```
   or:
   ```
   ### N. Test title — ✗ FAIL (expected)
   [description of what happened]
   ```
4. Build a failure list: all tests with `✗ FAIL` status, including `FAIL (expected)`.
5. If no failures found, report "all tests passing" and exit.

### Phase 2: Fix Loop

For each failure, sequentially:

1. **Gather context:**
   - Read the failure description from the test report (what was observed, how it differed from expectation)
   - Read the test's instructions from `validation/app-behaviors.md` (what the test expects)
   - Explore the relevant codebase to understand the current implementation

2. **Implement the fix or feature:**
   - Edit frontend (`storyteller_frontend/src/`) and/or backend (`storyteller_backend/`) code as needed
   - For bug fixes: identify and fix the root cause
   - For unimplemented features: implement the feature as described by the test

3. **Verify with single-test rerun:**
   - Ensure servers are running (check once at start of Phase 2, not per-test)
   - Navigate Playwright to `http://localhost:3000`
   - Execute the test's instructions from `app-behaviors.md` using Playwright MCP
   - Judge pass/fail based on observed behavior
   - Vite HMR reflects code changes immediately — no server restart needed

4. **Retry on failure:**
   - If the test still fails, analyze what went wrong and try a different approach
   - Up to **3 attempts total** per test
   - After 3 failed attempts, log as "unresolved" and move to the next failure

5. **Reset between tests:**
   - Reload the page after each single-test rerun to clear app state

### Phase 3: Full Suite Run

After all individual fixes are done:

1. Run the full test suite following the same procedure as the `test-app` skill (all phases: server check, browser setup, parse manifest, execute all tests, write report).
2. Write a new timestamped report to `validation/results/<timestamp>/results.md`.
3. Compare against the original failure list:
   - Tests that were failing and now pass → **fixed**
   - Tests that were failing and still fail → **unresolved**
   - Tests that were passing and now fail → **regressions**

### Phase 4: Summary

Output to the user:
- Count of fixed / unresolved / regressed tests
- List of each with one-line descriptions
- Paths to modified code files
- Path to the new test report

## Permissions

Same as `test-app`:
- Do NOT ask for permission to create directories, write files, or run bash commands.
- Do NOT ask for permission for any Playwright MCP action.
- Do NOT ask for permission to edit code files.
- Proceed autonomously through all phases.

## Constraints

- **Sequential execution** — fixes are applied one at a time, not in parallel (code changes can conflict, and the app has shared state)
- **Server lifecycle** — check once, don't restart between tests. HMR handles code changes.
- **3-attempt cap** — prevents infinite loops on intractable failures
- **No manual approval** — the skill operates with full autonomy; the user reviews results after completion

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Skill architecture | Single monolithic skill | Workflow is inherently sequential; no benefit from parallelism or multi-skill coordination |
| Unimplemented features | Treated as fixable failures | Tests are feature specs — the skill implements missing features, not just fixes bugs |
| Fix verification | Single-test rerun inline | Avoids skill-calling-skill complexity; keeps the loop tight |
| Retry limit | 3 attempts per test | Balances persistence with avoiding infinite loops |
| Full suite timing | After all fixes, not after each | Each full run takes ~10 minutes with streaming; running after each fix is too slow |
| Code change strategy | Full autonomy | User reviews results after completion, not during |
