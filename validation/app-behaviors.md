# Storyteller — App Behavior Tests

This manifest describes the expected behaviors of the Storyteller app.
Each test is a natural-language instruction for a Claude Code agent driving
Playwright MCP in a headless browser. Tests declare dependencies — if a
dependency fails, dependent tests are skipped.

Username for all tests: `agent-tester`

---

## 1. Activate username "agent-tester"
depends_on: none

Open the username dropdown. If "agent-tester" already appears in the list,
select it. If not, click "+ Add New", type "agent-tester", and press Enter.
Expect the dropdown to close and the button to display "agent-tester".

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

Click on a story node in the graph. Expect the reading panel to open displaying that node's story content.

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

## 14. Verify node layout immediately after story generation
depends_on: 13

This test checks layout quality IMMEDIATELY after streaming completes —
do NOT reload the page, pan, zoom, or interact with the graph before
taking the screenshot. The graph should already be well-laid-out without
any manual intervention.

Close the reading panel if it is covering the graph. Then immediately
take a screenshot of the graph area. The graph now has story-1, story-2,
and their choice nodes. Inspect the screenshot for:

- **No overlapping nodes:** Story nodes and choice nodes must not sit on
  top of each other. Every node should have clear visual separation.
- **No clipped or hidden labels:** All node labels should be fully
  readable, not obscured by neighbouring nodes.
- **Parent-child spacing:** There should be visible vertical space between
  story-1 and its choice nodes, and between the selected choice node and
  story-2.
- **Sibling spacing:** Choice nodes at the same level should be spread
  out horizontally, not stacked or bunched together.

If newly generated nodes are crowding or overlapping existing nodes, this
is a FAIL — the layout engine must arrange nodes cleanly as soon as they
are added, not only after a page refresh or user interaction.

## 15. Verify edited choice node shows updated text
depends_on: 13

After test 11 edited a choice node's prompt and continued the journey,
the choice node that was selected should now display the edited text —
not the original prompt. Close the reading panel if open. Find the
choice node that was used in test 11 (the one connected to the second
story node). Its label text should reflect the edit made in test 11
(e.g. it should contain the appended text). If the node still shows
the original unedited prompt, this is a FAIL.

## 16. Verify graph integrity after branching from an upper-level node
depends_on: 13

Close the reading panel if open. Navigate or scroll back in the graph to
the first story node's choice nodes. Identify a choice node that was NOT
used in test 11 (i.e. not the one that led to the second story). Click it
to expand, then click "Continue Journey" and wait for the stream to
complete (up to 60 seconds).

After the new story node (story-3) is generated, zoom out or pan the graph
to see the full structure. Verify ALL of the following are visible:
- **story-1** (the original story node) with its choice nodes
- **story-2** (previously explored branch) connected to one of story-1's choices
- **story-3** (the newly generated node) connected to a different choice of story-1
- story-2's own choice nodes are still present
- story-3's new choice nodes are present

The graph should show a tree with story-1 at the root and two branches.
If any previously existing nodes (story-1, story-2, or their choice nodes)
have disappeared, this is a FAIL — the graph state was lost during branching.

## 17. Verify graph layout is clean and non-overlapping
depends_on: 16

After the branching in test 16, zoom out until the full graph is visible in
one screenshot (story-1 at the root, story-2 and story-3 as branches, plus
all their choice nodes). Take a screenshot and visually inspect the layout:

- **No overlapping nodes:** Story nodes and choice nodes must not overlap or
  sit on top of each other. Every node should have clear boundaries with
  visible spacing between it and its neighbours.
- **Even spacing:** Nodes at the same depth level should be roughly evenly
  spaced horizontally. Parent-child vertical spacing should be consistent.
- **Readable labels:** Node labels should not be clipped or hidden behind
  other nodes.
- **Edges don't cross nodes:** Connection lines between nodes should route
  around other nodes, not pass through them.

If nodes overlap, are crammed together, or the layout looks cluttered and
hard to read, this is a FAIL. A clean hierarchical tree layout is expected.

## 18. Navigate to an unexplored choice from the second story
depends_on: 16

Close the reading panel if open. Navigate to story-2's choice nodes (the
branch explored in test 11). Identify an unexplored choice node and click
it to expand it.

## 19. Continue the second branch deeper
depends_on: 18

With the choice node expanded, edit the prompt if desired and click
"Continue Journey". Wait for the stream to complete (up to 60 seconds).
Expect a 4th story node, making branch 1 two levels deep.

## 20. Jump back to branch 2 and continue
depends_on: 19

Navigate to branch 2 (the story generated in test 16, story-3). Find an
unexplored choice node from that story and click it to expand. Edit the
prompt and click "Continue Journey". Wait for the stream to complete (up
to 60 seconds). Expect a new story node on branch 2. The graph should now
have 5 story nodes across 2 branches, each 2 levels deep.

## 21. Verify full graph structure
depends_on: 20

Take a snapshot of the full graph. Expect 5 story nodes with correct
parent-child connections across both branches. Each story node should have
choice nodes branching from it. The total edge count should reflect the
full tree structure.

## 22. Reload the page
depends_on: 16

Reload the browser page to clear in-memory state. Expect the app to load
with username "agent-tester" pre-selected (persisted in localStorage),
while persona resets to its default value from the API.

## 23. Select username "agent-tester" after reload
depends_on: 22

Verify the username dropdown shows "agent-tester" (pre-selected from
localStorage). If not pre-selected, select it from the dropdown.

## 24. Verify journey dropdown shows saved journeys
depends_on: 23

After the username is set, check that the journey dropdown loads and
displays a list of saved journeys for "agent-tester". Expect at least one
journey entry from the earlier test run.

## 25. Load a saved journey
depends_on: 24

Select the most recent saved journey from the journey dropdown. Expect the
graph to render with the journey's nodes and edges.

## 26. Verify loaded journey graph
depends_on: 25

Take a snapshot of the loaded graph. Expect it to contain the full
branching structure from the earlier test run — multiple story nodes
across branches with correct connections.

## 27. Attempt empty prompt submission
depends_on: 1

Clear the journey prompt input and attempt to click "Start New Journey".
Expect the button to be disabled or the submission to be rejected — no
stream should start and no reading panel should appear.

## 28. Trigger a stream error
depends_on: 1
status: unimplemented

Attempt to start a journey with conditions that trigger a backend error
(e.g., select an invalid corpus if possible). Expect an error message to
appear in the UI with a "Dismiss" button. Note: the exact trigger
mechanism may need to be determined during implementation — this test
tracks error handling coverage.

## 29. Switch corpus and verify story reflects new source material
depends_on: 6

The first story was generated using "The Mahabharata" corpus. Now switch
to a different corpus: open the corpus dropdown and select "The Odyssey".
Type a similar prompt (e.g. "Tell me the story of a brave warrior who
questions the meaning of duty") in the new journey input and click
"Start New Journey". Wait for the stream to complete (up to 60 seconds).
Verify the story text references Greek mythology or Odyssey-related
content (e.g. Odysseus, Ithaca, Penelope, Trojan War) rather than
Mahabharata content (e.g. Yudhishthira, Arjuna, Kurukshetra). The
reading panel should show "Complete" status and the graph should render
new nodes.

## 30. Discover and select a user from the backend
depends_on: none
status: unimplemented

Open the username dropdown. Look for "Mehrab" in the list.

"Mehrab" exists on the backend at `saved_graphs/Mehrab/` but was NEVER
typed or added via the username dropdown during this Playwright session
(only "agent-tester" was added in test 1). This means "Mehrab" can only
appear in the dropdown if the frontend fetches usernames from the backend
— not from localStorage.

If "Mehrab" is visible in the dropdown list, select it. Confirm the
dropdown closes and shows "Mehrab", then check that the journey dropdown
loads Mehrab's saved journeys. This is a PASS.

If "Mehrab" is not visible in the dropdown at all, this is a FAIL —
the app is only reading localStorage and has no backend user discovery.

Do NOT skip this test for any reason related to localStorage state.
The condition is already satisfied: this session has never added "Mehrab"
to localStorage.

Note: implementation requires a backend endpoint (e.g. `GET /api/journeys/users`)
that scans `saved_graphs/` directories, and frontend changes to fetch and
merge those usernames into the dropdown on load.

## 31. Placeholder node appears immediately when generation starts
depends_on: 13
status: unimplemented

This test verifies that a placeholder story node is added to the graph
the moment a prompt is submitted — before streaming completes — so the
user has a visual anchor even if they close the reading panel.

**Setup:** Close the reading panel if open. Navigate to a choice node
that has not yet been explored (from story-2's choices, from test 13).
Click it to expand it.

**Step 1 — Submit and immediately close panel:**
Click "Continue Journey". Within 2-3 seconds (while streaming is still
in progress), click the X or close button on the reading panel to
dismiss it. Do NOT wait for streaming to complete.

**Step 2 — Verify placeholder node on graph:**
Take a screenshot of the graph immediately after closing the panel.
Expect a new placeholder story node to already be visible in the graph,
connected to the choice node that was clicked. The node may show a
loading indicator, spinner, or empty content — but it must be visibly
present on the graph canvas. If no new node appears at all, this is a
FAIL.

**Step 3 — Reopen via placeholder:**
Click the placeholder story node. Expect the reading panel to reopen
and resume showing the streaming text (or the completed story if
streaming finished while the panel was closed). If clicking the
placeholder does nothing or the panel does not reopen, this is a FAIL.

**Step 4 — Verify final state:**
Wait for streaming to complete (up to 60 seconds from submission).
Take a screenshot. The placeholder node should now display the real
story content (or still show a loading state if streaming is ongoing).
Choice nodes should appear below it once streaming completes.

Note: implementation requires the frontend to optimistically insert a
placeholder node into the graph as soon as the SSE connection opens,
before any story content arrives. The placeholder should be clickable
and reopen the reading panel. Once the stream completes, the placeholder
updates in-place with the real content and its choice nodes.

## 32. Verify story nodes display generated images
depends_on: 7
status: unimplemented

After a journey has been generated and the graph is visible, examine each
story node. Expect every story node to display a generated image (e.g. an
illustration related to the story content). The image should be visible
within or adjacent to the story node in the graph — not just a placeholder
or empty space.

Take a screenshot and verify that at least the first story node shows a
rendered image. If story nodes show no images or only broken image icons,
this is a FAIL.

Note: implementation may require the backend to generate images during
story creation (e.g. via an image generation API) and return image URLs
in the story response. Images should be saved in a separate folder (e.g.
`saved_images/{username}/`) rather than inline in the graph JSON. The
graph metadata should store image path references (e.g.
`"image": "saved_images/agent-tester/abc123.png"`) so the frontend can
fetch and render them. This separation allows stale images to be cleaned
up independently without modifying graph data. The frontend story nodes
need to render these images using the paths from the graph.
