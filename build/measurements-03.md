# Module 03 verification

Date : 13 October 2026. Environment : the repository's locked Python 3.12
environment, LangGraph 1.2.15 and LangChain 1.4.5. Model calls use the shared
`llm`, `openai/gpt-6-luna` through OpenRouter, temperature zero, reasoning off.
Every notebook run used `COURSE_RPS=0.05`. No shared configuration was changed.

## Files written

- `src/slides/03-state-management/03-state-management.md`
- `src/slides/03-state-management/images/state-reducers.svg`, copied from ARI510
- `src/slides/03-state-management/images/checkpoint-fork.svg`, ported from ARI510
  with review renamed to record for the new graph
- `build/make_module03.py`
- Six executed notebooks in `notebooks/03-state-management/`
- `notebooks/03-state-management/run-status.json`
- This report

SQLite runtime files `module03.db` and `delta-probe.db` are inside the owned
notebook folder. `git check-ignore` confirms that both match the existing
`notebooks/**/*.db` rule. They are not delivery artifacts.

## Notebook runs

Built with `uv run python build/make_module03.py`, executed with the shared
`build/run_notebook.py`, then outputs read with `show_outputs.py` and direct
JSON inspection where that helper truncates a cell's output. The final demo06
was rebuilt and rerun after adding a nested graph for lifecycle events.
The raw runner results are in the owned `run-status.json`.

| notebook | status | errors | final elapsed seconds |
| --- | --- | --- | --- |
| demo01-state-schemas | PASS | 0 | 2.4 |
| demo02-reducers | PASS | 0 | 2.3 |
| demo03-checkpointers | PASS | 0 | 83.9 |
| demo04-history-and-time-travel | PASS | 0 | 44.4 |
| demo05-the-store | PASS | 0 | 2.3 |
| demo06-debugging-with-stream-modes | PASS | 0 | 25.7 |

Elapsed times include kernel startup and the rate limiter. They are execution
records, not model latency claims. No timings or token costs appear on slides.
The first-slide timing of about 75 minutes is a delivery estimate, not a run
measurement. Bus 4012 and the user/thread ids are illustrative identifiers.
BT-1001, its 2.5 hours and its symptom come from `data/demo-world/tickets.csv`.

Observed outputs :

- TypedDict retains untouched keys. Dataclass state supplies `status="new"`.
  Pydantic rejects negative hours on node input with `greater_than_equal`,
  but accepts an invalid final dictionary update. Public output contains only
  status. A private working_note appears in values streaming.
- Message editing retains two messages, replacing the reply by id. Removing
  the request leaves one message. The sequential ARI510 a/b example produces
  `collected=['a', 'b']` and `last='b'`. Custom merging removes duplicate
  findings. Overwrite clears the field. Two parallel branches writing the
  unreduced result key produce the caught InvalidUpdateError. The fixed graph
  retains both workshop findings.
- The same-thread reply names bus 4012 and depot Noord. The new-thread reply
  says the values are unknown. The same-thread snapshot has four messages.
  SQLite saves `next=('record',)`, restores that continuation through a second
  connection and compiled graph, then finishes with `next=()`.
- History is newest first. Replaying before draft adds one live model call.
  Forking after draft adds zero live model calls and records the supplied
  alternative. The original parent checkpoint remains unchanged.
- DeltaChannel reconstructs four accumulated entries and six history
  snapshots in the demonstration. A separate terminal probe checks the same
  result after reopening a SQLite saver, also with six snapshots. These are
  fixture counts, not a storage-size or throughput benchmark.
- Store get, put, replacement, delete and filtered search behave as shown.
  User u1 reads depot West on two different threads; u2 reads depot Zuid.
  The collection filter retrieves BT-1001. No semantic ranking is claimed.
- One live stream emits all seven pinned StreamMode values: values, updates,
  checkpoints, tasks, debug, messages and custom. The final reply acknowledges
  brake inspection at Noord. Root v2 namespaces are empty tuples. v3 values
  expose the counter before and after increment; output is the final state.
  Nested-graph lifecycle events are inspected in the final notebook output.

## Slide and section checks

28 slides, counted from Markdown slide headings. The count exceeds the
approximate 26-slide target to give restoration, inspection and the stream
formats their own slides. All course-map sections are present in their specified
order, with 15 slide pills and 15 corresponding notebook sections. A direct
comparison of pill ids/slugs and section ids/slugs passes in both directions.

Module-only Puppeteer lint passes with no warnings. The verbose run confirms
all 28 slides were rendered within height limits. Command :

```powershell
bun run --cwd build lint -- C:/Git/courseWare/Multi-Agents-LangGraph/src/slides/03-state-management/03-state-management.md --verbose
```

House-style lead-in share is 0 of 140 top-level bullets, measured with the house
guide's algorithm after removing speaker notes. No parent bullet introduces a
single child. Source syntax parses, every notebook code cell has an execution
count, and no error output remains. A PDF build was not run, as directed.

## API checks and documentation boundaries

Before teaching the APIs, installed signatures, docstrings and execution were
checked with `uv run python`, then the actual notebooks verified behaviour.
Sources reviewed : [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api),
[persistence](https://docs.langchain.com/oss/python/langgraph/persistence),
[time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel),
and [streaming](https://docs.langchain.com/oss/python/langgraph/streaming).
ARI510 source attribution is included in speaker notes and notebook prose.

- Pydantic validation applies when node input is constructed. It does not
  automatically validate the final dictionary returned by invoke. The slides
  state this boundary explicitly rather than suggesting all writes are checked.
- Private schema channels remain visible to values streaming and checkpoints.
  The current Graph API docs agree. No confidentiality guarantee is taught.
- `Overwrite(value=...)` exists. A terminal probe with two parallel Overwrite
  updates confirms InvalidUpdateError. A reduced-list update_state probe
  returns `['input', 'node', 'edit']`, confirming that edits use channel reducers.
  The notebook uses an unreduced draft field and explicit as_node attribution.
- DeltaChannel is exported from `langgraph.channels` and its installed docstring
  labels it beta. Its reducer takes a sequence of writes, not one incoming
  value. The API/on-disk contract is unstable. Reconstruction is checked with
  InMemorySaver and with file-backed SqliteSaver. No size savings are asserted.
- `stream` accepts only v1/v2; v3 is selected through `stream_events`.
  The installed v3 API is experimental. Default projections are values,
  messages, lifecycle and subgraphs. Updates, custom, tasks, debug and
  checkpoints projections require transformer registration on this pin.
  A terminal probe with `UpdatesTransformer` yields the expected update.
  Passing stream_mode or subgraphs to v3 raises TypeError, verified directly.
- A plain root-only graph has no nested lifecycle events. The final demo
  embeds a deterministic graph to show actual started/completed events.
- The v2 values part carries interrupts; other part types need not. In a
  multimode stream the first part may be a checkpoint part and therefore lack
  that field. The slides do not claim all v2 parts have identical keys.

The PostgreSQL integration is not installed: importing
`langgraph.checkpoint.postgres` raises ModuleNotFoundError. No PostgreSQL server
was used. PostgreSQL remains a conceptual, slide-only topic with no executable
API example or runtime verification claim. Shared dependency files were left
untouched. Studio is mentioned in one line and was not launched in this module.
All required local demos are complete; no endpoint failure or unresolved
notebook output remains.
