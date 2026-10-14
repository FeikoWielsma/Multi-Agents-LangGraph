---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Graph Fundamentals
---

# Why LangGraph?

- Chains suit sequential flow : `prompt -> model -> parser -> result`
- A work order needs more control than a chain :
  - An urgent order goes to an engineer, a routine one to the queue
  - A failed diagnosis runs again
  - Depot reports run in parallel ; a part order waits for approval
- LangGraph models a workflow as nodes over shared state :
  - Edges express branching and loops
  - State is explicit and typed
- LangChain agents and Deep Agents use the LangGraph runtime
- The application code owns the shape of the workflow

<!-- NOTES:
Timing : about 55 minutes for the module, including six demos. Open with the workflows whose paths are known before the model runs.
Source : course timing estimate, 13 October 2026. The module has 26 slides and six demos ; live delivery timing is unmeasured.
-->

---

# LangChain vs. LangGraph

| Concern | LCEL runnables | LangGraph |
| --- | --- | --- |
| Composition | Sequences, parallel calls and branches | Nodes and edges over state |
| State | Values passed between runnables | Explicit state returned from nodes |
| Repetition | Application code or custom runnables | Cycles and conditional edges |
| State updates | Application-managed values | Explicit updates returned from nodes |

- `create_agent` returns a compiled LangGraph graph
- A graph of its own suits logic specific to the application, such as a work order's lifecycle

<!-- NOTES:
Skippable.
-->

---

# Thinking in LangGraph

- A design starts from the process :
  - A work order is diagnosed, waits for parts, then is repaired
  - Diagnosis needs judgment ; the parts lookup does not
- Each step becomes a node ; a model call for judgment, a plain function for fixed work
- State holds every value a step reads, writes or needs after a pause
- Edges connect the nodes :
  - Fixed edges for known order, such as parts before repair
  - Conditional edges for decisions, such as a second diagnosis
- Control points go where a mistake costs most, such as a part order
- The graph drawing documents the design

---

# Directed Graphs

- A directed graph contains vertices and directed edges :
  - Vertices are steps, such as `diagnose`, `parts` and `repair`
  - Edges are allowed transitions, such as `diagnose` to `parts`
- A path follows the direction of each edge
- Fan-out sends execution to several branches, such as one per depot
- Fan-in joins the branch results at a later step
- A directed acyclic graph has no path back to an earlier vertex
- A cyclic graph contains at least one loop

> `demo01 · graphs-and-state-machines`

---

# DAGs and Cycles

- A DAG contains no directed cycle
- A cyclic graph allows a path to return to an earlier node
- A work order that goes from open to diagnosed to waiting for parts to closed is a DAG
- An edge from `parts` back to `diagnose` for a retry adds a cycle
- LangGraph accepts both ; a recursion limit bounds every cycle

---

# Fan-out and Fan-in

- Fan-out starts several branches from one step, such as a report per depot
- Fan-in continues once every branch has returned
- Branches that write one key need a reducer, such as `operator.add` on a list of reports
- `Send` creates branches whose number is known only at runtime, such as one per depot in the input

---

# State Machines

- A state machine represents a process as states and transitions :
  - State records where the work order is, such as open or waiting for parts
  - A transition changes state and selects the next step
- A plain node applies a fixed transition, such as open to diagnosed
- A model can choose a transition when the next step needs judgment
- A cycle lets the work order return to diagnosis
- An attempts counter in state decides when the loop ends

> `demo01b · work-order-lifecycle`

---

# Model Transitions

- A deterministic node applies a fixed transition to state
- A model node supplies the judgment, such as whether a work order is electrical or mechanical
- A routing function maps that label to a node, such as the electrical bay
- The other steps stay plain functions

---

# LangGraph Concepts

- A graph is a workflow over state
- State is a schema that nodes read and update
- A node is a function that receives state and returns updates
- An edge connects a node to a possible next node
- A conditional edge selects a target from the current state
- `START` and `END` mark graph entry and exit
- A builder is compiled before it is invoked

---

# Node Functions

- A node receives the current state as its input
- A node returns only the keys it changed, such as `{"status": "diagnosed"}`
- A node may be a Python function, a runnable, or a compiled graph
- A node can return `Command` to update state and route execution

---

# StateGraph Nodes and Edges

- `StateGraph` builds a graph around a state schema :
  - `add_node` registers a function or compiled graph
  - `add_edge` adds a fixed transition
  - `add_conditional_edges` adds a routed transition
- A node returns a partial state update
- A compiled graph exposes `invoke` and `stream`

> `demo02 · nodes-and-edges`

<!-- NOTES:
Source : LangGraph documentation, Graph API, https://docs.langchain.com/oss/python/langgraph/graph-api. API examples checked against LangGraph 1.2.15.
-->

---

# Hello LangGraph

```python
from typing import TypedDict
from langgraph.graph import END, START, StateGraph

class Number(TypedDict):
    value: int

builder = StateGraph(Number)
builder.add_node("double", lambda s: {"value": s["value"] * 2})
builder.add_edge(START, "double")
builder.add_edge("double", END)
graph = builder.compile()
print(graph.invoke({"value": 5}))
```

---

# START and END

- `START` identifies the graph entry point
- `END` marks a completed path
- `add_edge(START, "node")` defines the entry edge
- `add_edge("node", END)` defines a terminal edge
- `set_entry_point` and `set_finish_point` provide named alternatives

> `demo02b · start-end-entry`

---

# Conditional Edges

- A conditional edge calls a routing function at runtime :
  - The function reads state and returns a route label
  - `route` returns `"page"` for an urgent work order and `"queue"` otherwise
- Route labels can match node names directly
- A `Literal` return type documents the possible routes
- A route can select a branch or send execution around a cycle

> `demo03 · routing`

<!-- NOTES:
Source : LangGraph documentation, Graph API, https://docs.langchain.com/oss/python/langgraph/graph-api. Conditional edge behavior checked against LangGraph 1.2.15.
-->

---

# Routing with path_map

- `path_map` maps route labels to graph node names :

```python
builder.add_conditional_edges(
    "triage",
    route,
    {"urgent": "page_engineer", "routine": "queue"},
)
```

- A dictionary maps labels to destinations
- A list declares possible destinations when labels match node names

> `demo03b · path-map`

---

# Loops and Cycles

- A cycle returns execution to an earlier node :
  - A router decides whether to continue or exit
- Loops support retries and iterative refinement
- Every invocation has a recursion limit measured in graph steps
- Exceeding the limit raises `GraphRecursionError`
- Set `recursion_limit` in the invocation configuration

> `demo03c · recursion-limit`

<!-- NOTES:
Source : LangGraph documentation, Graph API, https://docs.langchain.com/oss/python/langgraph/graph-api. Recursion behavior checked against LangGraph 1.2.15.
-->

---

# GraphRecursionError

- The recursion limit bounds graph steps in one invocation
- A node with an edge back to itself raises `GraphRecursionError` at the limit
- A higher limit permits more steps before the runtime stops the graph
- Every cycle needs a routing condition that exits, such as a cap on attempts

---

# Command

- `Command` combines a state update with a routing decision :

```python
from langgraph.types import Command

def triage(state):
    return Command(update={"assigned": "urgent"}, goto="page")
```

- `update` changes state from inside a node
- `goto` selects one or more next nodes
- A node returning `Command` routes itself ; it needs no conditional edge

> `demo04 · command-and-send`

<!-- NOTES:
Source : LangGraph documentation, Graph API, https://docs.langchain.com/oss/python/langgraph/graph-api. `Command` behavior checked against LangGraph 1.2.15.
-->

---

# Parallel Branches and Send

- Nodes with a shared predecessor can run in parallel
- `Send` creates runtime branches with individual inputs :

```python
from langgraph.types import Send

def fan_out(state):
    return [Send("report", {"depot": name}) for name in state["depots"]]
```

- A `collect` node summarises the reports as `3 depots checked`
- Map-reduce combines fan-out work with a reduction step

> `demo04b · send-map-reduce`

---

# Deferred Nodes

- A deferred node waits until the other scheduled work is complete

```python
builder.add_node("collect", collect, defer=True)
```

- A deferred `collect` waits for every depot report before it summarises
- `defer` is available in LangGraph 1.2.15

> `demo04c · deferred-nodes`

<!-- NOTES:
Source : LangGraph 1.2.15 installed API signature for `StateGraph.add_node`, verified 13 October 2026. Demo04 executes the deferred aggregation example.
-->

---

# Compiling a Graph

- `compile` checks the builder's structure and returns a runnable graph
- A checkpointer is attached at compile time
- Runtime options such as `recursion_limit` go into each invocation
- A builder is compiled once ; the graph is invoked many times

---

# Visualising a Graph

- A compiled graph returns a Mermaid description :

```python
print(graph.get_graph().draw_mermaid())
```

- Mermaid text can be displayed in Markdown or a compatible viewer
- Mermaid text rendering requires no network service

> `demo05 · compiling-and-apis`

<!-- NOTES:
Source : LangGraph documentation, Graph API, https://docs.langchain.com/oss/python/langgraph/graph-api. Mermaid output checked against LangGraph 1.2.15.
-->

---

# Functional API

- The Functional API expresses a workflow with decorated functions :

```python
from langgraph.func import entrypoint, task

@task
def clean(text: str) -> str:
    return text.strip()

@entrypoint()
def workflow(text: str) -> str:
    return clean(text).result()
```

- Tasks can run in parallel and return values to the entrypoint

> `demo05b · functional-api`

<!-- NOTES:
Skippable.
Source : LangGraph documentation, Functional API, https://docs.langchain.com/oss/python/langgraph/functional-api. Example checked against LangGraph 1.2.15.
-->

---

# Graph API or Functional API

- Graph API :
  - Explicit nodes and edges are drawable and inspectable
  - Branches and loops appear directly in the graph definition
- Functional API :
  - Ordinary Python control flow expresses the sequence
  - Tasks mark work that can run and resume independently
- Both APIs use the LangGraph runtime
- A task can call a compiled graph

<!-- NOTES:
Skippable.
Source : LangGraph documentation, Graph API and Functional API, https://docs.langchain.com/oss/python/langgraph/graph-api and https://docs.langchain.com/oss/python/langgraph/functional-api.
-->

---

# A Model in a Node

- A model call is one node among plain functions :
  - `classify` asks the model whether a work order is electrical or mechanical
  - A routing function sends it to the electrical or the mechanical bay
- Model output can vary between runs
- The graph fixes every step around that one judgment

> `demo06 · a-model-in-a-node`

---

# Summary : Graph Fundamentals

- Directed graphs describe steps and allowed transitions
- State machines combine state with transitions
- `StateGraph` connects nodes with fixed and conditional edges
- `START`, `END`, `Command`, and `Send` express graph control flow
- Cycles run under a configurable recursion limit
- Deferred nodes wait for scheduled work to finish
- Compilation prepares a runnable graph that can be visualised
- Graph API and Functional API share the LangGraph runtime
