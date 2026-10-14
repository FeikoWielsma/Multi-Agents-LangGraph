---
footer: Graph Fundamentals
---

# Exercise 01 : Graphs and Loops

Open `exercises/exercise01-graphs-and-loops.ipynb` and run the setup cell. You route Aurelia service tickets through four small graphs by replacing the `____` blanks ; the solution is `solutions/exercise01-graphs-and-loops.ipynb`.

Worked examples to revisit : `demo02 · nodes-and-edges`, `demo03 · routing`, `demo04 · command-and-send`, `demo06 · a-model-in-a-node`.

Made up, not from work. The Aurelia tickets and sites are fictional.

---

### Step 1 : Linear graph

Add the `stamp` node and its three edges : `START` to `normalise`, `normalise` to `stamp`, `stamp` to `END`. Run the cell on the messy T-1001 slip ring ticket, then the check.

What happens if you remove the edge to `END` and compile again?

### Step 2 : Router

`prioritise` asks the model for `high` or `low`. Complete `route` so a high ticket goes to `page_engineer` and a low ticket to `queue`, and connect it to `prioritise` with the missing `router` method.

Which route did the stopped gantry get, and which the fan procedure request? Why does `route` declare its return type as `Literal["page_engineer", "queue"]`?

### Step 3 : Loop

`shorten` rewrites the Kanaalzicht gantry ticket in fewer words. Complete `again` : end when the text is at most 60 characters or after three attempts, otherwise return `"shorten"`.

Read the printed lengths. Which condition ended the loop, and what would `again` do on this ticket without the attempt cap?

### Step 4 : Command

`triage` already knows the priority. Return a `Command` that stores `target` on `assigned` and goes to `target`.

Which node ran for the high ticket, and what does `assigned` hold?

### If time permits

- Print `router_graph.get_graph().draw_mermaid()` and compare it with the router slide
- Give the loop in Step 3 a `recursion_limit` of 2 and read the error
- Fan out with `Send`, one branch per site from S01 to S04, and collect the site ids
