
## Exercises 05 to 07

Built and executed 14 October 2026 on Windows with `uv run ...` from the repository root. Model : `openai/gpt-6-luna` through OpenRouter, temperature 0, reasoning effort `none`, `COURSE_RPS=0.06`, `max_retries=0`. Installed packages inspected before building : LangChain 1.4.5, LangGraph 1.2.15, langgraph-api 0.16.0. Solution notebooks ran one at a time. No connection error or rate-limit retry occurred.

The notebook counter counts chat-model starts and sums returned input and output usage. Exercise 05 instead sums the persisted `usage_history` lists from both Agent Servers, so its served model calls are included. Notebook seconds start after the shared setup cell and include rate limiting, startup and shutdown. Runner seconds also include kernel and setup overhead. Neither is model latency.

### Exercise 05 : Two Agents over A2A

- First run : PASS, 0 errors ; notebook 122.6 s, runner 125.3 s ; 4 calls, 471 input tokens, 135 output tokens, 606 total tokens.
- Final run after making the editable graph-source cells multiline : PASS, 0 errors ; notebook 158.0 s, runner 160.7 s ; 4 calls, 467 input tokens, 131 output tokens, 598 total tokens. Final outputs are saved in the solution.
- Both cards advertised JSONRPC 1.0. The assistant UUIDs were discovered through `/assistants/search`, not hardcoded. The desk called the specialist with plain httpx JSON-RPC from inside its served graph. Each server allocated a different task id in the same UUID context.
- The first handover reported CT-FN-02 stock 6 and CT-SR-03 stock 0, both at Houten. The follow-up identified CT-SR-03 as out of stock. These counts and locations match the read-only Aurelia inventory.
- The second message reached both servers through the desk in the same context. `GetTask` returned keys `contextId`, `history`, `id`, `kind`, `status`, without artifacts. Task-only history contained 2 entries and full-context history 4. This is response-history selection, not a restriction on model input.
- Both process trees stopped in the final cell. Ports 2124 and 2125 were released. Servers used `--no-browser`, `--no-reload` and `--allow-blocking`. Runtime graph files, configurations and server storage live under the already-ignored `**/workspace/` path. Server stdout and stderr are discarded ; no environment values are written to generated source or logs.
- Readiness deadline 90 s, HTTP task timeout 240 s, shutdown timeout 20 s and delays of `1 / COURSE_RPS` before and after each remote call are lab settings. The delays space requests across the two process-local model limiters.

### Exercise 06 : Buyer and Seller

- Run : PASS, 0 errors ; notebook 135.2 s, runner 137.9 s ; 8 calls, 1,934 input tokens, 194 output tokens, 2,128 total tokens.
- Problem shape : price negotiation for a fixed three-unit MR-HF-01 filter order. Aurelia stock is 9 at Venlo and catalogue price is 310 EUR. Opening prices and limits are fictional lab inputs : buyer 210 EUR opening and 280 EUR ceiling ; seller 300 EUR opening and 240 EUR floor.
- Observed opening offers were buyer 210 and seller 300, producing review for non-overlap. Round 2 produced buyer 280 and seller 240. The deterministic midpoint rule produced a draft at 260 EUR per unit, total 780 EUR, with `external_action` false.
- Both proposals survived the list reducer and join. Only role and proposed unit price crossed into the other agent's next task. Private transcripts and policy fields were omitted from the shared negotiation state. Each agent called only its own policy tool.
- Buyer and seller tools both exposed empty argument schemas ; the principal came from trusted `ToolRuntime` context. A buyer read of the seller policy raised `PermissionError`. A seller role with the buyer credential scope was also denied. The fixtures checked overlapping prices, non-overlap and stock overflow. The database stayed unchanged.
- The access checks model service authorisation inside one Python process. They do not prevent the notebook author from inspecting Python memory. A public proposed price can equal a private limit without granting access to the private policy field. Production isolation requires service identities and downstream authorisation.

### Exercise 07 : Approval in a Subagent

- Run : PASS, 0 errors ; notebook 151.8 s, runner 154.4 s ; 9 calls, 1,336 input tokens, 192 output tokens, 1,528 total tokens.
- The ARI510 exercise13 parts and reviewer case is reworked into a child graph called by the supervisor's `parts_specialist` tool, following module 07 demo02b. Every order pauses. The supplied reviewer rule selects the lead up to 10,000 EUR and the manager above that amount.
- All three interrupts surfaced at the top-level supervisor, whose next node was `tools`. The ledger was empty before any approval. The child compiled without its own saver ; the supervisor owned `InMemorySaver` and propagated the nested invocation configuration.
- Approval recorded five MR-HF-01 filters, 1,550 EUR. Editing reduced the CT-FN-02 fan request from three units, 1,260 EUR, to one unit, 420 EUR. Rejection returned the manager's reason for the CT-DM-04 detector request, 12,900 EUR, without recording an order.
- Tool-wrapper and child-review entry counts were 1 before resume and 2 after resume for every request. Each accepted order had one ledger entry, using the order id as a local idempotency key. The ledger contained 2 entries and no detector order. Actions were simulated ; the Aurelia database was never changed.
- The child model notes stated that no order had been recorded. The structured interrupt payload, rather than that short note, carried part, quantity, total and reviewer. Completed preparation stayed checkpointed while the paused wrapper and review node replayed.

### Files and checks

- Builder : `build/make_exercises_05_07.py`, with `--only 5 6 7` for selective regeneration through `nb.write_exercise`.
- Guides : `src/exercises/05-two-agents-over-a2a.md`, `06-buyer-and-seller.md`, `07-approval-in-a-subagent.md`.
- Starters : `exercises/exercise05-two-agents-over-a2a.ipynb`, `exercise06-buyer-and-seller.ipynb`, `exercise07-approval-in-a-subagent.ipynb`.
- Solutions : the same three notebook filenames under `solutions/`, executed with outputs for every code cell and zero stored errors.
- Guides each have 5 steps, a question per step, 3 optional extensions, and 7 Marp pages. The action-first opening follows the winning house style. No module slides were edited.
- Scoped lint : `bun run --cwd build lint ../src/exercises/05-two-agents-over-a2a.md ../src/exercises/06-buyer-and-seller.md ../src/exercises/07-approval-in-a-subagent.md` passed, including page height. All six notebooks parsed. Starters have no outputs. Every solution code blank is filled. The owned files passed a scan against secret values from `.env`, without printing those values. Runtime JSON reports and metrics are already gitignored.
- Installed API observations agree with `build/measurements-06.md` : cards and A2A paths require assistant UUIDs, contexts require UUIDs, `SendMessage` wraps `result.task`, and `GetTask` returns the task directly without answer artifacts. No additional package discrepancy was found.
- Open questions for the lead : none. No change to shared helpers, dependencies or ignore rules was needed. The PDF build was not run.

## Exercises 08 to 11

Built and executed 14 October 2026 on Windows with `uv run ...` from the repository root. Round 2 the same day. Model : `openai/gpt-6-luna` through OpenRouter, temperature 0, reasoning off, `COURSE_RPS=0.07`, `max_retries=0`. Installed packages verified before building : `deepagents` 0.7.24, `langchain-quickjs` 0.3.9, `agentevals` 0.0.9, `langgraph-api` 0.16.0 (see also `build/measurements-09.md`). Solution notebooks ran one at a time. No connection-error retry was required. No key from `.env` was printed or written. The PDF build was not run.

### Exercise 08 : A Deep Agent

- Run : PASS, 0 errors ; runner 120 s (round 2 restore after builder regen) ; earlier measured `deep-aurelia` 10 calls, 38,490 input tokens, 474 output tokens, 145.4 s.
- Aurelia problem (not Veenhaven) : E-CT-110 briefing plus CT-FN-02 stock. `create_deep_agent` with `TodoListMiddleware`, `CompositeBackend` routing `/manuals/` to `FilesystemBackend`, one student-written `error-briefing` skill, and one dict `parts` subagent.
- Observed tools : `write_todos`, `read_file`, `ls`, `task`, `write_file`. Todos completed ; `/briefing.md` written ; stock 6 at Houten. `seen_by_parts` captured the subagent human message only (task description), not the parent skill text.
- API note : `FilesystemBackend.read` returns `ReadResult` with `file_data["content"]` ; `ls` returns `LsResult` with `entries`. Plan with a recursion limit of 36 and a pinned skill ; the first draft at limit 20 hit `GRAPH_RECURSION_LIMIT`.

### Exercise 09 : Offload and Measure (optional)

- Run : PASS, 0 errors ; runner 92 s (round 2 restore after builder regen).
- Table from the solution notebook :

| path | input tokens | calls | seconds | tool chars seen |
| --- | --- | --- | --- | --- |
| no offload | 9151 | 2 | 31.6 | 18623 |
| offload | 4351 | 2 | 27.9 | 897 |
| quickjs tickets | 5576 | 2 | 28.1 | n/a |

- Offloading with `tool_token_limit_before_evict=600` plus a deny on `/large_tool_results/**` reads kept the model on the preview. Without that deny, an earlier run re-read the export (`read_file` three times) and *raised* input tokens (11,898 vs 9,151) despite a shorter first tool message.
- QuickJS (`langchain-quickjs` 0.3.9) over `data/capstone/tickets.csv` : sandbox `{"count": 2, "hours": 3.5}` matched Python for site S01 with empty `parts_used`.

### Exercise 10 : Evaluating a System of Agents

- Round 2 run : PASS, 0 errors ; runner 722 s. Six selected cases from `data/capstone/eval.jsonl` : db-01, db-03, man-01, man-07, mix-01, mix-02. Desk final-answer score 6/6. `recursion_limit` 24 (one earlier rerun at 16 hit `GRAPH_RECURSION_LIMIT` on a tool loop).
- Main trajectory score uses `tool_args_match_mode="ignore"`. Live case is `man-01` (single `search_manuals`) : strict False, unordered True. `db-01` often over-calls `run_sql`, so both modes stay False even with ignore and teach nothing about order.
- Trajectory fixtures (`agentevals` 0.0.9) : strict and unordered both True on reordered calls inside one assistant message ; both False on a one-call output against a two-call reference. Agrees with `build/measurements-09.md`.
- Argument matching moved to "If time permits" : empty reference args fail against a live model for the wrong reason.
- Per agent : parts and manuals passed their single-tool cases on facts ; against mix-01 expected tools each specialist failed `tools_ok` (only one tool) while the desk passed facts and tools.

### Exercise 11 : An Async Subagent on a Server

- Round 2 run : PASS, 0 errors ; runner 204 s. Port 2134 only, `--no-browser`, `--n-jobs-per-worker 8`. Notebook cells write `course_runtime.py`, `graphs.py` and `langgraph.json` at run time (gitignored under `exercises/` and `solutions/` ; only `.ipynb` is committed).
- Lifecycle : `start_async_task`, `check_async_task`, `list_async_tasks`, then `runs.join` and a final check. First check status printed and asserted `running`. Final status `success`. Answer preserved E-CT-110 first action and CT-FN-02 stock 6 at Houten. Server stopped in the final cell ; port released.
- Worker hold is 120 s unless the task text contains `NO DELAY`. Matching on the word `DELAY` alone is unreliable : the supervisor may paraphrase the launch text and drop it, so a 30 s hold finished before the first check (~57 s under `COURSE_RPS=0.07`). Behaviour matches `measurements-09.md` for co-deployed ASGI async subagents on `deepagents` 0.7.24 / `langgraph-api` 0.16.0.

### Files

- Builder : `build/make_exercises_08_11.py` only (`build/_make_exercise11.py` removed ; exercise 11 inlined).
- Guides : `src/exercises/08-a-deep-agent.md`, `09-offload-and-measure.md`, `10-evaluating-a-system-of-agents.md`, `11-an-async-subagent-on-a-server.md` (10 and 11 linted).
- Starters and solutions : `exercises/exercise08-a-deep-agent.ipynb` through `exercise11-an-async-subagent-on-a-server.ipynb` and the matching `solutions/` notebooks (10 and 11 re-executed, 0 errors ; starters without outputs).

## Exercises 01 to 04

Built and executed 14 October 2026 on Windows with `uv run ...` from the repository root. Model : `openai/gpt-6-luna` through OpenRouter, temperature 0, reasoning effort `none`, `COURSE_RPS=0.05`. LangChain 1.4.5, LangGraph 1.2.15. Solution notebooks ran one at a time. No connection error. Token counts are `usage_metadata` on the course model, summed below. Runner seconds include kernel startup. Exercise 02 makes no model call.

### Exercise 01 : Graphs and Loops

- Run : PASS, 0 errors, runner 105 s. 5 calls, 211 input tokens, 99 output tokens, 310 total tokens.
- Router : two calls, 39 input and 5 output tokens each. High ticket routed to `page_engineer`, low ticket to `queue`. The route matched the priority label.
- Shorten loop : three calls (76, 73 and 73 total tokens). Lengths stayed at 125, 123 and 122 characters. The attempt cap stopped the loop. The check accepts that stop.
- `Command` : no model call. High went to `page` and wrote `engineer paged`. Low went to `queue`.

### Exercise 02 : State for Two Agents

- Run : PASS, 0 errors, runner 3 s. 0 calls, 0 tokens.
- Parallel writes to `note` raised `InvalidUpdateError`. With `operator.add`, both findings were kept and both nodes read the same keys.
- Triage's input keys were `symptom` and `ticket_id`. Parts also received `stock_note` (`CT-SR-03 slip ring brush kit stock 0 at Houten`). `invoke` omitted `stock_note`. The values stream still showed it.
- Thread `T-1001` kept 4 checkpoints. The newest has `next` empty and both findings.

### Exercise 03 : An Agent with Tests

- Run : PASS, 0 errors, runner 48 s. Live run : 2 calls, 201 input tokens, 40 output tokens, 241 total tokens. Pytest : 3 passed in 0.45 s, no network call.
- `part_stock` returned `0` for `CT-SR-03` and `Unknown part` for `UNKNOWN`.
- The scripted agent produced one tool message, content `0`, `tool_call_id` `stock-1`.
- `ModelCallLimitMiddleware(run_limit=1, exit_behavior="end")` allowed the first model call and the tool, then ended with `Model call limits exceeded: run limit (1/1)`.
- The live agent, `run_limit=4`, called the tool and answered that stock is 0. The limit did not stop it.

### Exercise 04 : A Multi-Agent Visit Planner

- Run : PASS, 0 errors, runner 206 s.
- Planner : 8 calls, 4,963 input tokens, 764 output tokens, 5,727 total tokens, 162.7 s inside the timed section. Round 1 passed the checker. The parts subagent reported WO-9003, `MR-CH-02`, stock 0, depot Venlo. The plan names both S04 serials and says the cold head is out of stock.
- One agent : 2 calls, 1,469 input tokens, 400 output tokens, 1,869 total tokens, 40.4 s. Checker problems empty. It also names WO-9003 and `MR-CH-02` as out of stock, and `UX-BT-02` as out of stock. It reported that the manual search returned CT-400 pages.
- On this visit the router used more calls and tokens than the one agent. Both plans passed the three code checks. The checker does not judge the maintenance sentences.
- Handoffs are not on the required path. The two demo04 fixes (no parallel tool calls, forward the full worker history) are an optional closer and were not executed.

### Package notes

- A `@tool` function is a `StructuredTool` on this pin and is not callable. `run_sql.invoke({"query": ...})` is the call that works. Calling it as a function raises `TypeError`.
- `GenericFakeChatModel.bind_tools` still raises `NotImplementedError`. The subclass returns `self`, as in module 04 demo07.
- An inner agent with `recursion_limit` 4 hit `GraphRecursionError` before a final answer. Limit 10 completed one tool call and an answer.
- `work_orders` has no `site_id`. A SELECT filtered by site on that table returns no rows. The parts question joins `work_orders` to `devices` on `serial`. Status `waiting for part` is not `closed`.

### Files

- Builder : `build/make_exercises_01_04.py`
- Guides : `src/exercises/00-setup.md`, `01-graphs-and-loops.md`, `02-state-for-two-agents.md`, `03-an-agent-with-tests.md`, `04-a-multi-agent-visit-planner.md`
- Starters and solutions : `exercises/exercise01-graphs-and-loops.ipynb` through `exercise04-a-multi-agent-visit-planner.ipynb`, and the matching `solutions/` notebooks

### Open questions for the lead

- The shorten loop did not get under 60 characters. The cap is the stop. Leave it, or tighten the prompt so a run usually finishes sooner?
- Exercise 04 compares a router of two subagents with one agent. On this run the one agent was cheaper and both passed. No change requested unless the lead wants the router to be the cheaper design.
