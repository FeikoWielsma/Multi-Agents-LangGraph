# Module 10 measurements

Date : 14 October 2026. Module : Real-World Applications (`10-real-world-applications`).

## Environment and method

The course model is `openai/gpt-6-luna` through OpenRouter, reasoning effort `none`, temperature 0. Installed versions verified on Python 3.12:
- `langchain`: 1.4.5
- `langgraph`: 1.2.15
- `deepagents`: 0.7.24

Notebook execution followed the module brief rate limit budget `COURSE_RPS=0.03`, running notebooks sequentially via `build/run_notebook.py`. All workers and model instances share the setup cell rate limiter (`InMemoryRateLimiter(requests_per_second=0.03, check_every_n_seconds=0.1, max_bucket_size=1)`). No API keys or credentials from `.env` are printed or written to files.

## Notebook execution

| Notebook | Status | Errors | Runtime | Model calls | Key verified output |
| --- | --- | --- | --- | --- | --- |
| `demo01-research-agent.ipynb` | PASS | 0 | ~70 s | 3 | Leading fault `F-RR-120` (27.5 h) ; 3 sources cited (`tickets.csv`, 2 manuals) |
| `demo02-customer-support.ipynb` | PASS | 0 | 71 s | 2 | Triage routed to `manuals` ; 5 evidence items gathered ; part `CE-IM-04` has stock 2 in Broekdam |
| `demo03-code-review.ipynb` | PASS | 0 | 106 s | 3 | Dispatched 2 parallel reviewers ; judge selected 3 supported findings ; pipeline checks: pass (3/3) |
| `demo04-data-and-content.ipynb` | PASS | 0 | 71 s | 2 | SQL query returned 4 workload rows ; content checks: 4/4 true ; release: ready for editor |

`demo05 · firstmate` is a live trainer demonstration conducted on Feiko's laptop and has no notebook in the student distribution.

## Measured facts and figures on slides

Every figure and factual assertion on module 10 slides originates from either `build/research-2026-10.md` primary sources or verified notebook executions on the Veenhaven Bus dataset. No figures were invented.

### Demo measurements (Veenhaven Bus dataset)

- `manuals` corpus: 31 markdown files in `data/demo-world/manuals/`.
- `tickets.csv`: 43 ticket records.
- Leading fault by mechanic hours: `F-RR-120` (Door controller not responding) with 27.5 total recorded mechanic hours (`demo01`).
- Second leading fault: `F-MM-210` with 16.0 hours (`demo01`).
- Support handoff state: Bus `CE12-2021-0117`, fault `F-CE-410`; part `CE-IM-04` verified stock of 2 units at depot Broekdam (`demo02`).
- Code review patch: `reserve_part` function with missing-part bug and unvalidated stock decrement; 2 parallel reviewer branches (`correctness`, `database_safety`); deterministic token checks for `reserve_part`, `SELECT`, `UPDATE` pass (`demo03`).
- Data analysis query: `work_orders` table grouping by `error_code` returns top 4 repeat faults (`F-RR-120`, `F-MM-320`, `F-CE-110`, `F-CD-202`, each count 1) (`demo04a`).
- Content pipeline: Procedure `cd-12-procedure-cd-af-01.md` for `F-CD-101`, part `CD-AF-01`, 2-hour workshop duration, self-test verification; deterministic checks verified all 4 requirements present (`demo04b`).

### Frontier swarms and primary industry sources (`build/research-2026-10.md` section 5)

- **OpenAI Navier-Stokes swarm** (OpenAI, 8 September 2026, updated 10 September 2026, `openai.com/index/navier-stokes-solution`):
  - Group size: on the order of 10,000 concurrent agents in the winning group.
  - Runtime: solution found after roughly 88 hours (Saturday 5 September 2026).
  - Formalisation: Lean formalisation completed by GPT-6 Astra in 17 additional hours.
  - Message and token volume: 2.7 million messages and about 130 billion output tokens for Navier-Stokes alone; across all problems, 4.9 million messages and about 300 billion output tokens.
  - Outside cost estimate: swyx estimated roughly $40 million at public prices (Latent Space, 2 October 2026). This is an outside estimate, not OpenAI's reported bill.
  - Swarm efficiency quote: Alex Zhang statement on Latent Space (2 October 2026): "95% of the swarm is entirely useless", with his immediate hedge that the harness setup may not have mattered much in that setup.

- **Anthropic Fermat formalisation** (Anthropic, 4 September 2026, `anthropic.com/research/formalizing-fermats-last-theorem` ; ported from ARI510 module 10):
  - Scope: formalising an existing proof of Fermat's Last Theorem in Lean.
  - Horizon: 11 days of largely autonomous operation by dozens of parallel agents.
  - Proof scale: 30,300 theorems proved, 29,500 used in the final proof, 13 million lines of Lean.
  - Coordination and verification: shared dependency graph of theorems in external state; Lean's type checker as mechanical verification.

- **Personal crew and coding fleets** (`build/research-2026-10.md` section 5):
  - Yair (`@finebutwhy`): public post on X, quoted with permission granted 13 October 2026.
  - Fleet size: about 30 single-job Grok bots behind one first mate coordinator.
  - Exact quote on slide 10: "They all share one computer with the same browser logins, and nothing gets sent without my ok".
  - Open-source tools: `firstmate` (`github.com/kunchenguid/firstmate`, MIT, ~7.9K GitHub stars on 13 October 2026); `no-mistakes` (`github.com/kunchenguid/no-mistakes`, MIT, ~8.9K GitHub stars on 13 October 2026).

- **Capstone service desk** (`build/plan.md`):
  - Architecture pointer: comparison between Stage 3 (multi-agent graph with parallel diagnosis, judge, A2A manuals agent, approval inside subagent) and Stage 4 (Deep Agent with skills and subagents).
  - Aurelia dataset: 31 manuals and bulletins, `service.db`, 50 tickets, 25 eval cases.

## Slide metrics

- Slide count: 18 slides in `src/slides/10-real-world-applications/10-real-world-applications.md`.
- Lead-in share: 0% lone lead-ins (0 of 58 top-level bullets end in ` :` with exactly one sub-bullet; all lead-in bullets have two or more sub-bullets).
- Titles: all 18 titles are at most 40 characters; no `X: Y` titles except the standard closing `Summary : Real-World Applications`.
- Banned phrases and style: 0 bold in prose, 0 em-dashes, 0 analogies, 0 banned phrases.
- Demo pills: 6 pills in ascending order (`demo01 · research-agent`, `demo02 · customer-support`, `demo03 · code-review`, `demo04 · data-and-content`, `demo04b · content-pipeline`, `demo05 · firstmate`).
