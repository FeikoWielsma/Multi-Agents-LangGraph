# Measurements : Deep Agents

## Environment and method

Execution date : 14 October 2026. Model : `openai/gpt-6-luna` through OpenRouter,
temperature 0, reasoning effort `none`, via the shared setup cell's `make_llm`.
Original pass : `COURSE_RPS=0.07`. The QuickJS completion pass re-executes
only demos 05 and 08 at `COURSE_RPS=0.1`, one notebook at a time.
Installed pins : `langchain` 1.4.5, `langgraph` 1.2.15,
`deepagents[quickjs]` 0.7.24 and `langchain-quickjs` 0.3.9.

The notebook `Counter` counts `on_chat_model_start` as a call and sums
`usage_metadata.input_tokens` and `output_tokens` on `on_llm_end`.
`malformed` is the length of `invalid_tool_calls` on completed messages.
`errors` counts `on_llm_error`. Nested agent and subagent calls inherit the
callback. Wall-clock seconds in the tables include the shared rate limiter
and must not be read as model latency. Token values are provider-reported
usage, not the local `count_tokens_approximately` estimate, except where a
row says approximate.

Demos 01 to 07 were already executed with 0 errors when the original pass started.
Their saved outputs were read and not re-run in that pass. Demo 08 was re-run after two
`OpenAIConnectionError` cells (connection drops, `malformed` still 0 on the
partial rows). Demos 09 and 10 were executed in the original pass. The tables below
are the saved notebooks after those runs, with demos 05 and 08 replaced by
the QuickJS completion runs. The discarded connection-error rows are not
cited on the slides.

Original spans below are from the first to the last saved cell timestamp.
Completion rows for demos 05 and 08 use `run_notebook.py` wall time including
startup. The original runner reported demo 08 at 120 s, demo 09 at 78 s and
demo 10 at 194 s.

| notebook | span | status |
| --- | --- | --- |
| demo01 | 205 s | PASS, 0 errors |
| demo02 | 104 s | PASS, 0 errors |
| demo03 | 62 s | PASS, 0 errors |
| demo04 | 162 s | PASS, 0 errors |
| demo05 | 76 s including startup | PASS, 0 errors, QuickJS completion |
| demo06 | 90 s | PASS, 0 errors |
| demo07 | 180 s | PASS, 0 errors |
| demo08 | 197 s including startup | PASS, 0 errors, QuickJS completion |
| demo09 | 76 s | PASS, 0 errors |
| demo10 | 192 s | PASS, 0 errors |

## Manuals on disk

`data/demo-world/manuals/*.md` : 31 files, 18795 characters, UTF-8, no
carriage returns. Counted 14 October 2026 with `Path.read_bytes` on those
Markdown files only. `index.txt` is a 709-byte extra file and is not in the
31. An earlier note of 18855 was a miscount and is not used.

The tool-shaped join `[name]\n` plus body, separated by a blank line, is
19626 characters. Demo 03 prints that as `raw characters`, and demo 08 prints
`files : 31 characters : 19626` for the same join.

## Callback rows

Every row has `malformed` 0 and `errors` 0.

| label | notebook | calls | input | output | seconds |
| --- | --- | --- | --- | --- | --- |
| plain | demo01 | 2 | 194 | 45 | 30.8 |
| todos | demo01 | 4 | 5502 | 122 | 57.4 |
| files | demo01 | 3 | 4160 | 95 | 42.5 |
| scratch-subagent | demo01 | 5 | 4438 | 144 | 71.8 |
| default-harness | demo02 | 3 | 6272 | 91 | 44.5 |
| harness-planning | demo02 | 4 | 13290 | 120 | 57.3 |
| virtual-read | demo03 | 2 | 4226 | 66 | 31.5 |
| offload | demo03 | 2 | 4336 | 55 | 27.9 |
| state-write | demo04 | 2 | 4033 | 49 | 30.1 |
| state-read | demo04 | 2 | 4204 | 44 | 28.6 |
| filesystem | demo04 | 2 | 4018 | 44 | 28.7 |
| store-new-thread | demo04 | 2 | 4014 | 40 | 28.9 |
| composite | demo04 | 3 | 6133 | 75 | 42.7 |
| permissions | demo05 | 3 | 6197 | 68 | 31.9 |
| quickjs-tickets | demo05 | 2 | 5657 | 158 | 21.0 |
| local-shell | demo05 | 2 | 4549 | 31 | 18.3 |
| memory | demo06 | 1 | 3106 | 14 | 15.7 |
| skills | demo06 | 2 | 4967 | 86 | 29.1 |
| bound-skill | demo06 | 3 | 7735 | 76 | 42.4 |
| dict-subagent | demo07 | 4 | 7558 | 121 | 59.3 |
| compiled | demo07 | 4 | 4375 | 106 | 56.9 |
| fork | demo07 | 4 | 8752 | 94 | 59.9 |
| python-fanout | demo08 | 4 | 465 | 69 | 42.8 |
| quickjs-fanout | demo08 | 6 | 16595 | 310 | 61.7 |
| whole-prompt | demo08 | 1 | 5121 | 20 | 7.5 |
| split-calls | demo08 | 3 | 5192 | 30 | 29.3 |
| quickjs-environment | demo08 | 5 | 15983 | 207 | 50.8 |
| interrupt | demo09 | 1 | 1997 | 27 | 15.8 |
| approved | demo09 | 1 | 2040 | 6 | 14.4 |
| summarise | demo09 | 3 | 4886 | 128 | 43.1 |
| graph | demo10 | 7 | 919 | 220 | 101.6 |
| deep | demo10 | 6 | 11165 | 258 | 88.0 |

`gpt-6-luna` produced no malformed tool calls in any completed response
these notebooks saved. The discarded demo 08 connection failures also
reported `malformed` 0 ; they failed before a normal completion, which is
a transport error, not a bad tool-call payload.

## Answers worth keeping

Stock lookups that used `part_stock` named 6 CE-CF-02 fans at Rietpoort.
That matches the parts row the other modules already recorded. The plain
agent called `part_stock` once. The todo runs called `write_todos`, then
`part_stock`, then `write_todos`, and the printed todo was `completed`.
The middleware does not enforce that order ; this run happened to follow it.

The scratch file run wrote `/stock.md` and did not put the body in the tool
reply. The scratch `task` worker's only tool was `part_stock` ; the parent's
tools were `task` and `write_note`.

`create_deep_agent` default tool schemas on this graph, plus the caller tool :
`delete`, `edit_file`, `execute`, `glob`, `grep`, `ls`, `part_stock`,
`read_file`, `task`, `write_file`. No `write_todos`. `todos` was `None`
until `TodoListMiddleware` was passed. The counted default-harness run
passes a one-line `system_prompt`. The empty authored prompt is a separate
package fact, below, and is not the 6272-token run.

Virtual read of seeded `/manual.md` reported the F-CE-110 first action
(check the traction cooling fan ; replace below 80 percent airflow) and
`Path("manual.md").exists()` was false.

Offload, with `tool_token_limit_before_evict=600` : the model saw the
`/large_tool_results/` path and a preview, and reported 2 sources. There
are 31 manuals. The slide treats the printed length as the check. The
preview is too short to count the files, and this answer shows that.

Filesystem traversal of `/../pyproject.toml` printed `Path traversal not
allowed`. A second store namespace read `/policy.md` as not found. The
composite route stored `/memory/policy.md` on the store as `/policy.md`.

Permissions : write to `/scratch.md` was denied ; write to `/reports/fan.md`
was allowed. First matching rule.

QuickJS tickets : one model-generated eval loads all 43 CSV rows with
`JSON.parse(await tools.ticketRows({}))`. It filters D01 rows with empty
`parts_used`, counts 4 and sums `Number(hours)` to 7.5. The independent
Python check uses `Decimal` and gets the same values. `typeof process`,
`typeof require` and `typeof fetch` are all `undefined`. The parent tool
history is only `eval`, and `ticket_rows` is absent from its static tool map.
The result is compact JSON in `<result>`, not the raw ticket export.
This run does not measure whether the model can sum the CSV unaided.

Local shell : `execute` printed `veenhaven` and exit code 0. The model
also answered `veenhaven` in the completion run. `inherit_env=False`.
The earlier pass's `veen haven` retelling is no longer a slide claim.

Memory answer named the high-visibility vest, which is only in the seeded
`AGENTS.md`. The skills answer added walkways and moving vehicles beyond
the three-rule file ; the notebook already says any other rule is the
model's. `order_fan` was absent from the static tool map and appeared
only after the skill was read. The tool reply says the order does not
change stock.

Dict subagent : 6 CE-CF-02 at Rietpoort, through `task`. The printed `task`
description lists `general-purpose` beside `parts`.

Compiled run : "check the traction cooling fan." Fork run : the same first
action. The fork's `task` description did not contain `F-CE-110`. Message
counts were `[2, 2, 4, 4]` on the compiled run and `[2, 3, 5, 4]` on the
fork run. The 4375 and 8752 input tokens are each run's callback total,
parent plus worker, not the worker call alone.

Python fan-out : F-CE-110 -> "Check the traction cooling fan." F-CE-305 ->
"Inspect the door actuator." Both match the manual's first action, in
shorter wording than the complete guidance. QuickJS fan-out uses one eval
with Promise.all/map and two top-level task dispatches. The schema returns
error_code and action. Coverage is both supplied codes once; the JavaScript
results are cooling-fan check and "Inspect and replace the door actuator."
The parent history contains only eval; worker fault_guidance calls stay
inside the workers. Parent plus workers cost 6 model calls, versus 4 for
the application-owned plain-agent loop. The interpreter does not erase
worker model calls. Both paths use the same model, but the Deep Agents
workers have harness middleware, so this is not a pure concurrency benchmark.

Interrupt : one pending `write_file` of `/note.md` with content
`fan stock checked`. Files while paused : empty. After
`{"decisions": [{"type": "approve"}]}` : pending 0, file `/note.md` present.

Summarisation : `compute_summarization_defaults(llm)` printed
`trigger ('tokens', 170000)`, `keep ('messages', 6)`, and
`truncate_args_settings` trigger/keep `('messages', 20)`. The demo replaces
that middleware with a 3-message trigger and `truncate_args_settings=None`.
The run wrote `/conversation_history/session_….md` containing the original
human lookup, and the answer was still 6 fans at Rietpoort. Three calls :
the lookup, the summary, the final answer.

## Demo 08 b : one prompt against a split

The joined manuals are about 4911 approximate tokens
(`count_tokens_approximately` on one `HumanMessage`). The three chunks
are about 1724, 1924 and 1271.

| path | calls | input tokens | output tokens | largest call | seconds |
| --- | --- | --- | --- | --- | --- |
| whole prompt | 1 | 5121 | 20 | 5121 | 7.5 |
| Python split | 3 | 5192 | 30 | 2010 | 29.3 |
| QuickJS environment | 5 | 15983 | 207 | 5241 root, 2199 reader | 50.8 |

Provider input on the split calls was 1784, 2010 and 1398. The largest
single call fell from 5121 to 2010. The total did not fall. The whole
prompt and the final Python split findings named the cooling-fan check and
80 percent replacement condition. Chunks 1 and 2 both contain F-CE-110,
in `ce-12-error-codes.md` and `ce-12-procedure-ce-cf-02.md`. The Python
split returned the correct guidance from chunk 1 but NONE from chunks 2
and 3 in this run. Chunk 2 is a false negative. The earlier pass returned
the same guidance twice. A successful notebook run does not make every
chunk classification correct; inspect each printed finding against its
source. The file-third split is not a unique-code split.

The added environment path uses a read-only PTC loader for the same chunks.
The root writes one JavaScript script that loads them, maps top-level task
over them, and returns only JSON-stringified findings. The reader is a
CompiledSubAgent wrapping create_agent with the same course model and no
tools. Its bulk prompt is a derived chunk with no independent file locator.
The parent model never receives the loader result as a ToolMessage.
The async model-request inspector found no complete chunk in either root
request, `[False, False]`. This checks complete-chunk absence, not an
arbitrary data-loss or leakage guarantee.

| role and call | provider input tokens | provider output tokens |
| --- | --- | --- |
| root 1 | 5055 | 106 |
| reader 1 | 1947 | 30 |
| reader 2 | 2199 | 30 |
| reader 3 | 1541 | 14 |
| root 2 | 5241 | 27 |

These sum to the Counter's 15983 input and 207 output tokens. Both relevant
readers gave the cooling-fan check and 80 percent condition. The third
reported absence, correctly. The final answer had the same action and
condition. The largest reader sees 2199 input tokens, while the largest
root prompt is 5241. On these 31 small manuals, the full harness prompt
offsets the benefit of keeping source data in the environment: total input
increases, and the largest overall call exceeds the single prompt's 5121.
This demonstrates one-level RLM context placement, not token savings,
arbitrary recursive depth or a corpus beyond the model's context window.

The paper's "about two orders of magnitude" beyond the context window
(research note, arXiv 2512.24601) is not a result on this corpus. These
31 manuals fit in one call. The slide's 100-times line is that paper
claim. The 5121 / 5192 / 2010 lines are this run.

## Demo 10 : graph against a Deep Agent

Same question : bus CE12-2021-0117, error F-CE-110, stock and location of
CE-CF-02, plus the manual's first action and replacement condition.
`inspect.getsource` on the two builders, shared tools excluded.

| builder | lines | calls | input | output | seconds | stock check | action check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| supervisor graph | 33 | 7 | 919 | 220 | 101.6 | true | true |
| Deep Agent | 8 | 6 | 11165 | 258 | 88.0 | true | true |

The supervisor chose `parts`, then `manuals`. Graph answer : 6 CE-CF-02
cooling fans at Rietpoort ; check the traction cooling fan ; replace it if
airflow is below 80 percent. Deep Agent tools were `task` and `task`.
Its answer named the same stock, location, first action and 80 percent
condition. The action check looks for fan, airflow and 80. Both passed.

The Deep Agent used one fewer call and about twelve times the input
tokens. The gap is the harness prompt and the default tool schemas,
including `general-purpose`, not a longer final answer. Output tokens
were 258 against 220.

## Slide figures

| figure on the slides | source |
| --- | --- |
| 2 calls, 194 input, 45 output | `plain` |
| 4 calls, 5502 input, against 2 and 194 | `todos` and `plain` |
| 3 calls, 4160 input | `files` |
| 5 calls, 4438 input | `scratch-subagent` |
| 3 calls, 6272 input, 91 output | `default-harness` |
| 4 calls, 13290 input | `harness-planning` |
| 31 manuals, 18795 characters on disk | directory count above |
| tool result 19626 characters, path under `/large_tool_results/`, model said 2 sources | demo03 |
| `Path traversal not allowed` | demo04 |
| D01 tickets without parts : 4 tickets, 7.5 hours ; host APIs undefined | demo05 QuickJS result and Python Decimal check |
| tool line `veenhaven`, exit code 0 | demo05 |
| fork run 8752 input, compiled run 4375 input | demo07 totals |
| paper, on the order of 100 times the context window | `build/research-2026-10.md`, two orders of magnitude, on the paper's tasks |
| one prompt 5121 input and 20 output ; Python split 5192, largest 2010 | demo08 |
| QuickJS environment 5 calls, 15983 input ; largest reader 2199 | demo08 Counter and per-role UsageRows |
| default summary trigger 170000 tokens, keep 6 messages | demo09 print of `compute_summarization_defaults` |
| tool eviction 20000 tokens, human message 50000 | `FilesystemMiddleware.__init__` defaults in 0.7.24, not a live oversized message |
| graph 33 lines, 7 calls, 919 input ; Deep Agent 8 lines, 6 calls, 11165 input ; both named 6 fans and the cooling-fan check | demo10 |

The lowered offload threshold of 600 tokens is the argument in the demo,
not a measured default.

## API differences : docs and deepagents 0.7.24

Checked against the installed package on 14 October 2026. The original pass
used the October research note and package deprecation text. The QuickJS
completion pass also read the live primary sources linked below.

- Interpreter and dynamic subagents are provided by the separate
  `langchain_quickjs` package, installed through the `deepagents[quickjs]`
  extra. They are demonstrated by real eval calls in demos 05 and 08.
  `execute` remains separate and requires `SandboxBackendProtocol`.
- Authored base prompt. `BASE_AGENT_PROMPT` was deprecated in 0.7.0 and is
  scheduled for removal in 0.9.0. The warning says Deep Agents no longer
  provides an authored base prompt. Reading the attribute still returns the
  legacy string. With no caller `system_prompt` and no matching harness
  profile, the authored prompt is empty ; tool schemas and middleware
  fragments still go to the model. The demo02 stock lookup does pass a
  one-line prompt, so its token count is not this empty-prompt case.
- Default model. `model=None` and `get_default_model` are deprecated since
  0.5.3, removal 1.0.0, and build `ChatAnthropic(model_name="claude-sonnet-4-6")`.
  Every demo passes `llm`.
- Planning. `write_todos` is absent from the default tool map. The three
  Codex harness profiles `openai:gpt-5.1-codex`, `openai:gpt-5.2-codex` and
  `openai:gpt-5.3-codex` add `TodoListMiddleware` because their suffix talks
  about `write_todos` (`profiles/harness/_openai_codex.py`).
  `openai/gpt-6-luna` matches no harness profile, so the planning demo passes
  the middleware itself.
- `StoreBackend` requires the `namespace` callback. An empty namespace raises
  `ValueError`. Demo 04 shows two namespaces do not share `/policy.md`.
- `metadata.include_tools` is a space-separated string of tool names
  (`skills.py`). A YAML list or a comma logs a warning. A list is then
  coerced with `str()`, and that text does not match tool names. The demo
  uses spaces. The 7 October skills change described in the research note
  is present : tools stay off the model request until the skill is read or
  named in `pinned_skills`.
- Summarisation defaults follow the model profile. This `ChatOpenAI` has
  `profile is None`, so the printed default is 170000 tokens and a keep
  window of 6 messages, not the fraction 0.85 / 0.10 used when
  `max_input_tokens` is set. `compact_conversation` comes from
  `SummarizationToolMiddleware`, which `create_deep_agent` does not add
  unless the caller passes it. The deepagents wrapper appends evicted
  messages to `/conversation_history/{session}.md` and leaves
  `state["messages"]` intact. LangChain's own middleware, as the factory
  docstring describes it, rewrites the message list and defaults `keep` to
  20 messages.
- Eviction defaults on `FilesystemMiddleware` are 20000 tokens for a tool
  result and 50000 for a human message. The offload demo sets the tool
  limit to 600 so one manuals export crosses it.
- Fork mode is marked experimental on the `SubAgent` docstring. A fork
  cannot set `skills`. The preamble tells a fork that a further `task`
  call will be refused and to complete the task directly. The demo did not
  attempt that nested call.
- `create_deep_agent` inserts a `general-purpose` subagent when the caller
  did not use that name. `GeneralPurposeSubagentProfile(enabled=False)`
  stops the insertion. With no synchronous subagent left, `task` is not
  registered. Async subagents are a different middleware.
- `CompositeBackend` strips the matched route prefix before the inner
  backend sees the path. Demo 04 printed the store entry as `/policy.md`.
- `FilesystemPermission` is applied by the file tools. The
  `create_deep_agent` docstring says a direct backend call does not apply
  those rules. `mode="interrupt"` builds the same human-in-the-loop pause
  as `interrupt_on`.
- Resume uses LangGraph `invoke(..., version="v2")`, which returns
  `GraphOutput` with `.interrupts` and `.value`. Subscripting that object
  for `__interrupt__` is deprecated. Demo 09 used `.interrupts` and
  `.value`, and the approve decision ran.

The Academy course noted in the research file pins `deepagents` 0.7.0.
This room is on 0.7.24. Their repository has no licence, so none of its
text or code is in these notebooks.

## QuickJS API inspection : 0.3.9

Inspected `inspect.signature`, the middleware class docstring and installed
`middleware.py`, `_prompt.py`, `_ptc.py`, `_subagent.py`, `_repl.py` and
`_format.py` with `uv run python` on 14 October 2026. No package was changed.

Attachment is `create_deep_agent(model=llm,
middleware=[CodeInterpreterMiddleware(...)])`. The middleware adds one
tool, `eval(code: str)`, with JavaScript language metadata. Existing Deep
Agents tools remain present. The model writes JavaScript, including
top-level await, not Python. The final expression or resolved promise is
rendered into `<result>`. Console output has its own `<stdout>` block;
execution errors use `<error>`. JSON.stringify makes the returned text
parseable by the notebook instead of the default JSON-like object rendering.

`PTCOption` is a type alias, `list[str | BaseTool]`, not an enum. PTC is off
with `ptc=None`. String names select tools from the live model request;
explicit BaseTool objects also work without putting them on that request.
Mixed entries are deduplicated. Snake-case tool names become camelCase
JavaScript names. The REPL's own eval tool is excluded. `ptc=["task"]`
raises ValueError when the allowlist is resolved; a local, model-free call
to `filter_tools_for_ptc` confirmed it. Our loaders return JSON strings and
therefore need JSON.parse. Source `coerce_tool_output_for_ptc` also preserves
native lists and objects; not every tool return is a string.

Top-level `task({description, subagentType, label?, responseSchema?})`
dispatches the configured Deep Agents task tool independently of PTC.
The bridge supplies the enclosing ToolRuntime and runnable config.
`responseSchema` requests dynamic structured output for a declarative
subagent; it is rejected for a runnable-backed CompiledSubAgent. With a
schema the result is already a native JavaScript value. The normal Python
tool uses `subagent_type`, not `subagentType`. Dispatch lifecycle events
are emitted on the custom stream, while intermediate worker messages do
not become parent ToolMessages.

| option | installed default | meaning |
| --- | --- | --- |
| memory_limit | 67108864 bytes, 64 MiB | QuickJS heap shared across contexts within a runtime |
| timeout | 5.0 seconds | VM execution time per eval, excluding waits in Python host calls |
| max_ptc_calls | 256 | per-eval tools.* calls ; None disables the budget |
| max_result_chars | 4000 | independent result and stdout truncation |
| capture_console | True | capture log, warn and error |
| subagents | True | enable task global when the host has the task tool |
| max_subagent_concurrency | 32 | simultaneous task calls per REPL ; excess waits |
| ptc | None | no ordinary host tools exposed |
| mode | None, resolved to thread | thread across turns, turn within a turn, call fresh each eval |
| max_snapshot_bytes | None, resolved to memory_limit | oversize persisted snapshot is dropped |
| snapshot_signing_key | None | snapshots unsigned unless caller supplies a key |

`max_ptc_calls` does not count top-level task dispatches. Its bridge increments
a separate ordinal and uses a semaphore. Neither the concurrency setting
nor the VM timeout is a total worker/cost/wall-clock budget. Our tasks use
two error codes and three chunks, and graph recursion_limit remains 24.
Demo05 uses 16 MiB, 2 seconds, 2 PTC calls, 1200 result characters,
subagents=False and turn mode. Demo08 uses 2 seconds and turn mode;
fan-out concurrency is 2, while the environment readers use concurrency 1
and one PTC loader call. Other arguments use the inspected defaults.

PTC and task dispatches bypass parent per-tool/per-task HITL approval.
Gate eval, use the ordinary tool path, or configure approval in a worker.
An allowlisted Python tool retains host capabilities; filesystem permissions
on Deep Agents file tools do not restrict arbitrary guest bridges.

Primary documentation checked in the completion pass :

- [Dynamic subagents](https://docs.langchain.com/oss/python/deepagents/dynamic-subagents)
  matches the top-level task API and configured-worker fan-out. The feature
  remains beta. The demo is one level of recursive-model orchestration,
  not a claim of the paper's context-window scale or benchmark gains.
- [Interpreters](https://docs.langchain.com/oss/python/deepagents/interpreters)
  describes the scoped JavaScript runtime and capability bridges. Our pin
  uses an explicit allowlist and keeps loader results in the REPL.
- [QuickJS package README](https://github.com/langchain-ai/deepagents/blob/main/libs/partners/quickjs/README.md)
  labels timeout wall-clock, but the installed docstring excludes Python
  host-call time. It also recommends ainvoke because sync bridges fail;
  in 0.3.9 `eval_sync` routes through `_aeval_async` on the worker loop.
  The first ticket run and first fan-out did work with synchronous invoke.
  Reusing the cached asynchronous model client in a second interpreter
  produced `RuntimeError: Event loop is closed` in the environment run
  (3 attempted model calls, callback errors 1). This is a loop-affinity
  limitation, not ConcurrentEvalError. We discarded that run, waited a
  minute and changed all interpreter invocations to notebook-level await
  agent.ainvoke. The next attempt exposed a sync-only inspection middleware;
  wrap_model_call must decorate an async function to support ainvoke.
  That attempt stopped before any environment-agent model call. The final
  inspect_root is async and awaits its handler. Final measurements come
  from the reruns, not these discarded attempts.
  Its Promise<string> summary is narrower than the installed native return
  coercion, which also accepts objects and arrays.
- [Interpreter introduction](https://www.langchain.com/blog/give-your-agents-an-interpreter)
  shows ptc=["task"] and tools.task with subagent_type. Those older
  examples conflict with 0.3.9's reserved-task check. Use top-level task
  with subagentType. The installed subagent prompt also says returned values
  are untruncated; `_format.format_outcome` actually caps the result block
  with max_result_chars, as it does stdout. Keep findings compact.
