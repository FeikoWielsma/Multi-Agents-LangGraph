# ARI520 capstone measurements

Date : 14 October 2026. Environment : Windows, Python 3.12.13, course `uv` environment. Model : `openai/gpt-6-luna` through OpenRouter, temperature 0, reasoning effort `none`, `max_tokens=900`, `max_retries=0`. All solution runs use `COURSE_RPS=0.08` and run one at a time from the repository root with `uv run python build/run_notebook.py solutions/capstone-stageN.ipynb`.

Package pins : LangChain 1.4.5, LangChain Core 1.6.10, LangGraph 1.2.15, Deep Agents 0.7.24, agentevals 0.0.9, langgraph-cli 0.4.33, langgraph-api 0.16.0, langgraph-sdk 0.4.7. No shared package or setup file changed.

The notebook counter counts attempted model starts and provider-reported input/output tokens from completed replies. A2A usage comes from all AI messages in the remote thread. The served desk returns the server counter delta, including specialist calls. Async totals add the complete dispatcher history and the child's measured usage. Per-ticket durations include rate limiting, local work and transport; they are not model latency. Runner durations also include kernel startup. Notebook totals start after common setup.

The fixed five-case subset is `db-01`, `db-03`, `db-04`, `man-01`, `mix-01`, selected by id from `data/capstone/eval.jsonl`. Stages 1 and 2 compare the first three on the same questions. All data is fictional. The notebooks' phrase scores are initial accuracy screens, with the same `answer_contains` alternatives as the labelled data. They can pass an incomplete or contradictory answer. Manual output review is recorded separately below.

## Stage 1

- Runner : PASS, 0 errors, 68 seconds (rounded runner output).
- Notebook total : 5 calls, 1288 input tokens, 254 output tokens, 65.1 seconds.
- Three database cases : all phrase screens True. Stock is 0 for CT-SR-03; firmware is 5.1 for CT400-2023-0342; Priya Raman and Tomasz Nowak are certified for MR-150.
- Every saved answer equals its returned answer. Each case uses a separate UUID thread.
- Unknown device : states that no record was found, with no invented firmware.
- Mixed fault : identifies the CT-400 and lists stock, but says a manual is needed before selecting a replacement. The supplied evidence does not contain a fault-code interpretation.

## Stage 2

- Runner : PASS, 0 errors, 193 seconds (rounded runner output).
- Notebook total : 15 calls, 4030 input tokens, 526 output tokens, 189.7 seconds.

| Design and case | Calls | Input tokens | Output tokens | Seconds |
| --- | --- | --- | --- | --- |
| Stage 1 db-01 | 1 | 167 | 36 | 14.1 |
| Stage 1 db-03 | 1 | 396 | 22 | 12.2 |
| Stage 1 db-04 | 1 | 197 | 20 | 14.0 |
| Stage 2 db-01 | 4 | 1081 | 147 | 50.5 |
| Stage 2 db-03 | 4 | 1115 | 143 | 49.5 |
| Stage 2 db-04 | 4 | 1074 | 158 | 49.3 |

Both designs' three screens passed. Output review confirmed the same database facts. The scheduling supervisor adds that availability is unknown, consistent with the absence of a calendar. Worker contexts contain four messages each; the supervisor receives only their final summaries. For these simple database questions the added agents increased cost without an observed correctness improvement.

Comparison totals : workflow 3 calls, 760 input tokens, 78 output tokens; supervisor 12 calls, 3270 input tokens, 448 output tokens. These are one run per case, not a reliability benchmark.

## Stage 3

- Runner : PASS, 0 errors, 191 seconds (rounded runner output).
- Notebook total : 13 calls, 4432 input tokens, 699 output tokens, 187.4 seconds, including A2A calls.
- Mixed diagnosis : 9 calls, 3529 input tokens, 548 output tokens, 131.2 seconds. Three findings reached the judge.
- Manuals assistant UUID : `244d99ea-f6af-5ded-b17f-bbbdc59094be`, resolved by graph id `manuals`. The A2A request uses a fresh UUID context, `SendMessage`, `ROLE_USER` and blocking completion.
- Final diagnosis correctly identifies CT-FN-02, stock 6 at Houten, and replacement only when measured airflow is below 80 percent. It cites the error-code manual and fan procedure.
- Parts worker declines to infer a replacement from inventory alone. The scheduling branch uses the malformed model name `CT400` and therefore reports no engineers. That finding is not reliable for the canonical CT-400 model. The mixed question does not request an engineer; the judge excludes that irrelevant result. Retained as evidence of a worker/context error for discussion, not counted as a scheduling success.
- Approval request : 1 call, 191 input / 49 output tokens. Ledger empty at the top-level interrupt; payload contains the requested fan, quantity 1, S01, WO-9001, stable request id, and 420 EUR total.
- Approval resume : 1 call, 262 input / 33 output tokens. One simulated order appears after approval.
- Rejection request/resume : 2 calls, 450 input / 69 output tokens. Rejected request id absent from the ledger. The notebook checks the top-level graph's interrupts and resumes that same thread.
- Final cell reports servers stopped True and checks port release. Only port 2145 was used.

## API and measurement limits

- `langgraph-api` 0.16.0 requires assistant UUIDs in the agent card and A2A route. A2A `contextId` is a UUID thread id, matching `build/measurements-06.md`. Graph names remain valid for SDK runs.
- The v1.0 `SendMessage` envelope uses `ROLE_USER`, returns `result.task`, and reports `TASK_STATE_COMPLETED`; JSON-RPC's envelope version remains 2.0.
- Deep Agents compiled subagents use a `runnable` entry. They retain their own approval code; harness `interrupt_on` is not added to a compiled subagent.
- `agentevals` 0.0.9 supports `superset` trajectory matching with `tool_args_match_mode="ignore"`. An offline probe scored a matching lookup True and a missing lookup False. This measures tool coverage, not argument correctness or factual accuracy.
- The stage 4 code metric counts non-empty lines in the additions for stages 3 and 4. Common setup, data tools and specialist factories are excluded from both. Stage 4 reuses the stage 3 approval implementation, so this is a measure of added orchestration code, not total deployable application size.
- Stage work allocations of 45 to 75 minutes are teaching budgets. The async worker's 15-second initial wait is an injected hold to make the lifecycle observable.

## Price snapshot

Source : [OpenRouter models API](https://openrouter.ai/api/v1/models), read 14 October 2026 without credentials, selecting `openai/gpt-6-luna`.

- Prompt : `0.0000001` USD per token, or 0.10 USD per million.
- Completion : `0.0000005` USD per token, or 0.50 USD per million.
- Cached input read : `0.00000001` USD per token.
- The API also lists a higher tier beginning at 272000 prompt tokens; none of these short ticket runs approaches that tier.

Required ticket estimates use uncached input and output rates. They exclude hosting, retries, evaluation extensions, discounts and cache effects. The stage 5 notebook fetches its own dated snapshot so reruns do not silently rely on this date.

## Validation

- Guide lint : `bun run ../../Presentation-Template/build/lint-slides.ts ../src/exercises/99-capstone.md` from `build/` : PASS, all slides within budget. No PDF build.
- All five solution notebooks parse as Python, including top-level notebook awaits.
- All five skeletons contain `____` blanks, collapsed hints, no execution counts and no outputs.
- Generated solution code in all five notebooks matches the builder's solution branches and shared setup exactly. The stage 4 count cell is separate and has a unique id.
- Guide structure : five stage sections, seventeen steps and thirty formatted pages, counted from the Markdown separators after front matter.
- Builder and runtime exports contain no credential values. Runtime files remain in isolated capstone server folders under exercises or solutions.

## Stage 4

- Runner : PASS, 0 errors, 995 seconds (rounded runner output).
- Notebook total : 76 calls, 72731 input tokens, 4078 output tokens, 991.3 seconds. This includes both five-case designs and the harness order rejection.

| Case | Graph calls | Graph input / output | Graph seconds | Deep Agent calls | Deep Agent input / output | Deep Agent seconds |
| --- | --- | --- | --- | --- | --- | --- |
| db-01 | 7 | 2085 / 239 | 105.6 | 5 | 8791 / 185 | 62.6 |
| db-03 | 7 | 1642 / 212 | 90.2 | 4 | 5931 / 139 | 50.7 |
| db-04 | 7 | 2168 / 241 | 91.6 | 5 | 8615 / 163 | 62.6 |
| man-01 | 7 | 2527 / 422 | 91.7 | 9 | 11360 / 862 | 111.5 |
| mix-01 | 10 | 5195 / 595 | 129.0 | 10 | 15657 / 822 | 125.6 |
| Total | 38 | 13617 / 1709 | 508.1 | 33 | 50354 / 2171 | 413.0 |

Phrase screens : graph 5 / 5, Deep Agent 4 / 5. Manual answer review : both 4 / 5. The graph's `db-04` includes Priya Raman and Tomasz Nowak while saying their MR-150 certification is not established. That is incorrect against the database and a false positive for the phrase screen. The Deep Agent says it could not find certified engineers, also incorrect. The other four answers preserve the requested facts and the mixed diagnosis's airflow condition. The graph's manual-only answer adds unnecessary uncertainty because the non-manual workers lack that evidence; its cited error-code interpretation remains correct.

The guide and notebook now explicitly ask students to inspect the certification failure and the optional scheduling parameters. No failed answer was removed, and no model was switched. These are evaluation findings, not notebook execution failures.

The Deep Agent uses 5 fewer calls in this sample while increasing input tokens from 13617 to 50354. Both designs include specialist work; graph totals include the separately served manuals agent. Wall time also includes the deliberately conservative cross-process rate gate on graph calls, so the timing difference does not establish a general harness latency advantage.

Non-empty additions : stage 3 orchestration 99 lines, stage 4 orchestration 48 lines. Counts include the respective supplied helper/skill definitions and exclude shared tools. The reused approval code is outside the stage 4 count, as stated in the guide.

Harness approval transfer : 3 calls, 5629 input / 156 output tokens, 36.9 seconds before the interrupt; rejection resume 2 calls, 3131 input / 42 output tokens, 25.5 seconds. The nested orders worker propagated its interrupt to the Deep Agent. Rejection left the ledger empty. The manuals server stopped before the harness cases and the final cell again checked shutdown.

## Stage 5 correction run

The first run failed in the evaluation cell on an unused `messages_from_dict` import from `langchain.messages`. The installed package does not export that helper there. It was removed; the actual evaluator uses the verified `langchain_core.messages.convert_to_messages`. The dependent cost loop then had no scores. No package change was needed.

That failed attempt took 205 seconds, made 15 model calls, and consumed 26243 input / 1154 output tokens. Async launch returned status running, the child completed, and the dispatcher fetched success. The final stop cell executed and released the server. No connection error occurred, so the one-minute Wi-Fi retry rule did not apply. The full corrected notebook was rerun sequentially, rather than leaving partial outputs.

Output review of the first async sample : the fault interpretation, CT-FN-02 identifier, firmware 5.3 and airflow condition were retained, but the final answer did not preserve the inventory count. Completion status is not a correctness score. This sample is not included in the corrected run's five-ticket evaluation or final notebook totals; its consumed tokens are recorded here.

## Files and delivery choices

Files authored :

- `build/make_capstone.py`
- `src/exercises/99-capstone.md`
- `exercises/capstone-stage1.ipynb` through `capstone-stage5.ipynb`
- `solutions/capstone-stage1.ipynb` through `capstone-stage5.ipynb`
- `build/measurements-capstone.md`

Runtime exports from the executed solutions : `solutions/capstone-stage3-server/` and `solutions/capstone-stage5-agent-server/`, each containing `capstone_runtime.py`, `graphs.py` and `langgraph.json`. Earlier stage 5 attempts also wrote `solutions/capstone-stage5-server/`. The skeletons contain the same export-writing cells, using isolated folders under `exercises/` when students run them. Development checkpoint storage is ignored by the repository; transient server logs are not teaching artifacts.

No lecture slide, exercise 01 to 11, ARI510 file, shared builder, setup cell, dependency pin, `.env` or PDF was edited. No shared change is required to run the capstone.

Delivery choice for the lead : keep the observed certification failure as an evaluation lesson, or make a repair of scheduling arguments and synthesis a required extension. The guide currently asks students to inspect it and retains the measured failures. Expanded eval sets and LLM judges remain optional; the Tuesday A2A wiring has an explicit trainer cut. These are curriculum choices, not execution blockers.

### Async inventory repair and retry

The import-corrected intermediate stage 5 run passed execution (585 seconds; 45 calls, 80775 input / 2729 output tokens), and its five served cases passed coverage and manual answer review. Its five-ticket list-price estimate was 0.006038 USD. The async answer still omitted the stock count. The parts worker now receives an explicit inventory task, including device lookup and the model's complete parts catalogue; the manuals worker receives diagnosis and conditions. The judge is instructed to use each source for its domain. A required async-result check inspects the fan identifier, count and depot.

The first generated version of that check contained backspace characters from a nested Python string's `\b` escapes. The final builder uses lookarounds without those escapes. Offline checks accept both `6` and `six`, and reject a `2026` document date as stock evidence. This was a generation error, not a package difference.

The next attempt failed that old generated check and encountered a local connection refusal during the fourth served case. Runner duration : 329 seconds. Three completed evaluation cases account for 12 calls, 21497 input / 458 output tokens; the final notebook counter excludes async usage because the failed assertion preceded its accumulation. A read-only child-state inspection recovered 7 child calls, 5015 input / 1079 output tokens and the inventory count 6 at Houten. Parent tokens and the interrupted fourth case are not fully measured in that partial attempt. No complete billing total is inferred from those partial figures.

The server log stops abruptly during the fourth case without an explanatory exception. A one-minute pause was observed before retry. Automatic command policy rejected recursive dev-cache deletion; the final run instead uses a fresh `capstone-stage5-agent-server` project, leaving the old cache untouched. No approval or shared-file change was needed. This is a fresh retry, not evidence that the cache caused the server exit.

## Stage 5 final run

- Runner : PASS, 0 errors, 505 seconds (rounded runner output).
- Notebook total : 39 calls, 66497 input tokens, 2837 output tokens, 500.9 seconds.
- Async sequence : 14 calls, 22669 input / 1293 output tokens. Launch returned running; join completed the child; the dispatcher fetched success. The async result now includes CT-FN-02, stock 6 at Houten, and replacement only below 80 percent airflow. The required identifier/count/depot check passed. Its citations use document identifiers in this sample instead of the requested file-name format; citation formatting is not automatically scored.
- Five served tickets : 25 calls, 43828 input / 1544 output tokens. All six required specialist coverage checks and all five system coverage checks scored True through agentevals 0.0.9.

| Case | Agent coverage | System coverage | Phrase screen | Manual answer review | Calls | Input / output tokens | Seconds | Estimated USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| db-01 | parts True | True | True | correct | 4 | 7198 / 144 | 56.1 | 0.0007918 |
| db-03 | parts True | True | True | correct | 4 | 7219 / 144 | 43.1 | 0.0007939 |
| db-04 | scheduling True | True | False | incorrect | 4 | 7091 / 144 | 50.6 | 0.0007811 |
| man-01 | manuals True | True | True | correct | 4 | 7881 / 346 | 50.3 | 0.0009611 |
| mix-01 | parts / manuals True | True | True | incomplete | 9 | 14439 / 766 | 114.4 | 0.0018269 |

Final phrase screen : 4 / 5. Manual answer review : 3 / 5. Scheduling called `engineers(model="Aurelia MR-150", region="")`, which does not match the canonical MR-150 rows. Mixed diagnosis called `lookup_parts(model="CT400")`, which does not match CT-400. The latter answer names CT-FN-02 but omits stock, so the alternatives-based phrase screen passes an incomplete answer. The earlier intermediate five-case run answered all five correctly; this variation is retained and explained rather than selecting the better run as the final score.

The notebook prints the actual tool arguments and the guide names these failure modes. Coverage with ignored arguments establishes that tools were selected, not that their inputs were valid. Argument validation, per-agent fact scoring and human labels are the stated follow-up extensions. No accuracy threshold is claimed for this small sample.

Public price snapshot : 14 October 2026, OpenRouter models API, prompt 0.0000001 USD/token and completion 0.0000005 USD/token. Final five-ticket estimate : 0.0051548 USD, or 0.00103096 USD per ticket on average. Including the async sequence, the final stage 5 notebook's uncached token estimate is 0.0080682 USD. The five final solution runs together account for 148 calls, 148978 input / 8394 output tokens and a 0.0190948 USD list-price estimate. Those figures exclude earlier correction attempts; they do not claim the actual amount billed.

Final cell reports servers stopped True. The fresh-server retry completed eight server runs without a background-run failure. No browser was opened.

## Final acceptance checks

| Solution | Final runner status | Errors | Runner seconds | Calls | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| capstone-stage1 | PASS | 0 | 68 | 5 | 1288 | 254 |
| capstone-stage2 | PASS | 0 | 193 | 15 | 4030 | 526 |
| capstone-stage3 | PASS | 0 | 191 | 13 | 4432 | 699 |
| capstone-stage4 | PASS | 0 | 995 | 76 | 72731 | 4078 |
| capstone-stage5 | PASS | 0 | 505 | 39 | 66497 | 2837 |

Every solution code cell has an execution count and no error output. Every skeleton has empty outputs, no execution counts, blanks, hints and unique cell ids. All solution code matches the builder branches and shared setup. Prose-only output-review and trainer-cut clarifications retained outputs only after exact code-cell equality checks.

Final guide lint : PASS. Final credential scan : PASS over 25 authored notebooks, guides, builder/report and generated server code/config/log files; no `.env` key values were found. Final socket probes : 2144 and 2145 both released. No PDF build ran. The optional local-manuals cut explicitly skips server startup and the remote-usage assertion, retains the three-finding check, and initializes the empty server list for cleanup.

Notebook execution acceptance is complete. The documented accuracy failures and citation-format variation remain teaching/evaluation findings; the reports do not present execution PASS or tool coverage as an accuracy guarantee.
