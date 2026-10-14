# Module 07 verification

Date : 14 October 2026. Environment : the repository's locked Python 3.12
environment, `langgraph` 1.2.15, `langchain` 1.4.5 and `deepagents` 0.7.24.
Model calls use the shared `llm`, `openai/gpt-6-luna` through OpenRouter,
temperature zero, reasoning off. Every notebook run used `COURSE_RPS=0.05`.
No shared configuration or packages outside owned paths were modified.

## Files written

- `src/slides/07-advanced-workflows/07-advanced-workflows.md`
- `build/make_module07.py`
- Six executed notebooks in `notebooks/07-advanced-workflows/` :
  - `demo01-interrupts.ipynb`
  - `demo02-interrupts-in-multi-agent.ipynb`
  - `demo03-human-in-the-loop-middleware.ipynb`
  - `demo04-loop-detection.ipynb`
  - `demo05-retries-and-fallbacks.ipynb`
  - `demo06-composition-and-durability.ipynb`
- `build/measurements-07.md`

Stray scratch file `notebooks/07-advanced-workflows/run-demo01.json` was deleted.
Runtime checkpoint file `workflow-checkpoints.sqlite` created during notebook
execution was cleaned up so only delivery artifacts remain.

## Notebook execution

Built with `build/make_module07.py` and executed with `build/run_notebook.py`
under `COURSE_RPS=0.05`. Outputs were read with `show_outputs.py` and direct
JSON inspection.

| notebook | status | errors | elapsed seconds | model calls | input tokens | output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| demo01-interrupts | PASS | 0 | 46.0 | 2 | 330 | 318 |
| demo02-interrupts-in-multi-agent | PASS | 0 | 85.0 | 4 | 516 | 271 |
| demo03-human-in-the-loop-middleware | PASS | 0 | 125.0 | 6 | 908 | 129 |
| demo04-loop-detection | PASS | 0 | 66.0 | 3 | 351 | 63 |
| demo05-retries-and-fallbacks | PASS | 0 | 46.0 | 2 | 145 | 86 |
| demo06-composition-and-durability | PASS | 0 | 66.0 | 3 | 286 | 158 |

Observed outputs :

- **demo01 · interrupts** :
  - Pausing with `interrupt` halts before the `send` node. Payload returns the
    review options `['approve', 'edit', 'reject']` and draft text.
  - Resuming with approve routes to `send` and writes `sent`.
  - Resuming with edit updates the draft text directly without a model call.
  - Resuming with reject updates `feedback` and loops back to rewrite.
  - Sequential interrupts pause one after another in order. Parallel nodes in
    one step emit distinct interrupt IDs and resume via `{item.id: reply}`.
- **demo02 · interrupts-in-multi-agent** :
  - Child graph compiled without a checkpointer pauses on approval. The parent
    invocation receives the child interrupt directly in `out.interrupts`.
  - `parent.get_state(cfg, subgraphs=True)` exposes `child next: ('approval',)`.
  - Resuming parent thread delivers approval into the child graph.
  - Wrapping the child in a subagent tool pauses the supervisor graph in `tools`.
    Resuming re-enters the tool function (2 executions observed), delivers the
    resume value, and returns a verified `ToolMessage`.
- **demo03 · human-in-the-loop-middleware** :
  - `HumanInTheLoopMiddleware` intercepts `reserve_part` calls before execution.
  - Pending interrupt exposes `action_requests` and `review_configs`.
  - Approve executes the tool and records 2 reserved parts.
  - Edit overrides quantity to 1 via `edited_action.args`, verified in reservations.
  - Reject injects an error tool message; tool is not executed and model stops.
- **demo04 · loop-detection** :
  - Model proposes diagnostic actions on unchanged evidence. Watchdog node
    tracks stalled progress and routes to `manual review queued` on turn 2.
  - Deliberately unbounded spin node hits `GraphRecursionError` at recursion limit 4.
  - Duplicate tool guard computes canonical `(name, args)` signature. Replayed
    read is intercepted with an error `ToolMessage`, blocking database execution.
- **demo05 · retries-and-fallbacks** :
  - `RetryPolicy` catches injected `ConnectionError` on remote stock lookup.
    Three attempts recorded with measured backoff intervals (0.101 s, 0.200 s).
  - Multi-tier fallback chain: live lookup fails -> local snapshot succeeds for
    known part CE-CF-02 -> manual review succeeds for unknown part.
  - Model generates summary preserving provenance and disallowing reservations.
- **demo06 · composition-and-durability** :
  - Lookup workflow and report workflow composed into parent graph with schema mapping.
  - Conditional branching routes error code `F-CE-110` to `electric` queue;
    unknown code routes to default `manual` queue.
  - Injected worker crash after `prepare` node saves state in SQLite checkpointer.
    Restarting graph and invoking with `None` resumes `finish` without repeating
    the model call in `prepare`.
  - Cooperative drain requested via `RunControl`. Graph raises `GraphDrained`
    after `prepare` completes; restarting and resuming executes `finish`.

## Slide and section checks

- Slide count: 22 slides, counted from Markdown slide headings in
  `src/slides/07-advanced-workflows/07-advanced-workflows.md`.
- All 13 course-map demo sections are present in their specified order,
  with 13 matching demo pills and 1 exercise pill (`exercise07 · Approval in a Subagent`).
- Pills and sections match bidirectionally:
  - `demo01 · interrupts` -> `a · interrupt`
  - `demo01b · approve-edit-reject` -> `b · approve-edit-reject`
  - `demo01c · several-interrupts` -> `c · several-interrupts`
  - `demo02 · interrupts-in-multi-agent` -> `a · in-a-subgraph`
  - `demo02b · in-a-subagent` -> `b · in-a-subagent`
  - `demo03 · human-in-the-loop-middleware` -> `a · approval-policy`
  - `demo04 · loop-detection` -> `a · watchdog-node`
  - `demo04b · repeated-tool-calls` -> `b · repeated-tool-calls`
  - `demo05 · retries-and-fallbacks` -> `a · backoff`
  - `demo05b · fallback-chain` -> `b · fallback-chain`
  - `demo06 · composition-and-durability` -> `a · composing-workflows`
  - `demo06b · branching-at-scale` -> `b · branching-at-scale`
  - `demo06c · resuming-after-a-crash` -> `c · resuming-after-a-crash`
  - `exercise07 · Approval in a Subagent` closes the deck on the Summary slide.
- Module Puppeteer lint passes with zero warnings:
  ```powershell
  bun run --cwd build lint -- C:/Git/courseWare/Multi-Agents-LangGraph/src/slides/07-advanced-workflows/07-advanced-workflows.md --verbose
  ```
  All 22 slides rendered within the 800px height limit with no overflows.
- House-style lead-in share: 0 of 28 top-level bullets (0%). No parent bullet
  introduces a single child bullet.
- No bold emphasis in bullet prose, no em-dashes, no rhetorical questions in bullets.
- Website outline terms present: human-in-the-loop, approval flows, branching,
  loop detection, retries, fallbacks, subgraphs, workflow composition.
- Closing slide: `Summary : Advanced Workflows`.

## API checks and documentation boundaries

- `interrupt(payload)`: Checked on `langgraph.types.interrupt`. Requires a checkpointer.
  Returns the resume value when the node re-executes.
- `Command(resume=...)`: Resumes paused node. In LangGraph 1.2.15, resuming
  re-executes the node from the beginning. Statements prior to `interrupt` execute
  again, making idempotency of pre-interrupt tool logic essential.
- Parallel interrupts in one step return a list of `Interrupt` objects with unique
  `.id` values. Resuming requires passing `{id: reply}` to `Command(resume=...)`.
- Subgraphs: When a child graph is compiled without a checkpointer, the parent
  checkpointer handles state persistence. `get_state(..., subgraphs=True)` exposes
  child task state.
- `HumanInTheLoopMiddleware`: Gating tool execution using `interrupt_on`.
  Returns `action_requests` and `review_configs`. The resume payload expects
  `{"decisions": [{"type": "approve" | "edit" | "reject", ...}]}`. For edits,
  the dictionary key is `edited_action` with `args`, overriding model arguments.
- Loop bounds: `recursion_limit` controls maximum Pregel supersteps and raises
  `langgraph.errors.GraphRecursionError`. Application loop detection uses state
  tracking in watchdog nodes to route stalled runs before hitting the hard bound.
- `RetryPolicy`: Configured on graph nodes with `initial_interval`, `backoff_factor`,
  `max_interval`, `jitter` and `retry_on`.
- Fallbacks: Implemented via `RunnableLambda(...).with_fallbacks(...)` with
  explicit `exceptions_to_handle`.
- Durability: `SqliteSaver` persists state across crashes. Reopening the database
  and invoking with `None` resumes the pending node. Completed nodes and their
  model calls are not repeated.
- Graceful drain: In LangGraph 1.2.15, `runtime: Runtime` provides cooperative
  draining via `runtime.control.request_drain()`. LangGraph raises `GraphDrained`
  after the active node completes and checkpoints its state.
