# Module 05 measurements

Date : 14 October 2026. Module : Multi-Agent Patterns.

## Environment and method

The course model is `openai/gpt-6-luna` through OpenRouter, reasoning effort
`none`, temperature 0. Installed versions inspected with `importlib.metadata`
are `langchain` 1.4.5, `langgraph` 1.2.15 and `deepagents` 0.7.24, on Python
3.12. Every notebook execution sets `COURSE_RPS=0.12`. All workers and model
copies share the setup cell's `InMemoryRateLimiter`, with a bucket size of 1.
The measuring model uses `max_tokens=1200` and `max_retries=0`.

`Counter` counts attempted model invocations at `on_chat_model_start`. Token
counts sum successful responses' `usage_metadata.input_tokens` and
`output_tokens` across all workers and coordinators. `on_llm_error` counts
failed invocations separately. A rejected handoff request therefore contributes
a call and an error, but no reported response tokens. `measured` times the
complete operation with `time.perf_counter`. Seconds include graph execution,
tools, network time and deliberate rate limiting ; they are not model latency.

Execution uses `build/run_notebook.py`, one notebook at a time. Connection
errors or timeouts trigger a 60-second wait and a rerun of that notebook.
Previous session failures were saved connection errors and timeouts, with one
`NameError` caused by a failed earlier cell. No keys or authentication headers
are included in the notebooks or this report.

## Questions and evidence

All demos use the fictional Veenhaven Bus records in `data/demo-world/`.
The principal question asks about bus `CE12-2021-0117`, error `F-CE-110`,
the stock and location of `CE-CF-02`, and the manual's first action and
replacement condition. It explicitly requests the condition because the answer
checks include it.

Read-only SQL against `service.db` returns `CE-CF-02`, stock 6, Rietpoort.
`ce-12-error-codes.md` says to check the traction cooling fan and replace it
if airflow is below 80 percent. Maker-checker and selection additionally use
`CE-DA-03`, stock 0, Rietpoort, and require an 'out of stock' warning.

`completeness` checks the count (6 or six), location, fan, airflow and the
threshold (80 or eighty). These are coarse keyword checks. They can accept a
contradictory sentence, miss a correct paraphrase, or ignore an omitted citation.
Every saved answer is also read. `check_note` checks required identifiers,
digits, locations and the zero-stock wording on the same line. It establishes
only that narrow contract.

## Documentation comparison

Source : [LangChain multi-agent documentation](https://docs.langchain.com/oss/python/langchain/multi-agent/index),
checked 14 October 2026. These are the documentation's illustrative comparisons,
not measurements of the course model.

| Pattern | One request calls | Repeat-turn calls | Three-domain calls | Three-domain tokens |
| --- | --- | --- | --- | --- |
| Subagents | 4 | 4 | 5 | About 9K |
| Handoffs | 3 | 2 | 7 or more | About 14K or more |
| Skills | 3 | 2 | 3 | About 15K |
| Router | 3 | 3 | 5 | About 9K |

The docs' one-request and repeat examples use a purchase task. The multi-domain
example compares programming languages with about 2,000 documentation tokens
per domain. The slide's capability matrix translates their five/three/one-star
ratings to High/Medium/Low. Unrated means a dash in the source, not an API
prohibition. Separate teams denotes distributed development. Custom workflows
are omitted from that source matrix.

## Earlier probe

Source : `build/measurements.md`, `build/probe_patterns.py` and
`build/probe-patterns-gpt-6-luna.json`. Recorded 13 October 2026, three runs per
pattern, component-wise medians, Luna through OpenRouter with reasoning off.
That question asks for BR-220 stock at Noord and the next workshop slot. It
uses small in-memory fixtures, stock 6 and Thursday 15 October at 09:00, and a
rate budget of 0.3 requests per second.

| Pattern | Correct | Calls | Input tokens | Output tokens | Seconds |
| --- | --- | --- | --- | --- | --- |
| Single agent | 3/3 | 2 | 399 | 96 | 6.7 |
| Subagents | 3/3 | 6 | 781 | 204 | 20.3 |
| Handoffs, fixes applied | 2/3 | 4 | 1,165 | 99 | 13.5 |
| Skills | 3/3 | 4 | 1,036 | 131 | 14.6 |
| Router | 3/3 | 6 | 622 | 184 | 20.6 |
| Custom workflow | 3/3 | 5 | 472 | 129 | 17.0 |
| Deep Agent, module 08 pointer | 3/3 | 6 | 11,044 | 214 | 20.6 |

The raw JSON marks the router's 'six' answer false. The shared measurements
correct this to true ; the module preserves that corrected score without
editing the raw file. The fixed handoff still has a half-answer run. The probe's
Deep Agent row is not rerun here ; the harness comparison belongs to module 08.
Different data and rate budgets prevent a direct seconds comparison with demo09.

## Handoff faults and pinned APIs

The [documented subgraph handoff](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)
forwards the last `AIMessage` and the transfer receipt. `build/measurements.md`
records two distinct failures : a sibling lookup result lost during a parallel
tool turn, and earlier lookup work lost when only the last message is forwarded.

Demo04 a seeds each triggering history in a LangGraph child and calls the live
model in the receiving parent node. It catches only the malformed-history
provider rejection, prints the error, and separately prints the valid-history
half answer. It does not swallow connection errors. Demo04 b uses live model
decisions and both fixes : `parallel_tool_calls=False` in the handoff model's
`model_kwargs`, and full `runtime.state['messages']` plus a matching transfer
receipt in the parent `Command` update. Both handoff worker loops are built
from `StateGraph`, `ToolNode` and `tools_condition`. Valid history does not
guarantee that a worker chooses to transfer or preserves all facts in its answer.

Demo04 c uses `create_agent` after those explicit loops, keeping `current_step`
and `bus` in state and selecting prompt/tools with `wrap_model_call` and
`request.override`. `InMemorySaver` retains the step across two user turns.

The installed signatures were inspected for `create_agent`,
`ChatOpenAI.bind_tools`, `ModelRequest.override`, `ToolNode`, `Command` and
`Send`. `Command(graph=Command.PARENT, update=..., goto=...)` and `Send(node,
arg)` are present. The corrected supervisor retains the model's delegated
`task` in state and passes it to the selected worker ; it no longer prints one
task while silently executing another fixed task.

Executable budgets are two worker rounds for the supervisor and two maker
attempts for maker-checker, with graph recursion limits of 24. Those limits
bound resource use ; they do not certify completion. The hierarchy adds one
outer synthesis call to the same team implementation. The code-lookup workflow
hard-codes this question's known lookup arguments ; it is not an arbitrary
question parser.

## Content verification

The slide deck has 33 slides. Nine notebooks contain 19 sections, with 19
matching pills in ascending notebook order. Each notebook's section pills occupy
consecutive slides. All code cells parse. The deck contains 166 top-level
bullets and no single-child lead-ins. The targeted Puppeteer slide-height and
house-style lint passes after replacing the crowded hierarchy diagram with its
nested graph wrapper code. No PDF build was run.

The deck ports the requested ARI510 topics and adds the manual supervisor,
manager-worker and hierarchical boundaries, the handoff faults, collaboration
shapes, isolation choice and measured comparison. Named orchestration ideas
from `build/academy-deepagents-notes.md` are explained in original wording.
No Academy lesson text, diagram or code is copied. Message passing, conflict
resolution and A2A have forward pointers to module 06 ; Deep Agents has forward
pointers to module 08.

## Observed learning points

- Demo01's final run preserves the stock, location and airflow condition. The
  context inspection shows that the coordinator receives final worker answers,
  not their internal tool messages.
- Demo02 selects both workers and includes the replacement condition in its
  final delegated task. The supervisor and hierarchical team preserve all the
  requested facts. The prose explains how to inspect a lost requirement if a
  future model run omits one.
- Demo03 selects only parts for the stock request and both workers for the
  combined question. The parallel router preserves both facts and the condition.
- Demo04's seeded sibling-result case returns a provider 400 rejection,
  `No tool output found for function call stock-1.` The valid but truncated
  history gives guidance while reporting stock unavailable. Both live repaired
  variants preserve the requested facts. Triage initially attempts an invalid
  fleet lookup using the error code ; the database validation keeps the step in
  triage, and the supplied valid bus advances it. This failure remains visible
  and is explained in the notebook prose.
- Demo05 loads both skills and retains their instructions/tool results in the
  main conversation. The separate worker starts from only the stock question.
- Demo06's sequential and parallel lookup answers retain the full condition.
  Both use five model calls. The fixed code-lookup variant uses one composition
  call. The shared limiter means parallel execution did not improve elapsed
  seconds in this run. The ticket reply promises no repair date.
- Demo07's model checker approves 'out of stock' without a literal zero. The
  deterministic checker flags the missing digit required by its format contract,
  not a wrong stock assertion. The code-checked repair includes zero and passes.
- Demo08's two proposals both retain the manual's inspection-first condition.
  The judge selects inspection with that evidence. Both independently generated
  notes pass the factual/format checks ; the code selects the shorter one.

## Demo01 to demo08 measurements

One final execution of each operation on 14 October 2026, at `COURSE_RPS=0.12`.
The expected rejected-history request is the only model error in these rows.

| Notebook | Operation | Calls | Input tokens | Output tokens | Seconds | Model errors |
| --- | --- | --- | --- | --- | --- | --- |
| demo01 | subagents | 6 | 996 | 282 | 52.7 | 0 |
| demo02 | supervisor | 7 | 959 | 272 | 60.2 | 0 |
| demo02 | hierarchical | 8 | 1097 | 342 | 67.2 | 0 |
| demo03 | router sequential | 4 | 419 | 108 | 34.8 | 0 |
| demo03 | router parallel | 6 | 824 | 261 | 50.7 | 0 |
| demo04 | handoff missing sibling | 1 | 0 | 0 | 11.8 | 1 |
| demo04 | handoff lost work | 1 | 156 | 40 | 6.3 | 0 |
| demo04 | handoffs fixed | 4 | 1215 | 106 | 33.9 | 0 |
| demo04 | triage | 2 | 362 | 46 | 16.3 | 0 |
| demo04 | specialist step | 4 | 1555 | 119 | 33.7 | 0 |
| demo05 | skills | 4 | 1139 | 175 | 35.1 | 0 |
| demo05 | isolated specialist | 2 | 226 | 44 | 16.5 | 0 |
| demo06 | sequential ticket | 2 | 106 | 52 | 18.4 | 0 |
| demo06 | sequential lookup | 5 | 621 | 171 | 41.8 | 0 |
| demo06 | parallel lookup | 5 | 627 | 185 | 42.4 | 0 |
| demo06 | orchestration in code | 1 | 129 | 57 | 8.1 | 0 |
| demo07 | model checker | 2 | 241 | 80 | 18.4 | 0 |
| demo07 | code checker | 1 | 137 | 36 | 8.1 | 0 |
| demo08 | debate with judge | 3 | 520 | 147 | 26.6 | 0 |
| demo08 | generate and filter | 2 | 191 | 95 | 16.9 | 0 |

## Demo09 comparison

Three runs per pattern, 21 total, on the same question. All 21 answers were
read against the source records and preserve the stock, location and
replacement condition. All completeness checks also pass. No model errors or
malformed tool calls occur in these rows. This is a small task-specific sample,
not a general reliability claim. Separate column medians can combine values
from different runs.

| Pattern | Correct | Calls | Input tokens | Output tokens | Seconds |
| --- | --- | --- | --- | --- | --- |
| single agent | 3/3 | 2 | 435 | 113 | 17.9 |
| subagents | 3/3 | 6 | 954 | 263 | 50.4 |
| handoffs fixed | 3/3 | 4 | 1,215 | 108 | 33.9 |
| skills | 3/3 | 4 | 1,139 | 162 | 33.8 |
| router | 3/3 | 6 | 816 | 247 | 50.0 |
| custom workflow | 3/3 | 5 | 632 | 192 | 42.2 |
| code lookups | 3/3 | 1 | 129 | 57 | 9.4 |

Raw rows : `notebooks/05-multi-agent-patterns/demo09-results.json`.
Each row records model, rate, run, calls, token counts, elapsed seconds,
malformed/error counts, checks and the full answer. Every run uses
`COURSE_RPS=0.12`. Code lookups use the known arguments and therefore do not
measure arbitrary question parsing. The single agent answers this task with
fewer calls and tokens than every multi-agent variant. Adding workers has not
earned its cost on this particular question.

## Final notebook execution

All nine notebooks execute with zero cell errors and their outputs have been
read. Final-version runs had no connection errors or timeouts, so no network
retry was needed. Earlier calibration runs motivated the explicit replacement-
condition wording. A final source audit caught demo02's older question cell
from an in-flight generation/run race. It was executed again after the source
was frozen, and its final tasks and answers now include the condition. Prose
additions explain possible boundary failures and retain outputs of unchanged
executed code.

| Notebook | Status | Cell errors | Runner seconds |
| --- | --- | --- | --- |
| demo01-subagents.ipynb | PASS | 0 | 55.7 |
| demo02-supervisors.ipynb | PASS | 0 | 130.2 |
| demo03-router.ipynb | PASS | 0 | 88.2 |
| demo04-handoffs.ipynb | PASS | 0 | 105.2 |
| demo05-skills.ipynb | PASS | 0 | 54.6 |
| demo06-workflows.ipynb | PASS | 0 | 113.3 |
| demo07-maker-checker.ipynb | PASS | 0 | 29.2 |
| demo08-debate-and-selection.ipynb | PASS | 0 | 46.1 |
| demo09-what-each-pattern-costs.ipynb | PASS | 0 | 709.7 |

Runner seconds include kernel/setup overhead and are distinct from the
per-operation measurements. The intentional provider rejection in demo04 is
caught and printed ; it is one expected model error, not a notebook cell error.
`run-status.json` consolidates the nine final per-notebook reports.

## API differences and limits

The documented last-message handoff exhibits both measured faults on the
pinned stack. The sibling-result rejection and lost-work half answer are
reproduced against the live provider ; serial tool calls and full-history
forwarding repair this example. The middleware variant and all other taught
APIs run on the pinned versions. No additional API incompatibility or shared-
file blocker remains. The final supervisor and hierarchy answers are complete.
The intentionally broken handoffs, rejected triage value and checker format
difference remain visible learning points. Keyword checks and the small
benchmark sample remain the stated limits.

Only module-owned source, notebooks, execution results and this report were
written. The PDF build is left to the lead, as required by the brief.
