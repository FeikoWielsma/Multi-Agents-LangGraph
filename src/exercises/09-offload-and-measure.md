---
footer: Deep Agents
---

# Exercise 09 : Offload and Measure

Open `exercises/exercise09-offload-and-measure.ipynb` and run the setup cell. This exercise is optional. You compare Aurelia manuals exports with and without offloading, then total ticket hours in QuickJS ; the solution is `solutions/exercise09-offload-and-measure.ipynb`.

Worked examples to revisit : `demo03b · offloading-large-results`, `demo05b · the-interpreter`.

Made up, not from work. The Aurelia manuals and tickets are fictional.

---

### Step 1 : Raw export

Run the helpers and the `plain` agent with `all_manuals`, then the check. Read `raw_chars`, the model's answer and the metrics saved in `no_offload`.

How close is the model's estimated export size to `raw_chars`?

### Step 2 : Offloading

Fill `tool_token_limit_before_evict` in `FilesystemMiddleware` with a threshold low enough to offload the export. Keep `deny_reread` and `capture_tool_results`. Run `offloader`, then the check, and compare `captured` with `saved paths`.

What does the model receive in place of the full export?

### Step 3 : QuickJS

Run `analyst` with `CodeInterpreterMiddleware` and the `ticket_rows` PTC tool on the supplied S01 request. Replace the final blank with an assertion that `computed` matches `expected` for `count` and `hours`, then run the check.

Which ticket count and hours total do the sandbox and Python report?

### Step 4 : Measurements

Run the cell that prints `rows` as a table. Replace its final blank with assertions that `offload_tool_chars` is less than half of `raw_chars` and that `quickjs` recorded input tokens.

How do input tokens and tool-message characters compare between `no_offload` and `offload`?

### If time permits

- Raise the eviction limit until offloading stops, and find the threshold on this export
- Ask QuickJS for a breakdown by `error_code` at site `S03`
- Offload `ticket_rows` itself and compare with the interpreter path
