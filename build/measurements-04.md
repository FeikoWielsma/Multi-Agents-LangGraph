# Module 04 measurements and validation

Date : 14 October 2026. Round 2 completion of the 13 October draft. Repository : ARI520 Multi Agents with LangGraph.
Builder : `build/make_module04.py`. Stack verified with `importlib.metadata.version`
and `inspect.signature` : Python 3.12, LangChain 1.4.5, LangGraph 1.2.15,
LangSmith 0.14.8. Live model : `openai/gpt-6-luna` through OpenRouter,
temperature 0, reasoning effort `none`. Every notebook execution uses
`COURSE_RPS=0.07`. No new provider is introduced.

## Scope and provenance

Written paths :

- `src/slides/04-building-agents/04-building-agents.md`
- `build/make_module04.py`
- Seven `notebooks/04-building-agents/demo01` through `demo07` notebooks
- `build/measurements-04.md`

Ports : ARI510 module 08 Agent Single Pass, Agent Loop, tools_condition, ReAct
Agent and Fault Tolerance, plus demo21; module 04 create_agent, state,
middleware, logging, error handling and limits, plus demos11 and 12; module 03
demo09 tracing; module 11 testing slides and demo32. The examples now query
Veenhaven Bus `data/demo-world/service.db`. No capstone data is used.

The deck has 29 slides, counted from `^# ` headings after the front matter.
There are 15 demo sections and corresponding demo pills. The closing exercise
pill refers to the lead-owned exercise03. The house-style lead-in count is
0 of 126 top-level bullets (0%); each elaborated parent has multiple children.
First-slide delivery timing is a planning allowance, not a measured duration.

## Numerical example settings

These are deliberate demo configurations, not production recommendations or
model performance claims :

- The agent recursion budget is 16 graph steps in the bounded examples.
- The transient node fails attempts 1 and 2, succeeds on attempt 3, and has
  `RetryPolicy(max_attempts=3, initial_interval=0.01, jitter=False,
  retry_on=ConnectionError)`. The interval is seconds.
- Both exhausted-retry examples allow 2 attempts. The first handles
  `ConnectionError`; the second uses the default retry filter on
  `NodeTimeoutError`. Each handler runs once after exhaustion.
- Timeout examples set 0.08 seconds for a run or idle limit. The slow node
  waits 0.5 seconds. The progressing node waits 0.03 seconds for each of
  4 batches, calling `runtime.heartbeat()` after each batch. This completes
  under an idle-only limit but exceeds the run limit when both are configured.
  These are requested sleep and timeout values, not precise elapsed-time claims.
- Model and named-tool call limits are each 1 per run. The scripted model
  requests the bus tool twice. The model limit blocks the second model turn;
  the tool limit returns a blocked result for the second tool request and ends.
- Tracing client timeout is 10000 milliseconds. Root-run confirmation allows
  3 read attempts separated by 0.5 seconds. These are transport settings.
- The fake-model example saves 4 messages : human, tool-calling AI, tool result,
  final AI. Pytest contains 3 tests. Neither uses a model API key.

Database facts are read with parameterised SQLite queries, not invented by the
model. `CE12-2021-0117` maps to model `CE-12`, depot id `D01`.
`CE-DA-03` is the CE-12 door actuator, with recorded stock 0 at Rietpoort.
The full parts result also includes traction cooling fan `CE-CF-02` stock 6,
traction battery module `CE-TB-01` stock 1 and inverter module `CE-IM-04`
stock 2. These are synthetic dataset values, not performance measurements.
Unknown parts explicitly return `Unknown part`, rather than an invented zero.

## Installed API verification

Signatures and implementation source were inspected in the installed packages
before writing the examples. Runnable observations are in demos04, 05 and 07.

| API | Verified signature or behaviour |
| --- | --- |
| `StateGraph.add_node` | `retry_policy=`, `timeout=`, `error_handler=` are keyword parameters |
| `TimeoutPolicy` | Keyword-only `run_timeout`, `idle_timeout`, `refresh_on`; timeout values accept seconds or `timedelta` |
| Numeric `timeout` | Coerces to `TimeoutPolicy(run_timeout=value)` |
| Async timeout | Cancellation raises `NodeTimeoutError`; run and idle limits report `kind` as `run` or `idle` |
| Sync timeout | Accepted at registration, rejected with `ValueError` at compile time |
| Heartbeat | Refreshes the idle limit; does not extend the run limit |
| Retry timing | Timeout budget starts again for each attempt |
| Error handler | `def on_error(state, error: NodeError) -> Command`; `error.node`, `error.error` identify the failure |
| Retry filter | Built-in `TimeoutError` is excluded by the default filter; `NodeTimeoutError` is retryable by default |
| `create_agent` | Returns a `CompiledStateGraph`; supports `state_schema`, `middleware`, `checkpointer` |
| `ToolErrorMiddleware` | `(on_error=None, *, aon_error=None, tools=None)`; at least one callback required |
| Tool-error callback | Returned content becomes `ToolMessage(status="error")`; `None` re-raises |
| Tool validation | Binding and validation failures are handled by ToolNode before tool execution, outside ToolErrorMiddleware |
| `ModelFallbackMiddleware` | `(first_model, *additional_models)`; these are fallback models after the create_agent primary |
| `ModelCallLimitMiddleware` | Keyword-only `thread_limit`, `run_limit`, `exit_behavior`; default behaviour `end` |
| `ToolCallLimitMiddleware` | Keyword-only `tool_name`, `thread_limit`, `run_limit`, `exit_behavior`; default behaviour `continue` |
| Messages and tool schemas | `AIMessage.tool_calls`, `ToolCall(name, args, id)`, `ToolMessage(tool_call_id=, status=)`, `@tool` and `BaseTool.invoke` inspected and executed |
| Graph execution | `invoke`, `ainvoke`, `stream(stream_mode="updates")`, `get_state`, `get_graph().draw_mermaid()` inspected and executed |
| `ToolRuntime` | `state` is injected; `depot_parts.args` is empty |
| `AgentMiddleware` | Lifecycle, model and tool hooks have matching async variants |
| `after_model` | Supports `state_schema=DepotState` for updates to the custom counter |
| `dynamic_prompt` | Receives a request with custom agent state |
| `GenericFakeChatModel` | Plain model raises `NotImplementedError` in bind_tools; subclass returns itself for scripted calls |
| `Client.flush` | Supported; called before root-run confirmation |
| `Client.runs.retrieve` | Async on installed `Client`; requires `run_id` string and keyword `project_id` string, returns only ID by default |
| `trace` | Explicit root identifier parameter is `run_id`, not `id` |

Current [fault-tolerance documentation](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)
and [TimeoutPolicy reference](https://reference.langchain.com/python/langgraph/types/TimeoutPolicy)
agree with the pinned stack on the verified cases. One documentation discrepancy was confirmed on 14 October : the default retry
section says `OSError` and its subclasses are excluded, but installed
`default_retry_on` first special-cases built-in `ConnectionError` and returns
`True`. `issubclass(ConnectionError, OSError)` is also `True`. Offline calls
returned `True` for `ConnectionError`, `False` for built-in `TimeoutError`, and
`True` for `NodeTimeoutError`. The explicit retry filter in demo04 remains
appropriate and makes the selected failure type visible. The older ARI510 `def on_error(error)`
sample is corrected to the state argument and typed `NodeError` injection.
`run_timeout` and `idle_timeout` are fields of `TimeoutPolicy`, not direct
`add_node` arguments.

The named middleware classes all exist in LangChain 1.4.5; no substitute is
needed. See the [prebuilt middleware documentation](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
and installed implementation for the signatures above. The tracing block uses
the recommended [scoped tracing context](https://docs.langchain.com/langsmith/trace-without-env-vars).
The initial live run recorded a root trace but emitted a deprecation warning
for `Client.read_run`, with removal after 31 January 2027. The notebook now
uses `await client.runs.retrieve(str(root_run.id), project_id=str(project.id))`.
The [run retrieval migration page](https://docs.langchain.com/langsmith/smithdb-sdk-migration-runs)
says the Python replacement is async and should be awaited. Inspection of the
installed method confirmed `inspect.iscoroutinefunction` is `True`, and the
notebook awaits it. The required project identifier and default ID-only
response agree with that page. No discrepancy was found for this replacement.

It leaves the environment's `LANGSMITH_TRACING=false` unchanged and uses the
configured `https://eu.api.smith.langchain.com` endpoint.

## Execution record

First live batch : the single-pass section succeeded and correctly reported
the missing dependent parts lookup. Subsequent live calls failed with
`OpenAIConnectionError`. LangSmith reported a DNS `NameResolutionError` for
the EU endpoint. Direct DNS and unauthenticated HTTPS checks subsequently
succeeded for both OpenRouter and LangSmith, so the batch was retried once
at the same rate. No rate-limit error or 429 retry loop occurred.

Round 2 output review caught a misleading custom-state answer in demo02 : the
original depot tool returned positional part rows without their model. The
model said no CE-12 actuator was listed even though CE-DA-03 was present with
zero stock. The tool now returns labelled `model`, `part_no`, `name`, and
`stock` fields. The final rerun below uses the corrected tool.

## Runtime files and ownership

`demo07` writes `test_module04_agent.py` next to the notebook. The test fixture
copies the demo database into pytest's temporary directory, so the generated
file can also run independently. The notebook removes its own database copy in
`finally`; `contextlib.closing` closes SQLite connections before removal.
Pytest runs with Python `-B` and `-p no:cacheprovider` to avoid local bytecode and
pytest caches. The generated test file stays out of git. The existing `.gitignore` already has
`notebooks/**/test_*.py` and `notebooks/**/*.db`; no additional line is needed.
The pre-existing ignored `__pycache__/test_module04_agent.cpython-312-pytest-9.1.1.pyc`
remains : automatic approval review rejected both recursive cleanup and a
single-file `Remove-Item` command with `blocked by policy`. No new local cache
is requested by the revised pytest subprocess. No file outside the owned paths
was edited. No PDF build was run.


## Round 2 validation

Execution date : 14 October 2026. Each notebook runs alone through
`build/run_notebook.py`, always with `COURSE_RPS=0.07`. Elapsed times include
the shared setup, kernel startup and rate-limiter waits; they are not model
latency benchmarks. Final outputs are retained in the notebooks.

- demo01 : PASS, 0 errors, approximately 119 seconds. Single pass explicitly
  reported the missing parts lookup. Handwritten and ToolNode loops found
  CE-DA-03 with stock 0; the handwritten loop made 3 model calls.
- demo02 : PASS, 0 errors, approximately 119 seconds after the data-label fix.
  The base agent and parent handover identified CE-DA-03 and zero stock. Custom
  depot state produced the correct compatibility and stock answer; its counter
  was 2 model calls and the injected-runtime tool schema was empty.
- demo03 : PASS, 0 errors, approximately 47 seconds. Lifecycle hooks and tool
  wrappers logged bus lookup then parts lookup; the final answer was correct.
- demo04 : PASS, 0 errors, approximately 2 seconds. Attempts 1, 2, 3 reached
  success. Run and idle timeouts were caught; heartbeat-only progress completed,
  combined run and idle limits expired on the run limit. Sync timeout failed
  compilation as expected. Exhausted ConnectionError and NodeTimeoutError each
  routed to the manual queue after 2 attempts.
- demo05 : PASS, 0 errors, approximately 76 seconds. Unhandled tool failure
  raised TimeoutError; the handled case returned status error and requested a
  manual stock check. The injected primary failed on each of 3 model turns and
  the course fallback returned the correct actuator and stock. Both scripted
  call limits stopped with explicit limit messages.

- demo06 : PASS, 0 errors, approximately 49 seconds on the final modern-API
  rerun. The EU endpoint recorded root run
  `b0514782-b49a-4765-9816-db70ea1a8586` in project
  `ARI520-module04-building-agents`. The correct actuator and stock answer
  completed; default tracing was false before and after. No deprecation warning
  remained. A separate offline fault-injection probe patched Client to raise
  RuntimeError and the agent to return a fixed answer : the same notebook cell
  printed `tracing failed: RuntimeError`, invoked the untraced fallback once,
  returned the answer, and left default tracing false. This probe made no
  provider request and is not a live tracing-outage measurement.
- demo07 : PASS, 0 errors, approximately 4 seconds. Plain fake binding failed
  as expected, subclass produced the tool result 0 and saved 4 messages. All
  3 pytest tests passed (0.40 seconds); local service.db was absent afterward.

Slides : all 29 passed the module-scoped Puppeteer lint, including height and
house-style checks. Command : `bun run --cwd build lint
../src/slides/04-building-agents/04-building-agents.md --verbose`.
All seven final notebooks have zero error outputs and all code cells have
execution counts. Every output was read in full rather than relying on the
truncated preview from `show_outputs.py`. Round 2 encountered no connection or
timeout failure from the live providers, so the one-minute network retry rule
was not needed. The two reruns corrected a semantic tool-data omission and a
deprecated tracing read API; the notebook model-call rate remained 0.07.

The prose scan found no banned emphasis, dash, contrast or second-person forms.
All 15 ascending demo pills match the corresponding notebook sections in both
directions, with consecutive sections per notebook. All first sections now use
`a · slug`. The builder's cell sources match all seven generated notebooks.
The module follows the existing module04 section of `build/plan.md`; that shared
plan was read and was not edited, as required by the build brief.
