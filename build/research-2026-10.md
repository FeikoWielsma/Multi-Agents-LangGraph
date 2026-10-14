# What multi-agent with LangGraph looks like in October 2026

Survey for ARI520, done 13 October 2026. It builds on the ARI510 survey of
15 September and its currency audit of 18 September, in
`../Agentic-AI-LangChain/build/research-2026.md` and
`currency-audit-2026-09-18.md`. This file records what changed since then, and
what is specific to multi-agent work. `plan.md` holds the decisions.

Primary sources are LangChain's docs, blog and PyPI. Industry claims from
secondary sources are marked as such ; none of their numbers goes on a slide
without a primary source.

## 1. Is the course still relevant?

Yes, with a different emphasis from the published outline.

- **LangGraph is the runtime, not a fading framework.** LangChain's docs now
  describe three layers : LangGraph the runtime, LangChain the framework,
  Deep Agents the harness. `create_agent` and `create_deep_agent` both compile
  to LangGraph graphs and run on its checkpointer, interrupts and streaming.
  Anyone running LangChain agents in production is running LangGraph
- **Deep Agents is the headline, but not new.** The open-source `deepagents`
  harness dates from mid-2025 and is at 0.7.24. What is new in September and
  October 2026 is **Managed Deep Agents**, a hosted runtime in LangSmith, and a
  revamp of skills. Deep Agents' own multi-agent story is the subagent pattern,
  built on LangGraph
- **The prebuilt multi-agent packages are dead.** `langgraph-supervisor` and
  `langgraph-swarm` have had no release since November and December 2025. The
  docs teach five patterns built from primitives instead : subagents, handoffs,
  skills, router, custom workflow
- **The industry converged on one shape.** An orchestrator owns the context,
  spawns isolated workers, and receives summaries back. Peer-to-peer agent
  teams survive in narrow, instrumented niches. Multi-agent is a context
  engineering tool with a token bill, not a default architecture
- **The skill that sells is judgement.** When one agent with good tools
  suffices, when a subagent pays for its tokens, how to evaluate and observe a
  system of agents. Generic courses still teach crews and swarms

## 2. The stack, measured

PyPI on 13 October 2026, against the ARI510 freeze of 18 September :

| package | ARI510 pin | latest | released | releases since 18 Sep |
| --- | --- | --- | --- | --- |
| `langgraph` | 1.2.11 | 1.2.15 | 2026-10-12 | 4 |
| `langchain` | 1.4.0 | 1.4.5 | 2026-10-12 | 4 |
| `langchain-core` | 1.6.3 | 1.6.10 | 2026-10-12 | 7 |
| `deepagents` | 0.7.14 | 0.7.24 | 2026-10-12 | 9 |
| `langsmith` | 0.12.5 | 0.14.8 | 2026-10-13 | 10 |
| `langgraph-cli` | 0.4.31 | 0.4.33 | 2026-10-07 | 3 |
| `langgraph-api` | not pinned | 0.16.0 | 2026-10-10 | 44 |
| `langgraph-checkpoint-postgres` | not used | 3.1.3 | 2026-10-12 | 1 |
| `managed-deepagents` | not used | 0.9.1 | 2026-10-13 | 99 |
| `a2a-sdk` | not used | 1.2.2 | 2026-10-05 | 6 |
| `langgraph-supervisor` | history | 0.0.31 | 2025-11-19 | 0 |
| `langgraph-swarm` | history | 0.1.0 | 2025-12-04 | 0 |

Neighbouring frameworks, for the landscape slide : `crewai` 1.15.27,
`openai-agents` 0.23.1, `google-adk` 2.12.0, `agent-framework` (Microsoft)
1.21.0, `pydantic-ai` 2.55.0, `claude-agent-sdk` 0.2.165. `autogen-agentchat`
has had no release since September 2025 ; Microsoft Agent Framework replaced it.

Nothing is probed against the course endpoint yet. The minor versions did not
move, so the ARI510 code should carry over ; verify before freezing.

## 3. What changed since 18 September

**Managed Deep Agents v0.8, 24 September, and v0.9, 7 October.** A hosted
runtime in LangSmith for the open-source harness, in public beta since August.
An agent is a folder : `AGENTS.md` or `instructions.md`, `skills/`,
`subagents/`, `tools.json`. `define_deep_agent(name, model, tools)` in
`agent.py`, then `mda dev` for a local Agent Server and Studio, `mda deploy` to
LangSmith. v0.8 added user-level memory, user-owned credentials, Slack file
transfer, an HTTP webhook channel and built-in web search. v0.9 added schedules,
per-run configuration and Slack reactions. The SDK is not open source during
the beta, and the service runs on US LangSmith Cloud.

**Revamping Skills in Deep Agents, 7 October.** Tools bound to a skill through
`metadata.include_tools` in `SKILL.md`, invisible until the skill is read ;
label resolvers that filter tools per user ; `pinned_skills` on `invoke` ;
mid-thread reload by resetting `skills_metadata`. Relevant to the skills
pattern : it is now a way to scope tools as well as prompts.

**LangSmith, 24 and 25 September.** Trajectories : one chronological view of a
session across the main agent and its subagents, scorable by online
evaluators. Engine v2 : red teaming and automated fix testing on deployed
agents. Fine-tuning of open models from trajectories. Custom Apps.

**Deep Agents subagents.** `mode: "fork"` passes the parent's history to a
subagent instead of only the task description, beta from 0.7.13. Dynamic
subagents dispatch from code through `CodeInterpreterMiddleware`, beta.

**LangGraph.** Patch releases 1.2.12 to 1.2.15 only. The 1.2 features remain
the ones to teach : node `timeout`, `error_handler` returning a `Command`,
graceful drain, `DeltaChannel`, v3 event streaming.

**Agent Server A2A.** Every assistant on Agent Server exposes `/a2a/{assistant_id}`
and an agent card at `/.well-known/agent-card.json?assistant_id=...`. It speaks
the A2A v1.0 JSON-RPC binding : send, stream, get, cancel and list tasks. The
`contextId` maps to a LangSmith thread, so traces across agents group together.
Requires a `messages` key in state. `langgraph dev` serves it locally.

## 4. How LangChain teaches multi-agent

From `docs.langchain.com/oss/python/langchain/multi-agent`, read 13 October.

The docs open with a warning : a single agent with the right, sometimes
dynamic, tools and prompt can often achieve similar results. Three reasons to
go multi-agent : too many tools for one agent to choose well, specialised
knowledge with long prompts, and sequential constraints that unlock
capabilities. Three motivations : context management, distributed development,
parallelisation. "At the center of multi-agent design is context engineering."

| pattern | how it works |
| --- | --- |
| Subagents | a main agent calls agents as tools ; all routing passes through it |
| Handoffs | a tool call updates state, which changes the active agent or its prompt and tools |
| Skills | one agent loads specialised prompts and knowledge on demand |
| Router | a step classifies the input, dispatches to one or more agents, synthesises |
| Custom workflow | a LangGraph graph mixing deterministic steps and agents ; embeds the others |

The docs' own measurements, which a slide may quote as theirs :

| pattern | one-shot calls | repeat request, turn 2 | three domains, calls and tokens |
| --- | --- | --- | --- |
| Subagents | 4 | 4 | 5, about 9K |
| Handoffs | 3 | 2 | 7 or more, about 14K or more |
| Skills | 3 | 2 | 3, about 15K |
| Router | 3 | 3 | 5, about 9K |

Stateful patterns save 40 to 50 percent of calls on repeat requests ; parallel
patterns win on multi-domain work ; skills use fewest calls but most tokens.

The website outline's vocabulary maps onto these :

| outline term | 2026 equivalent |
| --- | --- |
| Supervisor, manager-worker | subagents ; a main agent with agents as tools |
| Hierarchical | subagents whose subagents are graphs ; nested subgraphs |
| Sequential, parallel | custom workflow ; `Send` fan-out ; router |
| Collaborative | handoffs ; maker-checker ; debate with a judge |
| Specialized agents | subagents or skills, chosen by whether context must be isolated |
| Message passing, shared state | subgraph state mapping ; `Command(graph=Command.PARENT)` ; tool results |
| Handoffs | handoff tools returning `Command` ; the active agent kept in state |
| Communication protocols | A2A between servers ; Agent Protocol for async subagents ; MCP for tools |
| Event systems, broadcasting | v3 event streaming with subgraph projections ; custom stream events |
| Conflict resolution | reducers for concurrent writes ; voting ; a judge |
| Synchronization | fan-in edges ; deferred nodes ; async task check and cancel |

**Deep Agents subagent types**, from the subagents and async subagents pages :

- Synchronous, the default : dicts with `name`, `description`, `system_prompt`,
  `tools`, optional `model`, called through the `task` tool
- `CompiledSubAgent` : any LangGraph graph with a `messages` key, including a
  `create_agent` agent or a custom workflow
- Asynchronous : `AsyncSubAgent` against any Agent Protocol server, co-deployed
  over ASGI or remote over HTTP. Tools `start_async_task`, `check_async_task`,
  `update_async_task`, `cancel_async_task`, `list_async_tasks`. Locally needs
  `langgraph dev --n-jobs-per-worker 10` or similar
- Dynamic : fan-out written as code in a QuickJS interpreter, beta
- Context : `isolated` by default, `fork` in beta

## 5. What the industry says

Primary sources :

- **Anthropic, "How we built our multi-agent research system", June 2025.** A
  lead agent spawning parallel subagents beat a single agent by 90.2 percent on
  their internal research evaluation. Multi-agent runs used about 15 times the
  tokens of a chat, single agents about 4 times. Token use explained most of
  the variance in performance. The canonical case for, and against
- **Cognition, "Don't Build Multi-Agents", June 2025.** Share full context,
  and actions carry implicit decisions ; parallel agents with partial context
  make conflicting decisions. The canonical case against peer agents
- **LangChain, State of Agent Engineering**, survey of over 1,300 people in late
  2025 : 57 percent have agents in production, quality is the top barrier at
  32 percent, observability at 89 percent far ahead of evals at 52 percent.
  Supports a module on evaluating multi-agent systems
- **LangChain docs**, section 4 : start single, measure, add agents for context

- **Recursive language models**, Zhang, Kraska and Khattab, MIT CSAIL,
  `arxiv.org/abs/2512.24601`, v1 31 December 2025, v3 11 May 2026. A long
  prompt becomes an environment the model inspects in code, calling itself on
  the pieces. Handles inputs about two orders of magnitude beyond the context
  window ; with GPT-5, a median gain of 26 percent over compaction, 130 percent
  over CodeAct with sub-calls and 13 percent over Claude Code, at comparable
  cost. Deep Agents' dynamic subagents implement the idea
- **Prime Intellect, "Recursive Language Models : the paradigm of 2026"**,
  1 January 2026, `primeintellect.ai/blog/rlm`. The same RLM, credited to Alex
  Zhang, implemented as `RLMEnv` in their `verifiers` library. The root model
  sees the prompt ; the bulk input lives only in a Python REPL. It calls fresh
  sub-LLMs from code, in parallel through `llm_batch`, and only sub-LLMs get
  tools, so their verbose output never reaches the root. The answer is a Python
  variable, not a message. Depth 1 for now. It folds context without
  summarising it, so nothing is lost to compaction. With GPT-5-mini it raised
  reward on most environments and won clearly on long-context Oolong up to
  about 1.5 million characters ; it lost on math-python, and needed a strategy
  hint to win on DeepDive. Training on long-horizon environments is planned
- **Latent Space, "Recursive Language Models", Alex Zhang with swyx and
  Vibhu, 2 October 2026**, `latent.space/p/rlm`, transcript on the page. Zhang :
  an RLM is a harness whose only tool is code ; the model calls itself as a
  subagent and keeps its context in the code environment. Claude Code, Codex and
  Pi are one loop, "trajectory as a prompt" ; an RLM orchestrates through code
  and subagents instead. Trained RLMs generalise to tasks 8 to 30 times longer,
  because every sub-call stays locally in distribution. On swarms : "95% of the
  swarm is entirely useless", and the harness may not have mattered much for
  OpenAI's run ; swyx puts that run at about $40 million at public prices, his
  estimate. A coordinator-heavy org chart, as Cursor described, bottlenecks.
  Advice : state in files, persistent and inspectable subagents, orchestration
  in code, compare against plain compaction on cost and speed, and let domain
  insight replace brute-force search. Check every quote against the transcript
  before it goes on a slide
- **The slide in 08** : an RLM is context isolation done in code. The root
  model is a supervisor whose subagents are calls in a loop ; the same shape as
  Deep Agents' dynamic subagents, where the interpreter calls `task()`. Zhang's
  two families of harness, trajectory as prompt against orchestration in code,
  frame the slide. Its limits are the course's thesis again : it helped on long inputs and not on
  math, and it needed telling how to split the work
- **OpenAI, "On the Navier–Stokes Millennium Prize Problem"**, 8 September
  2026, `openai.com/index/navier-stokes-solution`, updated 10 September. A
  system of coordinating agents on an internal model "significantly more capable
  than GPT-6 Astra", with a cached web and code execution. Agents work in groups
  of varying size and message only within their group ; the winning group had
  on the order of 10,000 concurrent agents. Separate groups got different
  variants of the problem, the proof versions and the disproof versions. After
  an Euler result from nearly 100 agents in about 50 hours, agents were moved
  from the other problems to Navier-Stokes and prompted with it. Codex
  periodically consolidated the most useful insights of each group into
  follow-up prompts : cross-pollination. The model was swapped for a further
  trained version mid-run. Solution after about 88 hours, Saturday 5 September ;
  Lean formalisation by GPT-6 Astra in 17 more hours. Navier-Stokes alone : 2.7
  million messages, about 130 billion output tokens ; all problems : 4.9
  million and about 300 billion. The claim : finite-time blowup from a smooth
  fluid at rest under a smooth force with finite energy, statements C and D of
  the Clay formulation. OpenAI does not claim the prize. Priority on forced
  Euler goes to Alpöge and Buckmaster ; OpenAI's investigation found
  Buckmaster's Codex prompts could not have influenced the result. Quanta
  reports Bubeck's estimate of several million dollars and mathematicians'
  scepticism. The page describes no recursion and no RLM ; do not link the two
- **OpenAI, "Sharing AI progress in mathematics"**, `openai.com/index/sharing-ai-progress-in-mathematics`.
  A GitHub release of further results with Lean formalisations, following the
  IAS advisory group's guidance ; the average result took about three hours
  of ChatGPT Pro thinking. Background only

What the swarm shows, one slide in 10 and a callback in 05 and 06 :

| in the swarm | in the course |
| --- | --- |
| groups that message only internally | scoped communication ; hierarchical teams |
| proof and disproof variants to separate groups | parallel exploration ; adversarial verification |
| Codex consolidating insights across groups | a synthesiser over map-reduce ; summaries, not transcripts |
| agents moved to the promising problem | an orchestrator reallocating work ; humans steering |
| model upgraded mid-run | durable execution ; state outlives the model |
| Lean checks the proof | a checker written in code, at the top of maker-checker |
| 130 billion output tokens | the token bill, at the far end of the scale |

Secondary, not yet checked against the original :

- Cognition's "Devin can now manage Devins", reported March 2026 : a
  coordinator assigns work to Devins in isolated VMs. Read by commentators as
  Cognition adopting the orchestrator shape, not peer agents
- Anthropic's harness posts on long-running agents, November 2025 to March
  2026. Harness design as the lever for long runs ; matches Deep Agents' pitch
- Claude Code : subagents report only to the orchestrator ; Agent Teams, which
  message each other, are experimental and off by default
- Several 2026 papers find single agents as good or better at equal token
  budget on reasoning tasks, and multi-agent ahead on parallel, breadth-first
  work. Cite a paper only after reading it
- Framework popularity : figures between 15 and 41 percent "market share" for
  LangGraph circulate with no methodology. Do not use them. PyPI downloads are
  the only comparable number, and only as an order of magnitude

**`firstmate`**, `github.com/kunchenguid/firstmate`, MIT, about 7.9K stars on
13 October 2026. An "agent distro" : instructions, skills, scripts and state
conventions that a coding harness follows ; Claude Code, Codex, Pi, OpenCode and
others. The user talks to one first mate, which dispatches each task to a
crewmate in its own git worktree and tmux session, ship or scout. A bash
watcher wakes the first mate only on events ; state lives on disk ; only real
decisions such as merges are escalated. The orchestrator shape built from
processes and files instead of a graph, and used in practice by people Feiko
knows. Its concepts map onto the course :

| `firstmate` | ARI520 |
| --- | --- |
| first mate, crewmates | subagents ; orchestrator with isolated workers |
| one worktree and session per task | context isolation ; sandboxes and backends |
| dispatch, watch, type into a session | async subagents : start, check, steer, cancel |
| watcher that wakes on events | event systems ; no polling by the model |
| backlog, briefs, state files | checkpointer and `Store` ; durable execution |
| escalate real decisions, approve merges | interrupts and approval flows |
| secondmates on other hosts | remote subagents over Agent Protocol or A2A |
| instructions and skills in a repo | `AGENTS.md`, skills ; Managed Deep Agents' folder shape |

Two uses seen in practice :

- **A personal crew.** Yair, `@finebutwhy`, in a public post : about 30 Grok
  bots, each with a single job, behind one first mate he talks to. An
  accountant for Dutch books and taxes with bunq, a Tesla bot, a portfolio
  advisor, an inbox bot over Gmail and Outlook, Home Assistant, the admin of
  his app goldmary.eu, a seller and a buyer side by side, "a conflict of
  interest i've chosen to ignore". "They all share one computer with the same
  browser logins, and nothing gets sent without my ok"
- **A coding fleet.** The same person, Feiko's friend, in a Discord message
  of 26 September 2026 : he builds goldmary.eu with `firstmate` plus `no-mistakes`
  (`github.com/kunchenguid/no-mistakes`, MIT, about 8.9K stars) : a local git
  remote that runs review, test, docs, lint, push, PR and CI before anything
  reaches `origin`, fixes the mechanical findings and escalates the rest.
  A maker-checker where the checker is a pipeline

Yair gave permission on 13 October 2026 to quote both and show the crew
diagram. Cite the public post on slides

What the crew post teaches, each point a slide :

- Single-job agents are the docs' first reason for multi-agent : too many
  tools for one agent. Thirty bots with a few tools each, not one with a hundred
- One point of contact : the subagents pattern, not handoffs
- "Nothing gets sent without my ok" is the only control, and it is an
  approval gate on outbound actions : module 07
- One computer, shared logins : every bot holds every credential. The inbox
  reads untrusted mail, the accountant sees the bank, the browser can send.
  The lethal trifecta across a whole fleet, and the case for per-agent
  credentials, skill-bound tools and permissions
- The seller and the buyer : two agents of one principal with opposing goals.
  The outline's conflict resolution, made concrete

What follows for the course :

- Teach the orchestrator with isolated subagents as the default shape, and
  peer collaboration as the exception that needs justification
- Measure tokens and calls per pattern on the course model, and show them.
  The 15 times figure is the reason the student should care
- Context engineering is the thread through every pattern : what each agent sees

**Anthropic, Fermat's Last Theorem in Lean**, 4 September 2026,
`anthropic.com/research/formalizing-fermats-last-theorem`. Carried over from ARI510
module 10 ("Thirty Thousand Theorems"). An internal research model formalised an
existing proof in eleven days of largely autonomous work : 30,300 theorems proved,
29,500 used in the final proof, 13 million lines of Lean, dozens of agents in
parallel. Lean's type checker is the verifier. Module 10 sets it beside the
Navier-Stokes swarm.

## 6. Competing courses

| course | provider | shape | multi-agent content |
| --- | --- | --- | --- |
| Introduction to LangGraph | LangChain Academy | free, self-paced | parallelisation, subgraphs, map-reduce, research assistant |
| Introduction to Deep Agents | LangChain Academy | free, self-paced | subagents, dynamic subagents, sales-assistant capstone |
| Deep Research with LangGraph | LangChain Academy | free, project | scoping, research agent, supervisor, multi-agent system |
| Agentic AI with LangChain and LangGraph | DeepLearning.AI on Coursera | 3 weeks | collaborative multi-agent orchestration |
| Multi-Agent Systems with LangGraph | Edureka on Coursera | about 10 hours, updated Feb 2026 | supervision, consensus reasoning |
| Complete Agentic AI Bootcamp | Udemy | self-paced, updated June 2026 | collaboration, shared goals |

No instructor-led three-day LangGraph multi-agent course turned up in the
search. The Dutch providers from the ARI510 survey sell LangChain courses with
multi-agent as one line. ARI520's selling points : in person, current APIs, the
docs' patterns built by hand, evaluation and deployment of a multi-agent system,
measured costs.

## 7. Consequences for ARI520

- Module names stay as published ; the content is the five patterns, the
  Deep Agents subagent types and A2A, built on LangGraph primitives
- Each outline term in the table in section 4 gets a slide, framed by its 2026
  equivalent. Supervisor and swarm packages get one slide as history
- Deep Agents is taught as a harness that implements the subagent pattern,
  after the student has built that pattern by hand. Managed Deep Agents gets
  one slide and no lab : US cloud, beta, closed SDK
- Agent communication across processes is A2A on Agent Server, run locally
  with `langgraph dev`. Two local servers talking is a feasible lab
- Evaluation and observability of multi-agent runs get real time : trajectory
  evals per agent and for the whole, cost per pattern, LangSmith Trajectories
- Upgrade the stack to the October releases and freeze a week before delivery

## Sources

- [SpiralTrain, Multi Agents with LangGraph](https://www.spiraltrain.nl/multi-agents-with-langgraph/?lang=en)
- [LangChain docs, Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent/index)
- [LangChain docs, Frameworks, runtimes and harnesses](https://docs.langchain.com/oss/python/concepts/products)
- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview), [subagents](https://docs.langchain.com/oss/python/deepagents/subagents), [async subagents](https://docs.langchain.com/oss/python/deepagents/async-subagents)
- [Agent Server A2A endpoint](https://docs.langchain.com/langsmith/server-a2a)
- [LangChain changelog](https://docs.langchain.com/oss/python/releases/changelog)
- [LangChain blog index](https://www.langchain.com/blog), read 13 October 2026
- [Introducing Managed Deep Agents](https://www.langchain.com/blog/introducing-managed-deep-agents), [public beta](https://www.langchain.com/blog/managed-deep-agents-is-now-in-public-beta), [quickstart](https://docs.langchain.com/langsmith/python/managed-deep-agents-quickstart), [CLI](https://docs.langchain.com/langsmith/python/managed-deep-agents-cli)
- [New in LangSmith : Engine v2, Managed Deep Agents, Fine-Tuning](https://www.langchain.com/blog/langsmith-engine-agents-fine-tuning-trajectories), 25 September 2026
- [Revamping Skills in Deep Agents](https://www.langchain.com/blog/revamping-skills-in-deep-agents), 7 October 2026
- [LangChain, State of Agent Engineering](https://langchain.com/state-of-agent-engineering)
- [Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Cognition, Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
- [Linux Foundation, A2A one-year announcement](https://linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year)
- Secondary : [FlowHunt, Multi-agent AI systems in 2026](https://www.flowhunt.io/blog/multi-agent-ai-system/), [Micheal Lanham, Multi-agent in production in 2026](https://medium.com/@Micheal-Lanham/multi-agent-in-production-in-2026-what-actually-survived-f86de8bb1cd1), [Tembo, Claude Code multi-agent orchestration](https://www.tembo.io/blog/claude-code-multi-agent-orchestration)
- Courses : [LangChain Academy](https://academy.langchain.com/collections), [Coursera, Agentic AI with LangChain and LangGraph](https://coursera.org/learn/agentic-ai-with-langchain-and-langgraph), [Coursera, Multi-Agent Systems with LangGraph](https://coursera.org/learn/multi-agent-systems-with-langgraph), [Udemy, Complete Agentic AI Bootcamp](https://www.udemy.com/course/complete-agentic-ai-bootcamp-with-langgraph-and-langchain/)
- PyPI JSON API for every version in section 2, queried 13 October 2026
