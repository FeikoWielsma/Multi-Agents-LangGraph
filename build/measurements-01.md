# Measurements : Introduction to LangGraph

## Environment and method

Execution date : 14 October 2026. The notebooks use the generated shared setup,
`openai/gpt-6-luna` through OpenRouter, temperature 0 and reasoning effort
`none`. Every notebook run sets `COURSE_RPS=0.08`. Runs are sequential.
Installed metadata confirms `langchain` 1.4.5, `langgraph` 1.2.15 and
`deepagents` 0.7.24.

`Meter.on_llm_end` counts completed model calls and sums each returned
message's `usage_metadata.input_tokens` and `output_tokens`. Nested agent
calls inherit the callback. Failed requests and provider retries are not
completed calls in these tables. Token values are provider-reported usage,
not local token estimates. Wall time includes the shared rate limiter and
must not be presented as model latency.

Answers are preserved in the executed notebooks. The `correct` helper checks
accepted text fragments, with `|` separating alternatives. It is a narrow
fact check, not a complete answer-quality evaluator. Reading the answers is
required to catch contradictions, incidental numeric matches and unsupported
claims.

## Dataset counts

The notebooks load 82 manual sections, 43 tickets, 10 buses and 13 parts.
The sections are obtained by splitting each of the 31 Markdown manuals on
`\n## `. SQLite count queries also confirm 5 depots, 4 mechanics and 4 work
orders. The relevant stock rows are CE-DA-03 = 0, CE-CF-02 = 6 and MM-BT-02 = 0.
These are supplied fictional data values, checked locally on the execution
date, not model estimates.

## Demo01 method

The same six service desk questions run once at each tool-list size. Eight
tools read Veenhaven Bus records. Another 52 tools describe unrelated company
systems and return no records. The four sizes are 8, 20, 40 and 60 tools.
`random.Random(n)` shuffles each list reproducibly. The agent starts a fresh
conversation for every question. A detour is a returned tool message from
one of the added systems. This probes schema load and tool selection with
inert distractors ; it does not benchmark working integrations with all
company systems. The questions are authored over the dataset, not imported
from `eval.jsonl`.

## Demo01 results

PASS, zero execution errors, 795 seconds including rate limiting and kernel
startup. All 24 answers were read. The observed fact-check scores are :

| tools | expected facts | calls | input tokens | output tokens | input/call, floored | distractor calls |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 6/6 | 15 | 8,335 | 540 | 555 | 0 |
| 20 | 6/6 | 17 | 14,868 | 532 | 874 | 0 |
| 40 | 5/6 | 15 | 19,038 | 486 | 1,269 | 0 |
| 60 | 6/6 | 16 | 26,719 | 437 | 1,669 | 0 |

The missed fact at 40 tools is Nora Dalen in the region-Zuid mechanic question.
The answer treats F-CD-101 as a fleet number and refuses to identify a
mechanic. The other sizes also attempt the incorrect fleet lookup, but
eventually name Nora Dalen with a qualification. Thus the run shows a
non-monotonic expected-fact miss, not a reliable degradation threshold.
The added tool descriptions increase average input tokens per call in this
run, while none of the distractor tools is selected.

Answer review catches additional errors that the narrow fact check misses :
the 20-tool and 40-tool historical-ticket answers call RR-BP-03 a door
controller. The database identifies it as the auxiliary battery pack. The
returned part number satisfies the scorer, but the component label is wrong.
The baseline's ticket answer reports repair durations from matching tickets,
which is outside the scored facts. Scores are therefore labelled expected
facts, not comprehensive correctness. No prompt or tool list was changed to
force a decline or conceal these outputs.

## Demo02 method

Section a runs a deterministic bus/manual lookup graph, including conditional
routing and update streaming, with no model call. Section b invokes one
supervisor with a manuals subagent and a parts subagent as tools. Each
subagent receives a new user message containing the delegated question.
Callbacks include the supervisor and both specialists. The stock check
accepts CE-CF-02 or cooling fan and 6 or six, then the output is read.

The first execution completed with zero errors in 105 seconds, but the
answer was wrong : the parts specialist treated F-CE-110 as a part number in
its returned answer and could not confirm stock. Its tool set had no bus lookup to resolve a fleet
number into a model. That run used 8 completed model calls, 2,444 input tokens
and 359 output tokens. The builder now gives that specialist `bus_info` and
instructions distinguishing fleet numbers, fault codes and part numbers.
The repair changes its available context and tool contract ; it does not
hard-code the expected part or stock. The corrected run is recorded below.

## Demo02 results

The corrected execution passes with zero errors in 106 seconds. The first
graph routes F-CD-202 to the workshop, F-CE-305 to on-site work, and streams
the MM-09 auxiliary-battery action. The supervisor's final answer correctly
identifies CE-CF-02, the cooling-fan replacement condition, six units in stock
and Rietpoort. Its fact check is true. The run uses 8 completed model calls,
2,332 input tokens and 313 output tokens, including both specialists.
The delegated questions and returned answers were read. This is one
successful corrected run, not an estimate of reliability.

## Demo03 method

The task asks for the spare part and stock for MM09-2025-2350 with F-MM-210.
Section a uses structured model extraction, deterministic lookups, and model
answer generation. Sections b and c let an agent select among the same four
service desk tools. The comparison shares a task, not an identical execution
path. The expected facts are MM-BT-02 / auxiliary battery and zero stock.

Installed `create_deep_agent` source confirms filesystem middleware,
delegation and summarisation in the default stack. It does not add
`TodoListMiddleware` by default. Planning is opt-in. The default virtual
backend does not provide a working host shell. This corrects the older
builder's todo-list description ; no dependency change was required.

## Demo03 results

PASS, zero execution errors, 130 seconds including rate limiting and kernel
startup. All three answers were read and correctly identify MM-BT-02 as the
auxiliary battery with zero units in stock at Zandveen.

| implementation | fact check | calls | input tokens | output tokens |
| --- | --- | --- | --- | --- |
| hand-written StateGraph | pass | 2 | 216 | 52 |
| create_agent | pass | 4 | 1,962 | 110 |
| create_deep_agent | pass | 4 | 9,732 | 118 |

Both agents selected `bus_info`, `search_manuals` and `parts_for_model`.
The Deep Agent did not use its additional harness tools on this short task.
Its larger input is observed overhead on this run, not a claim that the
harness cannot help a longer task. These are single runs, not medians.

## Demo04 method

The same four driver reports run through a workflow and a tool-calling agent.
Three reports contain recognised fleet numbers and error codes. The fourth
describes a ramp symptom without a code. The fixed workflow uses regular
expressions, deterministic data lookups and one answer-generation call for
each recognised report. Its missing-code branch escalates without a model
call. The agent receives the four service desk tools and can search symptoms.
The final table prints calls and input tokens ; the preceding per-report
meters also print output tokens. Answers must be read independently of cost.

## Demo04 results

PASS, zero execution errors, 243 seconds including rate limiting and kernel
startup. All eight outcomes were read.

| report | workflow calls | workflow input | workflow output | agent calls | agent input | agent output |
| --- | --- | --- | --- | --- | --- | --- |
| CE12-2021-0117, F-CE-110 | 1 | 145 | 56 | 4 | 2,079 | 148 |
| CD12-2024-0098, F-CD-202 | 1 | 147 | 63 | 3 | 1,308 | 154 |
| RR14-2022-0210, F-RR-120 | 1 | 140 | 52 | 5 | 2,870 | 166 |
| MM09-2025-2311, ramp symptom, no code | 0 | 0 | 0 | 4 | 3,164 | 205 |

For the coded reports, both implementations identify the appropriate part
and stock : CE-CF-02 = 6, CD-FP-02 = 0 and RR-BP-03 = 5. Their first actions
match the manuals, including the withdrawal and diesel-specialist instruction
for F-CD-202. The workflow escalates the report without a code. The agent
finds the ramp test and MM-RM-01 with 3 units in stock at Zandveen. It marks
the motor diagnosis as unconfirmed. This is a relevant procedure and
conditional diagnosis, not proof that the motor is the cause.

The workflow totals 3 model calls, 432 input tokens and 171 output tokens.
The agent totals 16 calls, 9,421 input tokens and 673 output tokens. The
workflow's narrower path and the agent's additional symptom search are both
visible. No general speed or accuracy claim follows from these four reports.

## Numbers in the opening slides

The seven opening slides are retained without content changes. These numbers
are attributed reports, not experiments reproduced by this module.

| slide | figures | record and method |
| --- | --- | --- |
| A Crew of Thirty Agents | about 30 agents ; October 2026 | Yair's public post and permission recorded in `research-2026-10.md` section 5 ; personal account |
| Ten Thousand Agents on Navier-Stokes | order of 10,000 ; 88 hours ; 17 hours ; 2.7 million messages ; about 130 billion output tokens | OpenAI report dated 8 September 2026, updated 10 September ; internal-model run reported by OpenAI |
| How the Swarm Was Organised | about 100 agents | same OpenAI report, related Euler investigation |
| A Research Team of Agents | 90.2 percent ; 4 times ; 15 times ; 80 percent | Anthropic's June 2025 internal research evaluation and token analysis |
| Recursive Language Models | about two orders of magnitude ; December 2025 | Zhang, Kraska and Khattab paper, version history and reported long-input experiments |
| The Bill for a Swarm | 2 calls ; 4 to 6 calls ; 28 times input tokens | `build/measurements.md`, 13 October 2026, three Luna runs per pattern ; medians, 11,044 / 399 rounds to 28 |
| Patterns Behind the Examples | module numbers 05 to 08 | curriculum mapping in `plan.md` ; identifiers, not experimental measurements |

Primary references : [OpenAI](https://openai.com/index/navier-stokes-solution),
[Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system),
[RLM paper](https://arxiv.org/abs/2512.24601),
[Prime Intellect](https://www.primeintellect.ai/blog/rlm),
[Zhang interview](https://www.latent.space/p/rlm),
[firstmate](https://github.com/kunchenguid/firstmate).
The opening's claim about waste is an attributed suspicion, with the
interview's uncertainty preserved in its notes.

## Versions and delivery estimates

The six competing framework versions are the PyPI snapshot of 13 October
2026 in `research-2026-10.md` section 2. They are not benchmark results and
the packages were not installed for this module. The primary documentation
was checked for the capabilities described on the new slides.

The 90-minute module allowance and 20-minute opening allowance are planning
estimates, not measured delivery times. The first opening slide's existing
note says six slides ; the retained opening actually contains seven. The
first slide after the opening records seven and carries the module timing.
The three-day progression and delivery dates, 2 to 4 November 2026, come
from `plan.md`.

## Verification

All four notebooks were executed sequentially at `COURSE_RPS=0.08` and their
outputs were read. Final executions have zero errors. The initial demo02
answer-quality failure and its correction are recorded above. No connection
error, timeout or rate-limit failure occurred in these notebook executions.

| notebook | final execution | errors | elapsed seconds |
| --- | --- | --- | --- |
| demo01-one-agent-limits | pass | 0 | 795 |
| demo02-first-look | pass, corrected answer checked | 0 | 106 |
| demo03-three-levels | pass, all answers checked | 0 | 130 |
| demo04-workflow-or-agent | pass, all outcomes checked | 0 | 243 |

The slide file contains 32 slides : seven retained openers and 25
continuation slides. Slide lint reports no warning for the file on
14 October 2026 ; the lint run's two warnings belong to modules 08 and 09.
`check_code.py` reports no error for the file. No PDF build was run.

All seven demo pills match notebook sections in both directions, appear once
and follow the course-map order. First sections use notebook slugs ; later
sections use their own kebab-case slugs. The single-child lead-in share is
8 of 130 top-level bullets, 6 percent, counting the retained openers.
Python cells parse and the saved execution outputs correspond to
the final builder's code. Prose-only regeneration retains those outputs.

A previous attempt's module01 runner was still active when this round
started. Its process tree was stopped to prevent concurrent execution and
stale file writes. The other modules' runners were left alone. Only the
assigned module paths were edited. The APIs used by the notebooks execute
on the installed pins ; the notable default-behaviour correction is Deep
Agents' opt-in todo planning.

## Merge of 14 October 2026

A second agent on the same assignment, started at 09:39, merged its slides
into this set after the run above. It added Context Engineering, Conditional
Routing, A First Graph, Three Levels Compared, The firstmate Orchestrator and
The Capstone in Five Stages, put the docs' single-agent warning on When One
Agent is Enough, and replaced the prose of The Three Days with a table of days
and the course thesis. The `demo02 · first-look` pill moved from Graph-Based
Architecture to A First Graph, whose code matches demo02 a. No notebook was
rerun for the merge.

Every number on the added slides comes from the tables above or from
`build/measurements.md` :

| slide | figures | source |
| --- | --- | --- |
| Three Levels Compared | 2 / 4 / 4 calls ; 216 / 1,962 / 9,732 input tokens ; all correct | Demo03 results |
| When One Agent is Enough | 2 calls against 4 to 6 per pattern | `build/measurements.md`, 13 October 2026 |
| The Capstone in Five Stages | five stages, modules 03 to 09 | `plan.md`, the capstone |

The quotations on Context Engineering and When One Agent is Enough were read
on `docs.langchain.com/oss/python/langchain/multi-agent` on 14 October 2026.
