# Plan : ARI520 Multi Agents with LangGraph

Three-day course, delivered Monday 2 to Wednesday 4 November 2026. Draft written
Tuesday 13 October 2026, after the survey in `research-2026-10.md`, and revised
the same day with Feiko's answers. Status : built 14 October ; see "Status" at the end.

Advertised at `spiraltrain.nl/multi-agents-with-langgraph` : 9 modules, for AI
engineers, developers and data scientists with Python and a grasp of LLMs and
agents. LangChain, graph theory and async are listed as helpful, not required.

## Why this course exists now

One participant from Philips booked ARI510 Agentic AI with LangChain for
September. It moved to 2 to 4 November, and the participant now wants ARI520
instead. Their background is still unknown. ARI510 is built, executed and
published ; ARI520 reuses its LangGraph and multi-agent material, its capstone
data and its tooling, and adds what a multi-agent course needs on top.

## The published outline is not a spec

As with ARI510, the outline predates the current APIs. Module names stay ; the
content is LangGraph 1.2, the five documented patterns, Deep Agents and A2A. The
table in `research-2026-10.md` section 4 maps each outline term to its 2026
equivalent, and each gets a slide under that heading. One module is added :
Deep Agents, a full day, which the outline predates.

## The thesis

Three ideas carry the course from the first hour to the capstone :

- **Multi-agent is context engineering.** A second agent exists to give a
  task its own context. Every pattern answers one question : what does each
  agent see ?
- **One agent first.** Add an agent when a measurement says so. Every pattern
  demo prints calls, tokens and time on the course model
- **Build it by hand, then use the harness.** Days 1 and 2 build every pattern
  from LangGraph primitives. Day 3 rebuilds the same system as a Deep Agent and
  compares the two on cost, quality and code

## Decisions

| | |
| --- | --- |
| Code | ARI520. PDFs `ARI520-Multi-Agents-LangGraph.pdf` and `ARI520-Multi-Agents-LangGraph-Exercises.pdf` |
| Repository | `C:\Git\courseWare\Multi-Agents-LangGraph`. Forgejo `SpiralTrain/Multi-Agents-LangGraph` and a GitHub student subset, as ARI510 |
| Participant | Same as ARI510, background unknown. Build for a developer, refresher in module 04, pivots as ARI510 |
| Outline | Module names kept, content current, Deep Agents added as module 08 |
| Deck | New Marp deck. Ported from ARI510 modules 04, 08, 10, 11 and 12 where the material exists |
| Volume | More than three days need, with skip marks in the speaker notes, as ARI510. About 290 slides and 68 demo notebooks with about 145 sections, one section for almost every other slide. Numbered per module : `notebooks/NN-module/demoNN-slug.ipynb` ; later sections pill as `demoNNb` |
| Deep Agents | A full day, day 3 : the harness, then deploying and applying it |
| Managed Deep Agents | One slide, and a trainer demo only if the account allows. US cloud, beta, closed SDK |
| A2A | Two local Agent Servers talking over A2A, as a lab |
| Evaluation | Real time : trajectory evals per agent and for the system, cost per pattern |
| Model | GPT-6 Luna through OpenRouter, reasoning off ; MiMo-V2.6-Pro as fallback. Measured 13 October |
| Labs | `uv` on the classroom laptop, Colab as backup, as ARI510 |
| Exercises | Written guide plus skeleton notebook with blanks and hints, as ARI510 |
| Capstone | Guided, staged build on ARI510's Aurelia Imaging Systems data. Demos stay on Veenhaven Bus |

## The model

The Qwen token plan ARI510 used is not active. No DeepSeek key is in BWS.

**OpenRouter**, one key, OpenAI-compatible, reached through `ChatOpenAI` with a
`base_url` as ARI510's setup cell already does. A separate key with a credit
limit goes to the participant. Candidates, priced on 13 October 2026 from
OpenRouter and aggregators, to be confirmed on the provider pages :

| model | role | AA index, cost per task at max effort | on OpenRouter |
| --- | --- | --- | --- |
| `openai/gpt-6-luna` | course model | about 38, about $0.065 | tools, `response_format`, `reasoning_effort` ; $0.10 / $0.50 per 1M |
| `xiaomi/mimo-v2.6-pro` | step up if Luna fails | about 46, about $0.13 | tools, `response_format`, `reasoning`, `temperature` |
| `openai/gpt-6.1-sol` | orchestrator fallback | about 52, about $0.75 | not checked |
| `deepseek/deepseek-v4.1-flash` | dropped | about 39, about $0.27 | dominated : Luna's score at four times the cost |

Index and cost read off Feiko's screenshot of the Artificial Analysis
intelligence-against-cost chart, 13 October 2026 ; cost per task there is at
maximum reasoning effort, which the labs will not use. The index measures
general intelligence, not tool-call reliability over long agent loops.

**Decided 13 October : GPT-6 Luna, reasoning effort `none`.** Measured in
`measurements.md` : both models answered 20 of 21 pattern runs correctly with no
malformed tool call, but MiMo was three to ten times slower and read more
tokens. MiMo stays as the fallback ; no second model for orchestrators. Both
full probes cost $0.0225 together, so cost is not a constraint.

**Rate limit.** OpenRouter caps new accounts at 20 requests a minute per model.
The setup cell shares one `InMemoryRateLimiter` across every model instance,
0.3 requests a second by default, `COURSE_RPS` to change it. Recheck the cap the
week before delivery ; a parallel fan-out at 0.3 a second is slow to watch.

**ChatGPT Plus through Sign in with ChatGPT : no.** The plan-usage preview
reaches only the Responses API with `stream: true` and `store: false`, rejects
`temperature`, `max_output_tokens` and system-role messages, needs an OAuth
client per user and host, and shares the Plus five-hour limit across apps. Paid
or hosted apps go through an interest form. LangChain's `ChatOpenAI` sends
several of the rejected fields, and a student would spend the trainer's plan.
Sources : `developers.openai.com/siwc`, its preview limitations page.

## The stack

Start from the ARI510 pins, upgrade to the October releases, probe, then freeze
with `exclude-newer` about a week before delivery :

```
python 3.12
langchain[mcp] 1.4.5   langchain-core 1.6.10   langgraph 1.2.15
deepagents 0.7.24      langsmith 0.14.8        langgraph-cli[inmem] 0.4.33
langgraph-checkpoint-sqlite   langgraph-checkpoint-postgres (slide only)
a2a-sdk 1.2.2, only if the A2A lab needs a client beyond httpx
```

Measure before building on it :

- Every ARI510 demo from modules 08 and 10 on the upgraded stack and the new model
- The five patterns and a Deep Agent with subagents on both candidate models
- `langgraph dev` serving two graphs, an A2A call between two servers, and
  async subagents with `--n-jobs-per-worker`
- Whether `langgraph dev` needs a LangSmith key, as in ARI510

## The course

Eleven modules including the preamble. `port` names the ARI510 source ; `new`
means written for ARI520. Slide counts are targets.

### 00 Preamble

Port. Course remarks, lab setup, the three-day map, the stack.

### 01 Introduction to LangGraph : ~20 slides

Website module 1. Opens with the frontier, written 13 October : seven
slides, about 20 minutes, as the hook. Yair's crew of thirty agents, OpenAI's
Navier-Stokes swarm and how it was organised, Anthropic's research system,
recursive language models, the bill for a swarm with our own measurements, and
a table mapping every example to the module that teaches its pattern. Module 10
returns to each in depth.

- What is LangGraph ? Runtime, framework, harness : new, from the docs page
- How LangGraph differs from other frameworks : port ARI510 01 frameworks slide, reworked. CrewAI, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework, Claude Agent SDK, Pydantic AI
- Agents versus workflows : port
- Graph-based architecture, state graphs, nodes, edges, conditional routing : port ARI510 08 opening, overview level
- Why multi-agent ? Context, specialisation, parallelism, distributed development : new
- When one agent is enough : new. The docs' warning, Cognition, the token bill
- What survived in 2026 : new. Orchestrator with isolated workers ; research section 5. `firstmate` as the example from practice
- The course case : the capstone scenario introduced

Demo : a single agent hitting its limits on the capstone data, measured.

### 02 Graph Fundamentals : ~26 slides

Website module 2. Mostly port of ARI510 08.

- Graph theory basics : new, short. Directed graphs, cycles, DAG versus cyclic, fan-out and fan-in
- State machines : new. A graph as a state machine with an LLM in some transitions
- `StateGraph`, nodes, edges, `START`, `END`, entry points : port
- Conditional edges, routing functions, `path_map` : port
- Cycles, loops and the recursion limit : port
- `Command` : new. Update and route from inside a node
- `Send` and map-reduce : port
- Deferred nodes : new. Waiting for all branches
- Compiling and visualising, Mermaid : port
- Graph API or Functional API : port

Exercise : ARI510 `exercise12 · Graphs and Loops`, port.

### 03 State Management : ~26 slides

Website module 3.

- State schemas : `TypedDict`, dataclass, Pydantic ; input, output and private schemas : port plus new
- Reducers, `add_messages`, custom reducers, overwriting a reduced key : port plus new
- Concurrent updates and `InvalidUpdateError` : new. Why parallel agents need reducers
- Persistence and checkpointing : port. `InMemorySaver`, `SqliteSaver`, Postgres on a slide
- Threads, `get_state`, `get_state_history` : port
- Restoration, time travel, forking : port
- `DeltaChannel` for long threads : new, one slide
- The `Store`, cross-thread memory : port ARI510 07, short
- Debugging state : new. `stream_mode="debug"`, v3 projections, Studio

Exercise : new, state for a two-agent pipeline with a reducer conflict to fix.

### 04 Building Agents : ~28 slides

Website module 4. Assumes no LangChain ; the refresher is folded in.

- Tool-calling agents and the ReAct pattern, written as a graph : port ARI510 08
- `ToolNode`, `tools_condition` : port
- `create_agent` : port ARI510 04. Compiles to a graph ; usable as a node
- Custom agent logic : new. Agent nodes with their own state and prompts
- Middleware for agents : port ARI510 04, short
- Error handling : port plus new. `RetryPolicy`, node `timeout`, `error_handler`, `ToolErrorMiddleware`, `ModelFallbackMiddleware`
- Monitoring : port. LangSmith tracing, a logging middleware
- Testing : port ARI510 11. `GenericFakeChatModel`, scripted tool calls, `InMemorySaver`
- Best practices : new

Exercises : ARI510 middleware exercise adapted, plus a unit test.

### 05 Multi-Agent Patterns : ~32 slides

Website module 5. The core of the course. Port of ARI510 10, extended.

- Choosing a pattern : port. The docs' matrix and their call counts
- Subagents, the supervisor : port. A main agent with agents as tools
- Manager-worker and hierarchical teams : new. Subagents whose workers are subgraphs ; two levels
- Router and parallel dispatch : port
- Handoffs : port
- Skills : port
- Custom workflow : port. Sequential pipeline as a graph
- Parallel agents and map-reduce : port
- Collaborative agents : new. Maker-checker, debate with a judge
- Specialised agents : new. Subagent or skill ? Decided by context isolation
- Orchestration : new. Deterministic code around agentic steps
- Supervisor and swarm packages : port, one slide, history
- Cost of each pattern, measured : new

Demos : each pattern by hand on the bus data, with a measurement table.
Exercise : port and rework ARI510 `exercise17 · A Multi-Agent Visit Planner`.

### 06 Agent Communication : ~26 slides

Website module 6. Mostly new.

- Message passing against shared state : new
- What each agent sees : new. Full history, task only, fork, summary back
- Handoffs between graphs : new. `Command(goto=..., graph=Command.PARENT)`
- Subgraph state mapping : port plus new. Shared keys, transformed input and output
- Communication protocols : new. Tool calls in process ; Agent Protocol ; A2A ; MCP for tools, not agents
- A2A in depth : new. Agent cards, tasks, `contextId`, the Agent Server endpoint
- Event systems : new. Subgraph streaming, v3 projections, custom events with the stream writer
- State broadcasting : new. A shared channel every agent reads
- Conflict resolution : port plus new. Reducers, voting, a judge, a tie-break rule. Opens on the seller and buyer bots from the crew post, research section 5
- Least privilege across agents : new. One shared login is the trifecta for the whole fleet ; per-agent credentials, skill-bound tools
- Synchronisation : new. Fan-in, deferred nodes, barriers

Exercises : new, two agents on two local servers talking over A2A ; new, a
conflict on the bus data : a disposal agent selling surplus depot stock and a
procurement agent buying, with a policy node or judge that settles it.

### 07 Advanced Workflows : ~22 slides

Website module 7. The Deep Agents parts moved to 08.

- Human-in-the-loop : port. `interrupt`, `Command(resume=...)`
- Interrupts inside subagents and subgraphs : new
- Approval flows : port. Approve, edit, reject ; `HumanInTheLoopMiddleware`
- Conditional branching at scale : new
- Loop detection : new. Recursion limit, call limits, repeated tool calls, a watchdog node
- Retry and fallback strategies : port plus new
- Subgraphs and workflow composition : port plus new
- Durable execution : port. Graceful drain, resuming after a crash

Exercise : port ARI510 `exercise13 · Human Approval`, reworked into a subagent.

### 08 Deep Agents : ~36 slides

New module, a morning. Inspiration : `deep-agents-from-scratch`, the Academy's
Introduction to Deep Agents, the Deep Agents docs.

The Academy course maps almost one to one onto 08 and part of 09 : building
(module 1), execution environment (2), context management (3), delegation (4),
local deployment and async subagents (5), Managed Deep Agents (6). Its repo
`langchain-ai/lca-deepagents` has no licence, so it is all rights reserved :
take its order and ideas, not its text or code. Code comes from the MIT repos,
`deepagents`, `docs` and `deep-agents-from-scratch`, with attribution, or is
written for the course. It pins `deepagents` 0.7.0 and `langchain-mcp-adapters`,
behind this course's stack. The course is free : point the participant at it as
the follow-up, in the summary of 08.

- What is an agent harness ? Framework, runtime, harness again : new
- Deep Agents from scratch : port ARI510 demo29. `create_agent`, then a todo list, then files, then subagents
- `create_deep_agent` : port. Defaults in 0.7 : lean prompts, planning opt-in
- Planning with `write_todos` : port
- The virtual filesystem and context offloading : port plus new
- Backends : port. State, filesystem, store, composite
- Sandboxes and interpreters : new. Hosted sandboxes, QuickJS
- Memory and `AGENTS.md` : port
- Skills : port plus the October revamp. Bound tools, pinned skills, reload
- Subagents : port plus new. Dict subagents, `CompiledSubAgent`, the general-purpose subagent
- Context isolation : new. `isolated` and `fork` modes
- Dynamic subagents : new, beta. Orchestration shapes for many subagents ; the loop in code as the guarantee
- Recursive language models : new. Zhang, Kraska and Khattab, `arxiv.org/abs/2512.24601` ; the model splits a long input in code and calls itself on the parts
- Human-in-the-loop with `interrupt_on`, permissions : port
- Summarisation and context limits : port
- Profiles per model : new, one slide
- Deep Agents against the patterns of module 05 : new. Which pattern each feature implements
- Comparison with the Claude Agent SDK and Codex : new, one slide each, from the docs

Exercises : new, a Deep Agent over the capstone data with one `CompiledSubAgent`
and one skill ; new, offload a large tool result to the filesystem and measure.

### 09 Production Deployment : ~30 slides

Website module 8. Port of ARI510 11, refocused on serving agents and Deep Agents.

- The LangGraph API and Agent Server : port plus new. Assistants, threads, runs, `langgraph.json`
- `langgraph dev` and Studio : port
- Async subagents : new. Co-deployed graphs, start, check, steer, cancel
- The same shape outside LangGraph : new. `firstmate`, coding agents in worktrees under one orchestrator. Trainer demo
- A2A on Agent Server : new. Exposing a Deep Agent ; pointer back to 06
- Streaming to clients : port. Modes, subgraph events, SSE
- Persistence backends and checkpoint storage : new. Postgres, TTLs, `DeltaChannel`
- Double-texting and concurrency : new
- Deployment options : new. Self-hosted, LangSmith Deployment, Managed Deep Agents
- Scaling strategies : port. Workers, queues
- Evaluating a multi-agent system : port plus new. Four levels ; per agent and end to end ; trajectory match
- Monitoring : port plus new. Tracing across agents, Trajectories, online evals
- Cost optimisation : new. Model per agent, caching, summaries over transcripts, measured

Exercises : port ARI510 `exercise18 · Evaluating an Agent`, reworked for the
capstone ; new, a supervisor with an async subagent under `langgraph dev`.

### 10 Real-World Applications : ~16 slides

Website module 9. Each as a Deep Agent or a graph, and why.

- Research automation : port ARI510 demo36. `open_deep_research`
- Customer support : port ARI510 demo35. Handoffs
- Code review : new. Parallel reviewers and a judge ; `no-mistakes` as a checker built as a pipeline
- Coding agent fleets : new. `firstmate` mapped onto the course's patterns ; when a harness beats a graph
- Data analysis : new, short. The docs' data analysis Deep Agent
- Content pipelines : new, short
- Swarms at the frontier : new. OpenAI's Navier-Stokes swarm, September 2026, against the Fermat formalisation from ARI510 ; verification in Lean as the checker, cost in millions ; Zhang's "95% of the swarm is entirely useless" as the counterpoint
- Capstone : the comparison of stage 3 and stage 4

## The capstone

A multi-agent service desk for Aurelia Imaging Systems, the fictional maker of
hospital imaging equipment from ARI510. The data exists : 31 manuals and
bulletins, `service.db`, 50 tickets, 25 eval cases, an injected bulletin.

| stage | after | the student adds |
| --- | --- | --- |
| 1 | 03, day 1 | A graph workflow : triage, lookup in `service.db`, answer. Typed state and a checkpointer |
| 2 | 05, day 2 | Specialists for parts, manuals and scheduling behind a supervisor. Calls and tokens against stage 1 |
| 3 | 07, day 2 | Parallel diagnosis with a judge ; the manuals agent served separately and called over A2A ; part orders wait for approval inside a subagent |
| 4 | 08, day 3 | The same desk as a Deep Agent : skills for the procedures, the specialists as subagents. Compared with stage 3 on the eval set, tokens and lines of code |
| 5 | 09, day 3 | Served with `langgraph dev`, a long diagnosis as an async subagent, scored per agent and end to end, cost per ticket |

## The days

09:30 to 16:30, lunch about 12:30.

| | Morning | Afternoon |
| --- | --- | --- |
| Monday | 00 Preamble, 01 Introduction, 02 Graph Fundamentals | 03 State Management, capstone 1, 04 Building Agents |
| Tuesday | 05 Multi-Agent Patterns, capstone 2 | 06 Agent Communication, 07 Advanced Workflows, capstone 3 |
| Wednesday | 08 Deep Agents, capstone 4 | 09 Production, capstone 5, 10 Applications |

Tuesday is the densest day. Its cut order : 06 broadcasting and event systems,
05 hierarchical teams, 07 durable execution, the A2A part of capstone 3.

**Pivots**, as ARI510 :

- **No LangChain background.** Lengthen 04 ; shorten 02 and 03 to the core slides
- **Strong developer.** Skip the 04 refresher ; A2A and async subagents as full labs
- **Production focus.** Shorten 10 to one slide per application ; lengthen 09

## Reuse from ARI510

| ARI510 | ARI520 |
| --- | --- |
| 08 LangGraph in Depth, 31 slides, demo20 to demo23 | 02, 03, parts of 04 and 07 |
| 10 Multi-Agent Systems, 31 slides, demo28 to demo30 | 05, 08 |
| 04 First Agent middleware and limits | 04 |
| 11 Production, demo31 to demo33 | 04 testing, 09 |
| 12 Advanced Applications, demo35, demo36 | 10 |
| exercises 12, 13, 17, 18 | reworked |
| `data/capstone/`, Veenhaven Bus demo world | capstone, demos |
| `build/nb.py`, `run_notebook.py`, `setup_cell.py`, `stamp_setup.py`, `check_setup.py` | copied, setup cell pointed at OpenRouter |

New : most of 06 and 08, the hierarchical and collaborative patterns, A2A,
async subagents, interrupts in subagents, multi-agent evaluation, cost per
pattern, capstone stages 3 to 5.

## Build order

1. OpenRouter account and keys ; probe both candidate models ; choose
2. Copy tooling, upgrade the stack, run `check_setup.py` and the five patterns
3. Course map with demo and exercise numbering
4. Slides 00 to 10, ported modules first
5. Demos, then exercises with guides, then capstone stages
6. Execute every notebook against the endpoint ; record measurements
7. Lint, build PDFs, timing and skip marks
8. Freeze the stack ; dry run on the classroom laptop ; publish

## Calendar

Proposed, three weeks to Monday 2 November :

| week | work | Feiko reviews |
| --- | --- | --- |
| 13 to 18 October | Model probe and choice, stack upgrade, course map ; ported modules 01 to 05 with demos | course map ; module 05 |
| 19 to 25 October | New modules 06, 08, 09 ; 07 and 10 ; exercises ; capstone stages | 06 and 08 ; capstone guide |
| 26 to 30 October | Execute everything, measurements, PDFs, timing ; freeze about 27 October ; laptop prep and dry run | dry run on the classroom laptop |

## Risks

- **The model is new to the course.** Every ARI510 measurement is void ; re-measure
- **Agent Server locally.** A2A and async subagents need `langgraph dev`, maybe a LangSmith key
- **Three weeks to build.** Volume is cut before quality ; ported modules first
- **API churn.** `deepagents` released nine times in four weeks. Freeze early

## Settled on 13 October

- In person in Houten, on a SpiralTrain laptop Feiko prepares beforehand :
  `uv sync`, the embedding model cached, `langgraph-cli` installed, `.env` with
  the participant's capped key, `check_setup.py` passing, one notebook run
- LangSmith : Feiko has a free Developer account in the EU region. Key goes in
  `.env` as `LANGSMITH_API_KEY`, never in chat, with
  `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`. Probe whether
  `langgraph dev` opens Studio on the EU host or needs `--studio-url`
- Managed Deep Agents : slide only. It runs on US cloud, and deploying needs a
  paid plan ; Plus is $39 a seat a month with one free serverless deployment.
  Optional : a second free US Developer account to try `mda dev` locally
- OpenRouter : Feiko creates the account, a trainer key and a capped participant key
- Yair's crew post, diagram and goldmary.eu coding setup may be quoted on slides

## Status, 14 October

Built, executed and pushed (Forgejo `SpiralTrain/Multi-Agents-LangGraph`, GitHub
`FeikoWielsma/Multi-Agents-LangGraph`, public for the Colab download path) :

- Slides 00 to 10, about 285 ; 67 demo notebooks, 0 errors ; lint clean ; both PDFs
- Exercises 01 to 11 and capstone stages 1 to 5 : guides, skeletons, executed solutions
- Per-module measurements in `measurements-NN.md`, exercises and capstone in
  `measurements-exercises.md` and `measurements-capstone.md`. OpenRouter spend for the
  whole build : $0.12 of the $10 trainer key

Decisions taken during the build :

- `deepagents[quickjs]` and `langchain-quickjs==0.3.9` added to the pins, so module 08
  runs the QuickJS interpreter and agent-written subagent fan-out (`measurements.md`)
- Module 08 demo08 b keeps its honest result : splitting 31 manuals that fit in one
  prompt costs more tokens, not fewer ; the RLM gain needs an input beyond the window
- On langgraph-api 0.16.0, A2A takes the assistant UUID, not the graph name ; slides,
  exercise05 and capstone stage 3 teach that (`measurements-06.md`)
- Capstone stage 5 keeps the evaluation lesson : tool coverage True while 2 of 5
  answers are wrong on tool arguments (`CT400`) ; argument validation is optional
- Exercise10 scores trajectories with `tool_args_match_mode="ignore"` ; exercise11
  holds its async task about two minutes so the first check sees `running` ;
  exercise02 is deterministic, no model calls
- Exercise pills sit on the module summary slides ; capstone stages are named in the
  speaker notes, since the linter allows only demo and exercise pills
- Only notebooks are committed under `exercises/` and `solutions/` ; notebooks write
  their own server files at run time

Next :

- Timing and skip marks per module against "The days"
- Laptop prep checklist from "Settled on 13 October" ; freeze the stack about 27 October
- Dry run on the classroom laptop about 29 October
- Optional : the URL of Yair's post for the module 01 and 06 notes

