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

## 14. Navigate to an unexplored choice from the first story
depends_on: 13

Close the reading panel if open. Navigate or scroll back in the graph to
the first story node's choice nodes. Identify one of the choice nodes that
was NOT used in test 11 (i.e. not the one that led to the second story).
Click it to expand it.

## 15. Start a second branch from an earlier choice
depends_on: 14

With the unexplored choice node expanded, edit the prompt if desired and
click "Continue Journey". Expect the reading panel to open with new
streaming text. Wait for the stream to complete (up to 60 seconds). The
graph should now have 3 story nodes — two branching from the original
story's choice nodes.

## 16. Verify branching graph structure
depends_on: 15

Take a snapshot of the graph. Expect 3 story nodes: the original story,
plus two branches from its choice nodes. Each branch's story node should
have its own set of choice nodes. The graph should show a tree shape, not
a linear chain.

## 17. Continue the second branch deeper
depends_on: 16

Click a choice node from the newest story (on branch 2, created in test
15). Edit the prompt and click "Continue Journey". Wait for the stream to
complete (up to 60 seconds). Expect a 4th story node, making branch 2
two levels deep.

## 18. Jump back to branch 1 and continue
depends_on: 17

Navigate back to branch 1 (the Aswatthaman story from test 11). Find an
unexplored choice node from that story and click it to expand. Edit the
prompt and click "Continue Journey". Wait for the stream to complete (up
to 60 seconds). Expect a new story node on branch 1. The graph should now
have 5 story nodes across 2 branches, each 2+ levels deep.

## 19. Verify full graph structure
depends_on: 18

Take a snapshot of the full graph. Expect 5 story nodes with correct
parent-child connections across both branches. Each story node should have
choice nodes branching from it. The total edge count should reflect the
full tree structure.

## 20. Reload the page
depends_on: 15

Reload the browser page to clear in-memory state. Expect the app to load
with username "agent-tester" pre-selected (persisted in localStorage),
while persona resets to its default value from the API.

## 21. Select username "agent-tester" after reload
depends_on: 20

Verify the username dropdown shows "agent-tester" (pre-selected from
localStorage). If not pre-selected, select it from the dropdown.

## 22. Verify journey dropdown shows saved journeys
depends_on: 21

After the username is set, check that the journey dropdown loads and
displays a list of saved journeys for "agent-tester". Expect at least one
journey entry from the earlier test run.

## 23. Load a saved journey
depends_on: 22

Select the most recent saved journey from the journey dropdown. Expect the
graph to render with the journey's nodes and edges.

## 24. Verify loaded journey graph
depends_on: 23

Take a snapshot of the loaded graph. Expect it to contain the full
branching structure from the earlier test run — multiple story nodes
across branches with correct connections.

## 25. Attempt empty prompt submission
depends_on: 1

Clear the journey prompt input and attempt to click "Start New Journey".
Expect the button to be disabled or the submission to be rejected — no
stream should start and no reading panel should appear.

## 26. Trigger a stream error
depends_on: 1
status: unimplemented

Attempt to start a journey with conditions that trigger a backend error
(e.g., select an invalid corpus if possible). Expect an error message to
appear in the UI with a "Dismiss" button. Note: the exact trigger
mechanism may need to be determined during implementation — this test
tracks error handling coverage.

## 27. Switch corpus and verify story reflects new source material
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
