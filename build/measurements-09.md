# Module 09 measurements

Date : 14 October 2026. Environment : the repository's locked Python 3.12
environment. Installed versions from `importlib.metadata` :
`langgraph` 1.2.15, `langchain` 1.4.5, `deepagents` 0.7.24,
`langgraph-api` 0.16.0, `langgraph-sdk` 0.4.7, `langgraph-cli` 0.4.33,
`agentevals` 0.0.9, `langsmith` 0.14.8.
Model calls use the shared `llm`, `openai/gpt-6-luna` through OpenRouter,
temperature zero, reasoning off. Every notebook run used `COURSE_RPS=0.05`.
Agent Server used ports 2134 and 2135 only, with `--no-browser` and
`--n-jobs-per-worker 8`. No shared configuration or packages outside owned
paths were modified. No keys from `.env` are recorded here.

## Files written

- `src/slides/09-production-deployment/09-production-deployment.md` (30 slides)
- `src/slides/09-production-deployment/images/trust-boundaries.svg` (referenced in speaker notes)
- `build/make_module09.py`
- Eight executed notebooks in `notebooks/09-production-deployment/`
- Runtime helpers required at notebook run time : `course_runtime.py`, `graphs.py`
- `build/measurements-09.md`

## Notebook execution

Built with `build/make_module09.py` and executed with `build/run_notebook.py`
under `COURSE_RPS=0.05`, one notebook at a time. Elapsed times are from
`run_notebook.py` wall clock and include rate limiting and server startup.

| notebook | status | errors | elapsed seconds | notes |
| --- | --- | --- | --- | --- |
| demo01-agent-server | PASS | 0 | 70 | port 2134 |
| demo02-serving-in-practice | PASS | 0 | 180 | port 2134 ; reject 409 ; persist across restart |
| demo03-async-subagents | PASS | 0 | 332 | port 2135 ; five lifecycle tools used |
| demo04-a2a-on-agent-server | PASS | 0 | 50 | port 2135 ; UUID assistant ids |
| demo05-evaluating-agents | PASS | 0 | 204 | final answer, trajectory, judge, per agent |
| demo06-a-langsmith-experiment | PASS | 0 | 84.5 | review rerun ; EU experiment completed ; both per-example scores True |
| demo07-cost | PASS | 0 | 127 | model-per-agent usage and prompt cache |
| demo08-injection-through-an-error | PASS | 0 | 104 | raw error egress then mitigated codes |

## Observed outputs

### demo01 · agent-server

- `langgraph.json` registers `service`, `researcher`, `supervisor`.
- Server ready on 2134 ; Studio URL uses the EU base.
- Assistants : supervisor, researcher, service.
- Stock answer : 6 CE-CF-02 at Rietpoort. Follow-up recalls CE-CF-02 without a new lookup.
- Two successful runs on the thread ; 6 saved messages.

### demo02 · serving-in-practice

- Stream modes observed : `messages|...`, `metadata`, `updates`, `updates|...`.
- Streamed text : 6 CE-CF-02 fans at Rietpoort.
- Double-texting : reject returns HTTP 409 ; enqueue finishes both runs as success.
- After stop and restart in the same directory : 6 messages before and after ; follow-up recalls CE-DA-03 stock 0 at Rietpoort.
- Local storage files under `.langgraph_api` include checkpoint and store pickles (dev persistence, not a production database).

### demo03 · async-subagents

- Prior failure (12:09) : `list_async_tasks` run hit `OpenAIConnectionError` ; `runs.wait` returned without `messages`, so `supervise` raised `KeyError: 'messages'`. Server log `server-2135.log` shows the connection error after retries. Builder now checks for `messages`, sets `raise_error=True`, accumulates lifecycle tool names, and starts with `--n-jobs-per-worker 8`.
- Rerun : start returns a running task id ; check reports running ; update steers to CE-DA-03 ; join then check reports success with 0 stock at Rietpoort.
- Second DELAY task cancelled ; list shows one success and one cancelled.
- Lifecycle tools used : `start_async_task`, `check_async_task`, `update_async_task`, `cancel_async_task`, `list_async_tasks`.

### demo04 · a2a-on-agent-server

- API difference vs docs that show graph-name paths : on `langgraph-api` 0.16.0, `/.well-known/agent-card.json?assistant_id=supervisor` and `/a2a/service` return `Invalid assistant ID: must be a UUID`. Resolve UUIDs with `assistants.search` first.
- Deep Agent card name `supervisor` ; `supportedInterfaces` bind JSON-RPC 1.0 to `/a2a/{uuid}`.
- SendMessage on the service UUID completed : artifact text reports 6 CE-CF-02 fans at Rietpoort ; `contextId` present ; history includes tool_results for `part_stock`.

### demo05 · evaluating-agents

- Final answer facts : stock True, depot True, complete True (expected `(6, 'Rietpoort')`).
- Live trajectory vs one required `part_stock` call : strict False ; unordered/subset/superset True.
- Fixed reorder fixture inside one assistant message : strict, unordered, subset and superset all True. One-call fixture : subset True ; strict, unordered and superset False. The installed strict scorer permits call reordering within a message.
- Trajectory judge (`agentevals` 0.0.9) : `trajectory_accuracy` score True.
- Per agent : parts and manuals tool coverage True ; both judges True ; combined facts stock/depot/condition all True.

### demo06 · a-langsmith-experiment

- Review rerun on 14 October 2026 : `COURSE_RPS=0.05 uv run python build/run_notebook.py notebooks/09-production-deployment/demo06-a-langsmith-experiment.ipynb` from the repository root (PowerShell sets the environment variable separately).
- Runner result : PASS, 0 errors, 84.5 seconds.
- Local agent answered 6 CE-CF-02 cooling fans at Rietpoort.
- EU endpoint `https://eu.api.smith.langchain.com` ; experiment `ari520-module09-ab6e36ce` completed with 1 row.
- Example : `Is part CE-DA-03 in stock?` ; answer : `No. CE-DA-03 is out of stock at Rietpoort.`
- Per-example scores : `stock_fact=True`, `tool_coverage=True`.
- Installed `langsmith` 0.14.8 `ExperimentResultRow` annotations are `run`, `example`, `evaluation_results`. `run` is a `schemas.Run` object ; outputs are `row["run"].outputs`. Scores are `EvaluationResult` objects in `row["evaluation_results"]["results"]`, read through `.key` and `.score`.
- Original failure reproduced locally with a real `schemas.Run` fixture and the original `row["outputs"]` lookup : `KeyError: 'outputs'`. Iteration itself succeeds ; the list comprehension after iteration failed.
- Unavailable-path probe : mocked only `langsmith.Client` to raise `LangSmithConnectionError`, executed the generated experiment cell with a local agent fixture, and asserted that it finishes, marks the experiment FAILED, prints the exception class and omits raw exception text. This is a controlled failure check, not an observed live outage. No connection error occurred on the live rerun.
- EU experiment link : https://eu.smith.langchain.com/o/273ccfef-9b92-471e-8d31-d52722357485/datasets/eea5a0c8-0ded-48ac-8380-ca6ebd530adf/compare?selectedSessions=07591bd6-26de-465f-9794-07cb061fb269

### demo07 · cost

- Specialist usage : input 244, output 45, total 289 tokens.
- Transcript handoff : input 138, output 24, total 162.
- Summary handoff : input 50, output 24, total 74 (compact context uses fewer input tokens ; both answers preserved stock and depot).
- Prompt caching on repeated manual prefix : first call cache_read 0, cache_creation 4802 ; second call cache_read 4788, cache_creation 20. Provider-reported cache reads are non-zero on the second call through OpenRouter for this run.

### demo08 · injection-through-an-error

- Raw error path : injected recovery instruction arrived in a tool error ; agent called `export_report` ; egress attempts recorded `collector@outside.example` with the dummy secret. Neither compliance nor refusal is a security guarantee.
- Mitigated path : fixed `REPORT_UNAVAILABLE` code ; no egress attempts ; payload text absent from messages ; validated application path returns `[['CE-CF-02', 6, 'Rietpoort']]`.

## Figures and cited numbers on slides

| claim or figure | source |
| --- | --- |
| Stock 6 at Rietpoort ; CE-DA-03 stock 0 | executed demos 01–05, 07–08 and `service.db` |
| Reject 409 on double-texting | demo02 |
| Async lifecycle tools and `--n-jobs-per-worker` | demo03 ; research-2026-10 async notes |
| A2A UUID assistant ids | demo04 against langgraph-api 0.16.0 |
| Trajectory mode scores and judge True | demo05 |
| Plus plan about $39 a seat / month | `build/plan.md` Managed Deep Agents pricing note |
| firstmate ~7.9K stars (13 Oct 2026) | `build/research-2026-10.md` section 5 |
| Cost token and cache_read figures | demo07 |
| Injection then mitigation | demo08 |
| `images/trust-boundaries.svg` | speaker notes only (Academy notes 5.5 spirit) ; not rendered on the shortened slide |

## API differences from docs on the pinned stack

- **langgraph-api 0.16.0 / langgraph-sdk 0.4.7** : A2A agent-card and `/a2a/{id}` require assistant UUIDs. Graph names are rejected with JSON-RPC error `-32602`.
- **deepagents 0.7.24** : `AsyncSubAgent` fields are `name`, `description`, `graph_id`, optional `url`, `headers`, `mode` (`isolated` | `fork`). Co-deployed ASGI needs an async parent ; Agent Server satisfies that. Parent plus child runs need enough workers (`--n-jobs-per-worker`).
- **update_async_task** : interrupts the current run and starts a new run on the task thread ; it does not mutate a live model call mid-token (observed interrupt in server logs and demo03).
- **agentevals 0.0.9** : `create_trajectory_match_evaluator(trajectory_match_mode=...)` and `create_trajectory_llm_as_judge(prompt=..., judge=...)` behave as used in demo05 ; judge returns `key: trajectory_accuracy` with boolean `score`.
- **LangSmith 0.14.8 evaluate result rows** : result dictionaries contain `run`, `example` and `evaluation_results`. The former top-level outputs lookup failed after successful iteration. Read `row["run"].outputs` and score object attributes ; demo06 now completes and prints both per-example scores.

## Lint and pills

- Lint : `bun run ../../Presentation-Template/build/lint-slides.ts ../src/slides/09-production-deployment/09-production-deployment.md` from `build/` passes (Sandbox Return Channel shortened so the demo pill no longer overlaps content).
- Sixteen demo pills match sixteen notebook sections exactly, in order, each used once.
- Website outline terms present in the slide file : LangGraph API, deployment, scaling, streaming, persistence backends, checkpoint storage, cloud deployment, monitoring, cost optimization.

## Review changes and validation : 14 October 2026

Files changed in this review : the module slide Markdown, `build/make_module09.py`,
`demo06-a-langsmith-experiment.ipynb`, this measurement file, and the owned
run_notebook.py result. The builder was executed with its
`write_demo` call filtered to demo06 ; it also regenerated the existing runtime
helpers from unchanged definitions. Other notebooks retain their executed outputs.
No shared source, configuration, package pin or PDF was changed.

### Corrections

- Demo06 now reads run outputs and score objects from the installed result shape. Exceptions report their class without copying potentially credential-bearing text.
- Streaming no longer claims unchanged end-to-end latency. The slide states that clients can display chunks before completion ; no latency comparison was executed.
- Persistence identifies PostgreSQL as the default rather than the only production backend. TTL wording covers deletion and pruning rather than assuming every policy measures idle time.
- DeltaChannel describes reducer channels, replay and periodic snapshots. The list-only description omitted supported reducer value types.
- Co-deployment no longer implies a single process in a scaled deployment. The local demo's 8 run slots are a tested setting, not a claimed minimum.
- Scaling distinguishes local `--n-jobs-per-worker` from production `N_JOBS_PER_WORKER` and removes the unsupported assertion that provider quotas always dominate throughput.
- A2A `contextId` identifies an Agent Server thread. Protocol version 1.0 and the JSON-RPC envelope version 2.0 are distinguished in notes.
- Strict trajectory matching ignores prose and intra-message call order. The former same-order wording and incomplete measurement description were corrected.
- Managed Deep Agents commands are documentation-only APIs of a separate SDK, not installed course commands. Price is explicitly the dated plan figure ; SDK source availability is distinct from permission to use the SDK.
- Titles now name the technical subject. Administrative previews and contrast slogans were removed ; compound security and summary bullets were split.
- All 30 slides have explicit source notes. Design recommendations and unmeasured performance claims are identified as such. All 16 pills and their order were preserved.

### Installed API checks and executed probes

`uv run python` introspection confirmed SDK `assistants.search`, `threads.create`,
`threads.get_state`, `runs.wait`, `runs.list`, `runs.join`, `runs.cancel` and
`runs.stream`, including `stream_subgraphs`. Source inspection confirmed stream
mode literals `messages`, `messages-tuple`, `updates`, `values` and multitask
strategy literals `reject`, `enqueue`, `interrupt`, `rollback`.
`uv run langgraph dev --help` confirmed `--no-browser`, `--port`, `--studio-url`,
`--n-jobs-per-worker` ; the builder's `--no-reload` also exists. CLI help and
`langgraph_api/config/__init__.py` report a concurrency default of 10. Demos use
8, never a claimed minimum. `/ok` is supplied by `langgraph_api/api/meta.py`.

`AsyncSubAgent` annotations confirmed `name`, `description`, `graph_id`, `url`,
`headers`, `mode`. Installed async-subagent implementation contains all five
lifecycle tools and defaults context mode to `isolated` ; `fork` is accepted.
Installed `api/a2a.py` confirms UUID routes, agent-card query, context-to-thread
mapping and SendMessage, SendStreamingMessage, GetTask, CancelTask, ListTasks.
Demo04's card reports A2A protocolVersion 1.0 ; its request uses JSON-RPC 2.0.

`create_trajectory_llm_as_judge` accepts `prompt` and `judge`. `Client.evaluate`
accepts `max_concurrency`. `DeltaChannel` imports on 1.2.15 and its installed
signature includes `reducer`, `typ` and `snapshot_frequency`. No new DeltaChannel
storage benchmark or production deployment was executed.

Executed strict-matching probes on agentevals 0.0.9, no model calls :

| fixture | strict score |
| --- | --- |
| swap calls inside one assistant message | True |
| change prose while keeping roles and calls | True |
| swap two assistant messages with different calls | False |

The probe executed the real evaluator and agrees with `trajectory/strict.py`.
It supplements demo05's saved output rather than modifying its code.

### Slide-by-slide evidence

Every row refers to the installed packages listed above, the executed notebooks,
or the cited primary documentation. Speaker notes carry the precise source.

| slide | subject | evidence |
| --- | --- | --- |
| 1 | Production Agent Services | plan module 09 ; Agent Server docs ; demos 01, 02, 05, 07, 08 |
| 2 | LangGraph API | Agent Server docs ; SDK resource classes ; demo01 |
| 3 | Agent Server Resources | SDK clients ; demo01 c |
| 4 | langgraph.json | CLI config.py ; generated demo01 config ; graph-loading docs |
| 5 | langgraph dev and Studio | installed CLI help ; api/meta.py ; demo01 b |
| 6 | Threads and Runs in Practice | SDK methods ; demo01 c |
| 7 | Streaming to Clients | SDK StreamMode and runs.stream ; streaming docs ; demo02 a |
| 8 | Stream Modes and Subgraphs | runs.stream signature ; demo02 a metadata and saved state |
| 9 | Double-Texting and Concurrency | SDK literals ; demo02 b ; double-texting docs |
| 10 | Persistence Backends | Agent Server persistence docs ; demo02 c |
| 11 | Checkpoint Storage and TTLs | configure-ttl docs ; demo02 c |
| 12 | DeltaChannel | installed channels/delta.py ; research section 3 |
| 13 | Async Subagents | AsyncSubAgent and ASGI client implementation ; demo03 ; research section 4 |
| 14 | Async Task Lifecycle | installed lifecycle tool implementations ; demo03 |
| 15 | Co-deployed Graphs | graph exports ; demo03 |
| 16 | Firstmate Orchestration | dated research section 5 and its primary GitHub source |
| 17 | A2A on Agent Server | api/a2a.py ; demo04 ; server-a2a docs ; research section 3 |
| 18 | Deployment Options | Agent Server hosting docs ; CLI config |
| 19 | Managed Deep Agents | research section 3 ; dated plan pricing ; separate SDK CLI docs |
| 20 | Scaling Strategies | CLI help ; config/__init__.py ; Agent Server architecture docs |
| 21 | Evaluating a Multi-Agent System | plan ; ARI510 evaluation taxonomy ; evaluate-graph docs ; demo05 |
| 22 | Final Answer Evaluation | demo05 a ; service.db ; evaluate-graph docs |
| 23 | Trajectory Match | installed match scorers ; demo05 b ; executed review fixtures |
| 24 | Trajectory Judge | installed judge signature ; demo05 c ; LLM-as-judge docs |
| 25 | Specialist and System Evaluation | demo05 d |
| 26 | A LangSmith Experiment | installed result objects ; rerun demo06 ; evaluate-graph docs |
| 27 | Monitoring | research section 3 ; observability and online-evaluation docs |
| 28 | Cost Optimisation | demo07 token and cache outputs |
| 29 | Sandbox Return Channel | demo08 ; ARI510 demo34 ; Academy notes 5.5 |
| 30 | Summary | topic sources and demos 01-08 |

### Numeric ledger additions

- Package versions now include CLI 0.4.33 and LangSmith 0.14.8, read from `importlib.metadata` on the review date.
- Slide count 30 ; sourced-note count 30 ; 16 notebook sections and 16 matching pills. Script checked exact sequence equality, not just set membership.
- Lead-in share 0 / 142 top-level bullets, 0 percent using the house-style metric. No top-level parent has only one child.
- Demo06 1 example, both boolean scores True, 84.5 seconds, 0 errors : live output and runner JSON above.
- HTTP 409, stock 6 and 0, the 2134 and 2135 ports, local concurrency 8, and cached-token figures retain their existing executed-demo sources. CLI concurrency default 10 is read from installed help and server configuration ; it is not a throughput measurement.
- A2A 1.0 and JSON-RPC 2.0 are protocol identifiers from the executed card/request ; not latency or capacity numbers.
- Approximately $39 per seat per month and one free serverless deployment are the 13 October plan snapshot, not a verified current price. About 7.9K firstmate stars is the dated research snapshot, confined to notes.
- Notebook fault threshold 80 percent : demo05 tool evidence from `ce-12-error-codes.md`. Notebook maintenance intervals 12 and 18 months and firmware 5.2 / 5.3 : demo07 outputs and the CE-12 manual/bulletin fixtures. These are synthetic Veenhaven Bus data, not real maintenance advice.
- Notebook model token limits 300 / 200, recursion limits 20 / 16, evaluation concurrency 1 and injected worker hold 120 seconds are explicit demo parameters in the builder. They are not package defaults or observed model timings. Server polling and shutdown timeouts are control parameters, not performance claims.
- The former about-70-minute delivery estimate was removed ; live slide delivery has not been timed.

### Final validation and limits

- Changed notebook demo06 rerun using `build/run_notebook.py` : PASS, 0 errors ; scores and output read. Other seven notebooks' retained executions checked : all code cells have execution counts and no error outputs. They were not rerun in this review because their code was unchanged.
- All four server notebooks end with the stop cell ; saved output reports servers stopped. Ports 2134 and 2135 were free on the final socket check.
- Required lint from `build/` : PASS, `All slides within budget.`
- Controlled LangSmith-unavailable check passed. No live connection error required a one-minute retry.
- Managed Deep Agents, firstmate, TTL sweeps, rollback and production scaling remain documentation/research-backed subjects, not new live executions. No production performance claim is inferred from local dev runs.
- API differences : LangSmith row shape and strict trajectory semantics are corrected above ; A2A UUID requirement remains documented. No outstanding blocker found within the assigned scope.
