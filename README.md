# Multi Agents with LangGraph : course material

SpiralTrain ARI520. Three days of building systems of agents with LangGraph :
the graph runtime, the multi-agent patterns, agent communication over A2A, Deep
Agents, and serving and evaluating a system of agents.

## Setup

1. Install [uv](https://docs.astral.sh/uv/)
2. `uv sync --group server` in this folder
3. Copy `.env.example` to `.env` and paste the course key after `COURSE_API_KEY=`
4. `uv run python check_setup.py` ; it should end with every check passed
5. `uv run jupyter lab`

The full walkthrough is exercise 0 in the exercises PDF. On the course laptop the
trainer has done these steps already.

## Colab, if the laptop setup fails

The first cell of every notebook detects Colab, installs the pinned packages and
downloads the data it needs. Add the course key once : click the key icon in the
left sidebar, name the secret `COURSE_API_KEY`, paste the key, and switch notebook
access on. Notebooks that start a local Agent Server with `langgraph dev` (module 06
demo03 and demo04, module 09, exercises 05 and 11, capstone stages 3 and 5) need
the laptop.

Do not paste anything confidential from your employer into these notebooks. The
exercises never need real data.

## Materials

| folder | contents |
| --- | --- |
| `notebooks/` | demonstrations, run by the trainer, with their outputs |
| `exercises/` | exercise notebooks with blanks to fill in |
| `solutions/` | the same exercises, completed and run |
| `data/` | the fictional Veenhaven Bus world for the demos and the Aurelia world for the exercises |

## Per module

| module | demonstrations | exercises |
| --- | --- | --- |
| 01 Introduction to LangGraph | demo01 one-agent-limits, demo02 first-look, demo03 three-levels, demo04 workflow-or-agent | |
| 02 Graph Fundamentals | demo01 to demo06 : graphs and state machines, nodes and edges, routing, command and send, compiling and APIs, a model in a node | 01 Graphs and Loops |
| 03 State Management | demo01 to demo06 : state schemas, reducers, checkpointers, history and time travel, the store, stream modes | 02 State for Two Agents, capstone stage 1 |
| 04 Building Agents | demo01 to demo07 : ReAct as a graph, create_agent, middleware, node failures, agent failures, LangSmith tracing, testing agents | 03 An Agent with Tests |
| 05 Multi-Agent Patterns | demo01 to demo09 : subagents, supervisors, router, handoffs, skills, workflows, maker-checker, debate and selection, what each pattern costs | 04 A Multi-Agent Visit Planner, capstone stage 2 |
| 06 Agent Communication | demo01 to demo07 : what agents share, subgraph communication, served agents, two agents over A2A, events and synchronisation, conflicts, buyer and seller | 05 Two Agents over A2A, 06 Buyer and Seller |
| 07 Advanced Workflows | demo01 to demo06 : interrupts, interrupts in multi-agent systems, human-in-the-loop middleware, loop detection, retries and fallbacks, composition and durability | 07 Approval in a Subagent, capstone stage 3 |
| 08 Deep Agents | demo01 to demo10 : from scratch, create_deep_agent, the filesystem, backends, permissions and execution, memory and skills, subagents, dynamic subagents, control, Deep Agent or graph | 08 A Deep Agent, 09 Offload and Measure, capstone stage 4 |
| 09 Production Deployment | demo01 to demo08 : Agent Server, serving in practice, async subagents, A2A on Agent Server, evaluating agents, a LangSmith experiment, cost, injection through an error | 10 Evaluating a System of Agents, 11 An Async Subagent on a Server, capstone stage 5 |
| 10 Real-World Applications | demo01 research-agent, demo02 customer-support, demo03 code-review, demo04 data-and-content | capstone review |

Exercise notebooks are `exercises/exerciseNN-slug.ipynb` and `exercises/capstone-stageN.ipynb` ;
the guide for each is a chapter of the exercises PDF.

The capstone builds a multi-agent service desk for Aurelia Imaging Systems, a
made-up maker of hospital imaging equipment, in five stages. Each stage notebook
starts from the reference solution of the stages before it.

The running demonstration setting is Veenhaven Bus, a fictional bus operator.

## For maintainers

`AGENTS.md` describes the repository, the builders and the rules ; `build/plan.md`
holds the design and its current status.
