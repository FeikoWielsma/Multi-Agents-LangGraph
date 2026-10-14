# Course map : modules, demos, exercises

Revised 13 October 2026, second pass ; built as listed on 14 October. A demo for
almost every other slide, but grouped. One notebook covers two to four related slides, one section per slide,
so the trainer switches notebooks less often.

## Conventions

- Demos are numbered per module, as in Advanced Python ; `demo01` restarts in
  every module. Files : `notebooks/NN-module/demoNN-slug.ipynb`
- A notebook has one section per slide it serves. The first section's pill is
  `> \`demo04 · handoffs\`` ; later sections add a letter, `> \`demo04b ·
  handoffs-fixed\``, as Go Programming does. The linter checks the numbered
  pills for order and ignores the lettered ones
- `llm` marks a notebook that calls the course model ; the others are pure
  LangGraph, deterministic, and run in seconds
- `from` names the ARI510 source ; blank means new
- Demos run on the Veenhaven Bus data ; exercises and the capstone on Aurelia
- Exercises keep one sequence across the course

Counts as built : 67 demo notebooks (module 10 demo05 is a live trainer demo with
no notebook) ; 11 exercises ; 5 capstone stages ; about 285 slides. Exercise
notebooks are `exercises/exerciseNN-slug.ipynb`, guides `src/exercises/NN-slug.md`,
capstone `exercises/capstone-stageN.ipynb` and `src/exercises/99-capstone.md`.
Exercise pills sit on the module's summary slide ; capstone stages are named in
its speaker notes.

## 01 Introduction to LangGraph : 4 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · one-agent-limits` | | llm | |
| `demo02 · first-look` | a first graph ; b a first multi-agent system | llm | ARI510 demo20 |
| `demo03 · three-levels` | one task as a graph, with `create_agent`, as a Deep Agent | llm | |
| `demo04 · workflow-or-agent` | | llm | ARI510 demo01 |

## 02 Graph Fundamentals : 6 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · graphs-and-state-machines` | directed graphs ; b a work order's lifecycle | | |
| `demo02 · nodes-and-edges` | nodes and edges ; b `START`, `END`, entry points | | ARI510 demo20 |
| `demo03 · routing` | conditional edges ; b `path_map` ; c cycles and the recursion limit | | ARI510 demo20 |
| `demo04 · command-and-send` | `Command` ; b `Send` and map-reduce ; c deferred nodes | | ARI510 demo23 |
| `demo05 · compiling-and-apis` | compile and visualise ; b the Functional API | | ARI510 demo20, demo23 |
| `demo06 · a-model-in-a-node` | | llm | |

Exercise : `exercise01 · Graphs and Loops`, ARI510 exercise12.

## 03 State Management : 6 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · state-schemas` | `TypedDict` ; b Pydantic ; c input and output schemas ; d private state | | |
| `demo02 · reducers` | `add_messages` ; b custom reducers ; c overwriting ; d concurrent updates | | ARI510 demo20 |
| `demo03 · checkpointers` | threads ; b `SqliteSaver` | llm | ARI510 demo22 |
| `demo04 · history-and-time-travel` | state history ; b replay ; c forking with `update_state` | llm | ARI510 demo22 |
| `demo05 · the-store` | | | ARI510 demo18 |
| `demo06 · debugging-with-stream-modes` | | llm | |

Exercise : `exercise02 · State for Two Agents`. Capstone stage 1.

## 04 Building Agents : 7 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · react-as-a-graph` | by hand ; b `ToolNode` and `tools_condition` | llm | ARI510 demo21 |
| `demo02 · create-agent` | `create_agent` ; b an agent as a node ; c custom agent state | llm | ARI510 demo11 |
| `demo03 · middleware-hooks` | | llm | ARI510 demo12 |
| `demo04 · node-failures` | `RetryPolicy` ; b node `timeout` ; c `error_handler` | | |
| `demo05 · agent-failures` | tool errors ; b model fallback ; c call limits | llm | ARI510 demo12 |
| `demo06 · tracing-with-langsmith` | trainer | llm | ARI510 demo09 |
| `demo07 · testing-agents` | a scripted fake model ; b pytest | | ARI510 demo32 |

Exercise : `exercise03 · An Agent with Tests`.

## 05 Multi-Agent Patterns : 9 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · subagents` | agents as tools ; b what a subagent sees | llm | ARI510 demo28 |
| `demo02 · supervisors` | a supervisor node ; b hierarchical teams | llm | |
| `demo03 · router` | classify and dispatch ; b in parallel | llm | ARI510 demo28 |
| `demo04 · handoffs` | as documented, both faults ; b fixed ; c in one agent | llm | ARI510 demo28 |
| `demo05 · skills` | `load_skill` ; b subagent or skill | llm | ARI510 demo28 |
| `demo06 · workflows` | sequential ; b parallel ; c orchestration in code | llm | ARI510 demo28 |
| `demo07 · maker-checker` | a model checker ; b a checker in code | llm | |
| `demo08 · debate-and-selection` | debate with a judge ; b generate and filter | llm | |
| `demo09 · what-each-pattern-costs` | | llm | `build/probe_patterns.py` |

Exercise : `exercise04 · A Multi-Agent Visit Planner`, ARI510 exercise17. Capstone stage 2.

## 06 Agent Communication : 7 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · what-agents-share` | shared state or messages ; b full history, task or summary | llm | |
| `demo02 · subgraph-communication` | handoff to the parent ; b shared keys ; c transformed input and output | llm | |
| `demo03 · served-agents` | calling an agent under `langgraph dev` ; b an agent card | llm | |
| `demo04 · two-agents-over-a2a` | | llm | |
| `demo05 · events-and-synchronisation` | streaming subgraphs ; b custom events ; c a broadcast channel ; d fan-in and barriers | llm | |
| `demo06 · conflicts` | conflicting writes ; b voting ; c a judge and a tie-break | llm | |
| `demo07 · buyer-and-seller` | the conflict ; b least privilege per agent | llm | |

Exercises : `exercise05 · Two Agents over A2A`, `exercise06 · Buyer and Seller`.

## 07 Advanced Workflows : 6 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · interrupts` | `interrupt` ; b approve, edit, reject ; c several interrupts | llm | ARI510 demo22 |
| `demo02 · interrupts-in-multi-agent` | in a subgraph ; b in a subagent | llm | |
| `demo03 · human-in-the-loop-middleware` | | llm | ARI510 demo22 |
| `demo04 · loop-detection` | a watchdog node ; b repeated tool calls | llm | |
| `demo05 · retries-and-fallbacks` | backoff ; b a fallback chain | llm | |
| `demo06 · composition-and-durability` | composing workflows ; b branching at scale ; c resuming after a crash | llm | |

Exercise : `exercise07 · Approval in a Subagent`, ARI510 exercise13. Capstone stage 3.

## 08 Deep Agents : 10 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · deep-agent-from-scratch` | the loop ; b a todo list ; c files ; d subagents | llm | ARI510 demo29 |
| `demo02 · create-deep-agent` | defaults ; b planning with `write_todos` | llm | ARI510 demo30 |
| `demo03 · the-filesystem` | virtual files ; b offloading large results | llm | |
| `demo04 · backends` | state ; b filesystem ; c store ; d composite | llm | ARI510 demo30 |
| `demo05 · permissions-and-execution` | permissions ; b the interpreter ; c a local shell | llm | ARI510 demo30 |
| `demo06 · memory-and-skills` | `AGENTS.md` ; b skills ; c tools bound to skills | llm | ARI510 demo30 |
| `demo07 · subagents` | dict subagents ; b `CompiledSubAgent` ; c fork mode | llm | |
| `demo08 · dynamic-subagents` | fan-out in code ; b splitting a long input, the RLM idea | llm | |
| `demo09 · control` | `interrupt_on` ; b summarisation | llm | ARI510 demo30 |
| `demo10 · deep-agent-or-graph` | capstone stage 3 against stage 4 | llm | |

Exercises : `exercise08 · A Deep Agent`, `exercise09 · Offload and Measure`, optional. Capstone stage 4.

## 09 Production Deployment : 8 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · agent-server` | `langgraph.json` ; b `langgraph dev` and Studio ; c threads and runs | llm | ARI510 demo31, demo33 |
| `demo02 · serving-in-practice` | streaming to a client ; b double-texting ; c persistence across restarts | llm | ARI510 demo33 |
| `demo03 · async-subagents` | | llm | |
| `demo04 · a2a-on-agent-server` | | llm | |
| `demo05 · evaluating-agents` | the final answer ; b trajectory match ; c a trajectory judge ; d each agent | llm | ARI510 demo32 |
| `demo06 · a-langsmith-experiment` | trainer | llm | |
| `demo07 · cost` | a model per agent ; b prompt caching | llm | |
| `demo08 · injection-through-an-error` | | llm | ARI510 demo34 |

Exercises : `exercise10 · Evaluating a System of Agents`, `exercise11 · An Async Subagent on a Server`. Capstone stage 5.

## 10 Real-World Applications : 5 notebooks

| notebook | sections | | from |
| --- | --- | --- | --- |
| `demo01 · research-agent` | | llm | ARI510 demo36 |
| `demo02 · customer-support` | | llm | ARI510 demo35 |
| `demo03 · code-review` | | llm | |
| `demo04 · data-and-content` | data analysis ; b a content pipeline | llm | |
| `demo05 · firstmate` | trainer, Feiko's laptop, no notebook | | |
