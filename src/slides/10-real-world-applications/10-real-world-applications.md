---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Real-World Applications
---

# Research Automation

- Research agents turn open questions into sourced reports :
  - Plan sub-questions, retrieve evidence and combine findings
  - Keep notes and drafts in files as context grows
- `open_deep_research` is the reference implementation
- Parallel research workers receive bounded questions and separate source sets, as in module 05

> `demo01 · research-agent`

<!-- NOTES:
Timing : about 30 minutes for this module, including four demos and the trainer's firstmate demonstration. The estimate is for delivery, not measured. Source : LangChain open_deep_research, https://github.com/langchain-ai/open_deep-research ; Deep Agents research tutorial, https://docs.langchain.com/oss/python/deepagents/research.
The demo uses local manuals and tickets only. It follows the planning, research and synthesis shape at small scale.
-->

---

# Research Evidence

- Every report claim needs a traceable source :
  - Record the file or URL beside each finding
  - Report conflicting evidence and missing coverage
- Files hold research notes and drafts outside the conversation, as in module 08
- Provenance checks confirm retrieval ; human review verifies whether the source supports the claim

<!-- NOTES:
Source : LangChain open_deep_research, https://github.com/langchain-ai/open_deep-research. Skippable. The local demo checks file provenance in code, not entailment.
-->

---

# Customer Support

- A service agent routes, looks up policy and resolves or escalates a request :
  - Specialists hold distinct tools and authority
  - Irreversible actions pause for approval
- Handoffs carry the request between specialists, as in module 05
- Refunds, orders and account changes wait at approval gates from module 07

> `demo02 · customer-support`

<!-- NOTES:
Ported from ARI510 module 12's service-desk example, adapted to the Veenhaven Bus demo data. Handoffs refer to modules 05 and 06 : the speaker should distinguish the pattern from a simple router. Sources : https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs ; https://docs.langchain.com/oss/python/langgraph/interrupts ; build/measurements-10.md, demo02 ; build/measurements.md, handoff faults and fixes.
-->

---

# Handoffs in Support

- A handoff changes the active specialist and carries task state :
  - The next agent needs earlier tool results and the request
  - Parallel tool calls can leave an unanswered call after the transfer
- Shared state preserves the request and useful tool results across transfers, as in modules 05 and 06
- Evaluation checks complete answers and valid tool histories

<!-- NOTES:
Source : https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs ; build/measurements.md section "Handoffs : two faults in the documented example". The documented example can drop sibling tool results and earlier work. Module 05 demonstrates the measured faults and fixes.
-->

---

# Code Review

- Independent reviewers inspect different risks in the same change :
  - Reviewers evaluate correctness, database safety and concurrency in parallel
  - A judge resolves duplicate or conflicting findings
- Parallel review and a judge use the exploration pattern from module 05
- Evaluation from module 09 checks each reviewer and the combined findings for missed defects

> `demo03 · code-review`

<!-- NOTES:
Sources : build/measurements-10.md, demo03-code-review ; https://docs.langchain.com/oss/python/langgraph/workflows-agents. The notebook uses two focused review prompts, then a structured judge. The small checker only verifies required text and does not establish code safety.
-->

---

# Pipeline Checkers

- `no-mistakes` places a checker pipeline before changes reach `origin` :
  - Stages run review, test, documentation, lint, push, pull request and CI
  - Mechanical findings are fixed automatically ; unresolved issues escalate
- Defined pass conditions make the pipeline a maker-checker workflow from module 05
- Human approval controls consequential changes, as in module 07

<!-- NOTES:
Source : https://github.com/kunchenguid/no-mistakes, MIT-licensed project. The pipeline details come from the project description and the firsthand report recorded in build/research-2026-10.md section 5. This is a checker built from ordered steps, not a single model verdict.
-->

---

# Data Analysis

- An analytics agent turns a question into a query and an explanation :
  - Keep the SQL query, returned rows and explanation visible together
  - Restrict the database connection to read-only access
- A Deep Agent can use SQL tools and a configured execution sandbox from module 08
- Code checks compare reported figures with query results, using the checker pattern from module 05

> `demo04 · data-and-content`

<!-- NOTES:
Source : Deep Agents documentation, data analysis tutorial, https://docs.langchain.com/oss/python/deepagents. The demo pairs a read-only SQLite query with a bounded explanation prompt.
-->

---

# Content Pipelines

- A content pipeline transforms source material into reviewed output :
  - Retrieve the approved technical procedure
  - Draft and check required details before routing to editorial review
- Retrieval, drafting and validation form a fixed workflow from module 05
- Publication waits for human approval through an interrupt from module 07

> `demo04b · content-pipeline`

<!-- NOTES:
Sources : build/measurements-10.md, demo04b ; build/plan.md, module 10. The demo drafts an internal service bulletin from a local manual, then checks required details in code. These checks do not establish that every sentence is supported.
-->

---

# Coding Agent Fleets

- A fleet assigns separate coding tasks to isolated worktrees :
  - One orchestrator dispatches work and receives events
  - Each worker receives a brief, session and writable checkout
- Isolated subagents return findings to the orchestrator, as in modules 05 and 06
- Merge decisions use the human approval flow from module 07

> `demo05 · firstmate`

<!-- NOTES:
Source : firstmate, https://github.com/kunchenguid/firstmate ; Yair's public post is linked in build/research-2026-10.md section 5. The user authorized quotation on 13 October 2026. Trainer demonstration on Feiko's laptop, no notebook.
-->

---

# A Personal Crew

- Yair deployed about 30 single-job bots behind one first mate :
  - Specialists handle taxes, vehicle status, portfolio, inbox and app administration
  - One coordinator routes requests to the relevant bot
- "They all share one computer with the same browser logins, and nothing gets sent without my ok"
- Single-job workers have small tool sets behind one orchestrator, as in module 05
- Outbound actions wait for approval, as in module 07
- Shared logins motivate per-agent credentials and permissions from module 08

<!-- NOTES:
Source : Yair (@finebutwhy), public post on X, 2026 ; quoted with permission given 13 October 2026. build/research-2026-10.md section 5.
Single-job bots keep tool lists short (module 05). "Nothing gets sent without my ok" is an approval gate (module 07). Shared browser logins on one host illustrate the lethal trifecta across a fleet, motivating per-agent credentials and permissions (module 08).
-->

---

# Firstmate Patterns

| firstmate component | course pattern |
| --- | --- |
| first mate and crewmates | orchestrator with isolated subagents, module 05 |
| task worktree and session | context isolation and backend, module 08 |
| watcher and event files | event driven execution, module 06 |
| durable briefs and state | checkpointer and `Store`, modules 03 and 06 |
| merge escalation | interrupt and approval, module 07 |

- Files and processes provide the coordination and persistence covered in modules 05 to 08

<!-- NOTES:
Source : https://github.com/kunchenguid/firstmate ; mapping from build/research-2026-10.md section 5. Skippable. A firstmate fleet is a harness orchestration, not a LangGraph graph.
-->

---

# Harness or Graph

- A coding harness fits work tied to a repository and long-lived sessions :
  - Git worktrees, shell tools, watchers and persistent files form the runtime
  - The model interacts with existing files and developer tools directly
- A graph fits application-owned state and explicit transitions :
  - Typed schemas, state reducers and checkpointers define the boundaries
  - Conditional edges, loops and interrupt gates govern execution flow
- Both runtimes can coordinate isolated workers, as in modules 05 and 08
- Application requirements determine who owns state and execution

<!-- NOTES:
Sources : https://github.com/kunchenguid/firstmate ; https://docs.langchain.com/oss/python/deepagents. The comparison is an architectural fit, not a benchmark. Firstmate has event-driven local processes and worktrees ; LangGraph exposes application state and transitions. Either can call coding agents.
-->

---

# Swarms at the Frontier

- Large mathematical searches distribute variants across isolated groups :
  - Groups exchange messages internally to explore proof directions
  - A synthesiser consolidates useful findings across groups
- Separate proof and disproof groups use parallel exploration from module 05
- Cross-group synthesis shares selected findings, as in module 06

<!-- NOTES:
Sources : OpenAI, "On the Navier-Stokes Millennium Prize Problem," https://openai.com/index/navier-stokes-solution ; Anthropic, "Formalizing Fermat's Last Theorem," https://www.anthropic.com/research/formalizing-fermats-last-theorem. Both are primary reports. The two projects used different systems and tasks ; do not imply a direct comparison of capability.
-->

---

# Navier-Stokes Swarm

- OpenAI reports a coordinated search on an internal model :
  - Groups explored different problem variants and proof or disproof directions
  - The winning group had on the order of 10,000 concurrent agents
  - Codex consolidated findings ; the model was updated mid-run
- Lean formalisation checked the proposed proof after the search completed
- Parallel exploration and Lean verification combine worker and checker roles from module 05

<!-- NOTES:
Primary source : OpenAI, https://openai.com/index/navier-stokes-solution, published 8 September 2026 and updated 10 September. OpenAI reports the result, timeline, group structure and Lean formalisation. It does not claim the Clay prize. The page does not describe recursion or an RLM.
-->

---

# Fermat Formalisation

- Anthropic reports formalising an existing proof of Fermat's Last Theorem :
  - Dozens of parallel agents proved 30,300 theorems over 11 days
  - The final development used 29,500 proved theorems across 13 million lines of Lean
  - Lean's type checker rejected invalid proof steps mechanically
- A shared theorem dependency graph coordinates parallel work, as in modules 05 and 06

<!-- NOTES:
Primary source : build/research-2026-10.md section 5 and build/measurements-10.md ; Anthropic, "Formalizing Fermat's Last Theorem," https://www.anthropic.com/research/formalizing-fermats-last-theorem. The project formalised an existing proof ; it did not discover Fermat's theorem. Figures are Anthropic's report, not reproduced by this course. Ported and updated from ARI510 "Thirty Thousand Theorems" and "What the Fermat Project Shows".
-->

---

# Swarm Cost and Waste

- OpenAI reports about 130 billion output tokens for Navier-Stokes alone :
  - The reported run generated 2.7 million messages over roughly 88 hours
  - Codex consolidated findings across groups throughout the run
- swyx estimated about $40 million at public prices ; this is an outside estimate
- Alex Zhang stated, "95% of the swarm is entirely useless" :
  - He immediately hedged that the harness setup may not have mattered much in that run
  - The quote is his assessment, not a measured share of wasted tokens
- Single-agent baselines from modules 05 and 09 test whether added workers improve quality enough to justify their cost

<!-- NOTES:
Primary sources : OpenAI, https://openai.com/index/navier-stokes-solution ; Alex Zhang interview with swyx and Vibhu, https://latent.space/p/rlm, 2 October 2026. OpenAI reports 2.7 million messages and about 130 billion output tokens for Navier-Stokes. The roughly $40 million public-price estimate is swyx's, not OpenAI's reported bill. Zhang's exact line is "95% of the swarm is entirely useless"; immediately afterward he qualifies that the setup was different and says the harness "maybe ... doesn't matter that much." Preserve the hedge. The course did not reproduce either run.
-->

---

# The Capstone Desk

- The Aurelia service desk compares a graph with a Deep Agent on one service dataset :
  - Stage 3 implements parallel diagnosis, a judge, A2A communication and approval in a subagent
  - Stage 4 implements a Deep Agent with skills for procedures and specialists as subagents
- Modules 05 to 08 supply the graph patterns, skills and subagents used in both stages
- Modules 08 and 09 evaluate both stages on accuracy, token cost and lines of code

<!-- NOTES:
Source : build/plan.md capstone stages 3 and 4. The capstone data belongs to the exercises and is not used in module 10 demos. This slide points learners back to the comparison performed in modules 08 and 09.
-->

---

# Summary : Real-World Applications

- Research agents split questions, retrieve evidence and cite findings
- Support agents hand off task state and pause consequential actions
- Parallel reviewers need a judge ; deterministic checkers enforce requirements
- Analysis and content pipelines keep queries and sources reviewable
- Coding fleets use isolated workers, durable state and event-driven orchestration
- Lean and code checks make model output mechanically rejectable
- Evaluation compares quality and cost with a simpler baseline
