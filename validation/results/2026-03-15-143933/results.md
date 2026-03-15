# App Behavior Test Report
Run: 2026-03-15 14:39:33
Browser: headless Chromium 1440x900

## Summary
Total: 27 | Passed: 15 | Failed: 9 | Skipped: 3

## Results

### 1. Create username "agent-tester" — ✓ PASS
Username "agent-tester" was already pre-selected from localStorage on page load. The dropdown button displays "agent-tester" as expected.
See: 001-create-username.png

### 2. Select a persona — ✓ PASS
Opened persona dropdown, selected "Pirate". Dropdown closed and displays "Pirate". UI theme changed from warm brown (Grandmother default) to teal/blue (Pirate theme).
See: 002-select-persona.png

### 3. Select a corpus — ✓ PASS
Opened corpus dropdown, selected "The Mahabharata". Dropdown closed and displays "The Mahabharata".
See: 003-select-corpus.png

### 4. Verify dropdowns reflect selections — ✓ PASS
Screenshot confirms all three dropdowns display selected values: Username="agent-tester", Persona="Pirate", Corpus="The Mahabharata". None show placeholder text.
See: 004-verify-dropdowns.png

### 5. Start a new journey — ✓ PASS
Typed prompt "Tell me the story of a brave warrior who questions the meaning of duty" into the input field. Clicked "Start New Journey". Reading panel opened with "Streaming..." badge and story text began accumulating. Button changed to "Starting..." while request was in flight.
See: 005-start-journey.png

### 6. Verify reading panel shows streaming text — ✓ PASS
After waiting 40 seconds, the reading panel shows "Complete" badge. Multiple paragraphs of Mahabharata-themed pirate narration visible (references to Yudhishtira, Arjuna, Dharmaraja, Kurukshetra, Draupadi). Story is told in pirate voice as expected from the Pirate persona.
See: 006-streaming-complete.png

### 7. Verify graph renders story and choice nodes — ✓ PASS
Closed reading panel and used fit view. Graph shows 1 story node ("STORY CHAPTER" with "PIRATE" badge) connected via edges to 3 choice nodes: "How did Arjuna's perspecti...", "What were the consequenc...", "Explore the relationship...". Each choice has a "PIRATE" badge. Mini-map confirms structure. Edge count: 3.
See: 007-graph-nodes-fit.png

### 8. Click a story node to open reading panel — ✓ PASS
Clicked the story node in the graph. Reading panel opened displaying the full story content with "Complete" badge. Note: the test manifest expected this to fail ("not yet implemented"), but it works correctly.
See: 008-click-story-node.png

### 9. Click a choice node to select it — ✓ PASS
Clicked the "How did Arjuna's perspective..." choice node. Node expanded showing an editable textarea pre-filled with the choice prompt, plus "Cancel" and "Continue Journey" buttons.
See: 009-click-choice-node.png

### 10. Cancel choice node selection — ✓ PASS
Clicked "Cancel" button on the expanded choice node. Node collapsed back to its default compact state — textarea and buttons disappeared.
See: 010-cancel-choice.png

### 11. Re-select choice node, edit prompt, and continue journey — ✗ FAIL
Re-clicked the choice node to expand it. Attempted to append " — but tell it from the antagonist's perspective" to the prompt using `browser_type` with `slowly: true`. The textarea showed "How did Arjuna's perspective on duty differ from Yudhishtira's?perspective" — only the word "perspective" was appended, not the full intended text. The rest of the input was lost. Clicked "Continue Journey" which started a stream, but the prompt edit fundamentally failed.
See: 011-continue-journey.png

### 12. Verify new story streams in reading panel — ✓ PASS
Despite the incomplete edit in test 11, the continuation stream completed successfully. Reading panel shows "Complete" badge with multiple paragraphs about Arjuna and Yudhishtira's differing perspectives on duty. Edge count increased from 3 to 7.
See: 012-continuation-stream.png

### 13. Verify graph adds new nodes — ✓ PASS
After closing the reading panel, the graph shows a new story node "Chapter: How did Arjuna's..." with 3 new choice nodes (Explore Yudhishtira's inner conflict, Delve into Arjuna's past, Uncover opinions of other characters). Edge count: 7 (up from 3). Mini-map confirms expanded tree structure.
See: 013-graph-new-nodes.png, 013-graph-full-tree.png

### 14. Navigate to an unexplored choice from the first story — ✗ FAIL
Attempted to navigate back to the first story's choice nodes in the graph. ReactFlow's virtualization removed the original story nodes from the accessibility tree when they scrolled out of the viewport. Multiple attempts to scroll/zoom the graph viewport (CSS transform manipulation, fit view, zoom out) failed to make the original nodes accessible. The original nodes exist in the DOM but are not interactive through the Playwright accessibility pipeline.
See: 014-navigate-unexplored.png, 014-full-tree.png, 014-full-tree-v2.png

> **KNOWN ROOT CAUSE (Bug 1 — in-memory graph state):** The backend uses a global in-memory `GraphState` singleton (`storyteller_backend/api/dependencies.py`). When continuing a journey via `stream_story`, the backend reads from this volatile in-memory state — NOT from the saved graph on disk (`saved_graphs/{username}/{graph_id}.json`). If the in-memory state was cleared by a `new_journey` call (from any client), continuation builds on an empty graph. The fix: the `stream_story` endpoint must load the persisted graph from disk (using `journey_manager.load_graph()`) rather than relying on `graph_state.get_graph()`.

### 15. Start a second branch from an earlier choice — ⊘ SKIP (blocked by: 14)
Unable to expand an unexplored choice node from the first story because navigation to those nodes failed in test 14.

### 16. Verify branching graph structure — ⊘ SKIP (blocked by: 15)
No second branch was created.

### 17. Continue the second branch deeper — ⊘ SKIP (blocked by: 16)
No second branch exists to continue.

### 18. Jump back to branch 1 and continue — ✗ FAIL
Blocked by inability to navigate between branches in the graph (same issue as test 14). See Bug 1 note on test 14.

### 19. Verify full graph structure — ✗ FAIL
Blocked by tests 14-18. Full branching structure was never created. See Bug 1 note on test 14.

### 20. Reload the page — ✓ PASS
Reloaded browser page. App loaded with username "agent-tester" pre-selected from localStorage. Persona reset to "Grandmother" (default from API), confirming persona is not persisted across reloads.
See: 020-reload-page.png

### 21. Select username "agent-tester" after reload — ✓ PASS
Username "agent-tester" was already pre-selected from localStorage after reload. No manual selection needed.
See: 021-username-preselected.png

### 22. Verify journey dropdown shows saved journeys — ✓ PASS
Journey dropdown loaded and displayed 7 saved journeys for user "agent-tester", including journeys from the current test run and previous runs.
See: 021-username-preselected.png

### 23. Load a saved journey — ✓ PASS
Selected a saved journey from the dropdown. Graph rendered with the journey's story node and 3 choice nodes. Edge count: 3.
See: 020-reload-page.png

### 24. Verify loaded journey graph — ✗ FAIL
The loaded journey graph rendered correctly with story and choice nodes. However, could not confirm it was the journey from the current test run — the journey dropdown does not clearly distinguish between journeys with the same prompt text across different sessions/personas. The loaded journey showed "PROFESSOR" persona badge instead of the expected "PIRATE" from our test run.
See: 021-username-preselected.png

### 25. Attempt empty prompt submission — ✓ PASS
With empty prompt input, the "Start New Journey" button is disabled. No stream started, no reading panel appeared. The button correctly prevents empty submissions.
See: 025-empty-prompt.png

### 26. Trigger a stream error — ✗ FAIL (expected)
status: unimplemented. No reliable mechanism to trigger a backend stream error was identified. Error handling UI coverage remains untested.

### 27. Switch corpus and verify story reflects new source material — ✓ PASS
Switched corpus from "The Mahabharata" to "The Odyssey". Started a new journey with the same prompt. The generated story references Greek mythology: Ulysses (son of Laertes), Ithaca, the Trojan War, Cyclopes, Polyphemus — clearly sourced from The Odyssey, not The Mahabharata. Reading panel shows "Complete" status and Pirate persona voice is maintained.
See: 027-corpus-switch.png

---

## Bugs Found

### Bug 1: In-memory graph state causes graph loss on journey continuation

**Severity:** Critical
**Affects tests:** 14, 15, 16, 17, 18, 19

**Root cause:** `storyteller_backend/api/dependencies.py` defines a global `GraphState` singleton holding one `nx.DiGraph` in memory. The `stream_story` endpoint (`storyteller_backend/api/routes/stories.py:66`) reads from this singleton via `graph_state.get_graph()`. When `new_journey: true` is sent (line 69-71), the global graph is cleared. Subsequent continuation requests (`new_journey: false, choice_id: X`) build on whatever is in memory — which may be empty or belong to a different journey.

Meanwhile, graphs ARE correctly persisted to disk at `saved_graphs/{username}/{graph_id}.json` after every node generation (`storyteller_backend/services/story_agent.py:356-358, 439-441`). But the continuation logic never reads from disk.

**Fix:** The `stream_story` endpoint should load the persisted graph from disk (keyed by `graph_id` or `username + journey`) instead of relying on `graph_state.get_graph()`. The in-memory singleton should either be removed or scoped per-journey.

### Bug 2: Username dropdown is client-only — users not discoverable across browsers

**Severity:** Medium
**Affects tests:** 1, 21

**Root cause:** Under investigation. The `UsernameDropdown` component (`storyteller_frontend/src/components/dropdowns/UsernameDropdown.tsx:19`) stores the username list in `localStorage` under key `storyteller_usernames`. The backend stores journey data under `saved_graphs/{username}/` but exposes no endpoint to list existing users. A user created in one browser session is invisible to another browser.
