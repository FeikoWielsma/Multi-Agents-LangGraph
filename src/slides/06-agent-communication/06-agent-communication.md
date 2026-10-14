---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Agent Communication
---

# Message Passing

- A message carries a selected payload :
  - The sender names the recipient and a correlation id
  - The payload holds the facts that recipient needs
- Shared state exposes every key the nodes have in common
- Veenhaven's stock and manual findings can travel either way
- A local envelope has no network transport

<!-- NOTES:
Timing : Tuesday afternoon, before Advanced Workflows. Allow about 70 minutes for these slides and the committed notebook outputs. Live runs sit on COURSE_RPS 0.06 and are not the classroom timing. Cut event systems and state broadcasting first, matching the plan's cut order, then the Agent Protocol slide. Exercises exercise05 and exercise06 are owned by the lead.
New material. Sources : LangGraph 1.2.15 and langgraph-api 0.16.0, checked 14 October 2026 ; build/research-2026-10.md sections 3 and 5.
Source : notebooks/06-agent-communication/demo01-what-agents-share.ipynb a ; build/research-2026-10.md sections 3 and 5. Timing is an allocated teaching budget, recorded in build/measurements-06.md.
-->

---

# Shared State

- Parallel nodes write different keys of one schema
- A join waits for both writers before the report

```python
builder.add_edge(START, "parts")
builder.add_edge(START, "manuals")
builder.add_edge(["parts", "manuals"], "combine")
```

- `parts` writes stock ; `manuals` writes the error guidance
- The report node reads both keys

> `demo01 · what-agents-share`

<!-- NOTES:
demo01 a runs the shared-state graph and then a local Envelope. CE-CF-02 is stock 6 at Rietpoort, read from service.db on 14 October 2026. Do not promise the wording of the combined note.
Source : demo01-what-agents-share.ipynb a ; langgraph/graph/state.py, StateGraph.add_edge, in installed langgraph 1.2.15 ; build/measurements-06.md.
-->

---

# Full History

- Full history passes every message the caller holds
- The receiver can see the stock note and the open question
- Input grows with the transcript
- A later agent can repeat a lookup that is already in that history

<!-- NOTES:
Source : demo01-what-agents-share.ipynb b, history and contexts. Transcript growth follows the explicit message list ; a repeated lookup is a possible model choice, not an observed outcome in this demo.
-->

---

# Agent Context

- Four boundaries for one maintenance request :
  - Full history includes the earlier stock note
  - Task only sends the selected stock payload
  - A Python copy of the history adds a new task
  - A summary returns selected facts to the caller
- The task-only request omits the first action on purpose
- A summary can drop a condition on the way back

> `demo01b · full-history-task-or-summary`

<!-- NOTES:
demo01 b prints each context and its input-token count. The fork is an ordinary Python copy, not a checkpoint fork and not Deep Agents fork mode. Say that a missing first action in the task-only answer is the boundary, not a model failure. Summary wording will vary.
Source : demo01-what-agents-share.ipynb b ; build/measurements-06.md. All four inputs also receive the same manual excerpt as a SystemMessage. Task-only omits the repair request, not that system evidence. A lost condition is a risk ; this saved summary preserves the condition.
-->

---

# Handoffs

- A child node transfers control to a node in the parent

```python
def handoff(state):
    return Command(
        goto="manuals",
        graph=Command.PARENT,
        update={"messages": state["messages"]},
    )
```

- `Command.PARENT` targets the closest parent graph
- The destination is a node of the parent graph

> `demo02 · subgraph-communication`

<!-- NOTES:
Checked on langgraph 1.2.15. A return annotation Command[Literal["manuals"]] registers manuals as an edge inside the child, and compile raises ValueError because the child has no such node. The demo therefore omits that annotation. Module 05 still owns the tool-call faults: parallel tool calls drop a sibling result, and forwarding only the last assistant message drops earlier work. This transfer is node-triggered and forwards the child history. Source : https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs and build/measurements.md.
Source : demo02-subgraph-communication.ipynb a ; langgraph/types.py, Command.PARENT, and langgraph/graph/state.py in installed langgraph 1.2.15.
-->

---

# Parent Message Update

- The parent merges messages by id with `add_messages`
- The receiver's list includes the stock note
- The written answer can still omit a fact from that list
- The module 05 tool handoff disables parallel tool calls
- A tool handoff needs a `ToolMessage` for the transfer call
- This node transfer has no pending tool call

<!-- NOTES:
Source : demo02-subgraph-communication.ipynb a, receiver and answer outputs ; langgraph/graph/message.py, add_messages ; build/measurements.md, module 05 handoff probes. Serial tool calls are the taught implementation constraint, not a general restriction on every handoff design.
-->

---

# Shared Keys

- A compiled subgraph shares keys present in both schemas
- `part_no` and `stock` cross into the parent
- `working_note` exists only on the child schema
- The parent result does not contain `working_note`

> `demo02b · shared-keys`

<!-- NOTES:
Port of the compiled-subgraph shape from ARI510 demo23, on the bus part number. Checked on langgraph 1.2.15: the private key stays out of the parent result.
Source : demo02-subgraph-communication.ipynb b ; langgraph/graph/state.py, attach_node, in installed langgraph 1.2.15 ; build/measurements-06.md.
-->

---

# Transformed Input and Output

- A wrapper node maps parent fields onto the child schema

```python
def mapped_parts(state):
    child_input = {"part_no": state["item"]}
    child_output = parts_graph.invoke(child_input)
    return {"finding": child_output["stock"]}
```

- The child input has no `requester` field
- Leaving a field out of model input does not hide logs or credentials

> `demo02c · transformed-input-and-output`

<!-- NOTES:
The wrapper is the data interface. Say explicitly that this is not a security boundary.
Source : demo02-subgraph-communication.ipynb c, mapped_parts and printed child input/output. The wrapper selects fields ; it adds no process isolation or access checks.
-->

---

# Communication Protocols

- Agent and tool interfaces use these protocols :

| Boundary | Mechanism |
| --- | --- |
| One process | Tool call, shared keys, `Command` |
| Async subagent | Agent Protocol |
| Two servers | A2A JSON-RPC |
| Tools | MCP |

- In-process agents can access the same process credentials
- Separate servers can use separate storage and credentials

<!-- NOTES:
Source : demo02-subgraph-communication.ipynb ; demo04-two-agents-over-a2a.ipynb ; deepagents/middleware/async_subagents.py, _ClientCache and _create_start_task_tool ; langchain/mcp/__init__.py. Separate identities require configuration ; a process boundary does not assign credentials automatically.
-->

---

# Agent Protocol

- Agent Protocol is the HTTP API for runs and threads
- `POST /runs/wait` runs an assistant and returns its state
- Async subagents use these tools :
  - `start_async_task` and `check_async_task`
  - `update_async_task`, `cancel_async_task`, `list_async_tasks`
- Deep Agents owns that harness ; the server owns the transport

<!-- NOTES:
Skippable. Tool names checked in deepagents 0.7.24, middleware/async_subagents.py. Module 08 teaches the harness. This slide only places the protocol next to A2A. Source : https://github.com/langchain-ai/agent-protocol
Source : deepagents/middleware/async_subagents.py in installed deepagents 0.7.24, the five tool factories and langgraph_sdk clients ; langgraph_sdk/client.py, RunsClient.wait and SyncRunsClient.wait ; demo03-served-agents.ipynb a.
-->

---

# MCP for Tools

- `langchain.mcp` turns MCP tools into tools an agent can call
- The package is beta in langchain 1.4.5
- An MCP server publishes tools
- Agent-to-agent calls use A2A or Agent Protocol
- An agent card describes an assistant's communication interface

<!-- NOTES:
Import checked 14 October 2026: langchain.mcp exposes MCPAdapter and as_langchain_tool, and warns that the API is beta. No MCP demo in this module. Do not describe MCP as a way for two agents to delegate.
Source : langchain/mcp/__init__.py, adapter.py and tools.py in installed langchain 1.4.5 ; langgraph_api/api/a2a.py, generate_agent_card. MCP is described here through its tool interface ; the slide does not claim that an MCP tool cannot wrap an agent.
-->

---

# Served Agents

- `langgraph dev` serves a graph on the local Agent Server
- The echo server runs with the LangSmith variables removed
- `POST /runs/wait` accepts the graph id, such as `parts`
- The parts server sends metadata to the configured EU endpoint
- Both measured Studio banners use `smith.langchain.com`

> `demo03 · served-agents`

<!-- NOTES:
Measured 14 October 2026 on langgraph-cli 0.4.33 and langgraph-api 0.16.0. With the LangSmith variables removed, the notebook prints metadata loop skipped and Studio at https://smith.langchain.com/studio/, and the echo task still completes. With the repository environment inherited and tracing left off, the metadata loop is not skipped, the log names the EU metadata host, and the Studio banner stays on smith.langchain.com. The key is not required to serve a graph. The demo passes --no-browser, --no-reload and --allow-blocking, on port 2124. Do not read server.tmp aloud; it can contain request logs. Never print the key.
Source : demo03-served-agents.ipynb a and b, server_facts outputs ; build/measurements-06.md ; langgraph_api/metadata.py and langgraph_api/cli.py in installed langgraph-api 0.16.0. The inherited environment run and keyless run are distinct ; the Studio observation does not establish a rule for tracing-enabled runs.
-->

---

# Agent Cards

- The card describes one assistant and its transport
- The installed server requires the assistant UUID :

```text
GET /.well-known/agent-card.json?assistant_id=<uuid>
POST /a2a/<uuid>
```

- A graph name is rejected with "must be a UUID"
- `POST /assistants/search` returns the UUID for that graph id
- Default assistant UUIDs derive from the graph id with `uuid5`
- A2A requires a `messages` key in the input schema
- The card grants no credentials

> `demo03b · agent-card`

<!-- NOTES:
The docs and build/research-2026-10.md section 3 say /.well-known/agent-card.json?assistant_id=... and /a2a/{assistant_id}. On langgraph-api 0.16.0 both reject a graph name. assistants/search returns assistant_id, and it matches uuid5(UUID("6ba7b821-9dad-11d1-80b4-00c04fd430c8"), graph_id). That namespace constant is what graph.py registers in this version; the demo reads the id from search and prints the match. The card reports protocolBinding JSONRPC and protocolVersion 1.0. supportsA2A is true when the input schema has messages.
Source : demo03-served-agents.ipynb a and b ; build/measurements-06.md ; langgraph_api/api/a2a.py, handle_jsonrpc_request and generate_agent_card ; langgraph_api/graph.py, register_graph. uuid5 describes default registered assistants ; custom assistants may have other UUIDs.
-->

---

# A2A Tasks

- The completed `SendMessage` response has `result.task` :
  - `status.state` is `TASK_STATE_COMPLETED`
  - Artifacts hold the assistant text
- `GetTask` returns the task directly, with history and no artifacts
- The completed `GetTask` status says "Task completed successfully"
- `contextId` is the thread id and must be a UUID
- `message/send` unwraps the task and lowercases the state

<!-- NOTES:
Checked against the echo graph and then the parts graph on 14 October 2026. A contextId of BW-7001 returns "Failed to create run: Invalid thread ID". GetTask historyScope is a top-level parameter; SendMessage takes historyScope inside configuration. Default history scope is context. historyScope task on a later turn keeps that turn. ListTasks returns tasks, pageSize, totalSize and nextPageToken. Separate servers do not share state when given the same contextId; each creates its own thread.
Source : demo03-served-agents.ipynb b and demo04-two-agents-over-a2a.ipynb ; build/measurements-06.md ; langgraph_api/api/a2a.py, handle_message_send, handle_tasks_get, _to_spec_format and _resolve_history_scope. These response claims describe completed tasks on 0.16.0, not every possible task state. historyScope task selects the requested task ; it does not select the latest task or limit the model input history.
-->

---

# Two Agents over A2A

- Two processes use ports 2124 and 2125 and separate storage
- The coordinator looks up the specialist UUID and posts JSON-RPC
- The notebook prints both cards and the stored exchange
- Each server allocates its own task id
- A follow-up sends a new message with the same `contextId`

> `demo04 · two-agents-over-a2a`

<!-- NOTES:
The coordinator sleeps 1/COURSE_RPS between the remote call and its own model call because each server has its own rate limiter. Failures raise. The follow-up uses the legacy method message/send so the room can see the unwrapped, lowercased task. History lengths differ only after a second turn in the same context.
Source : demo04-two-agents-over-a2a.ipynb a, coordinator_graph source and stored exchange ; build/measurements-06.md. Both servers reuse one context UUID but maintain separate thread state. The next completed-task follow-up omits taskId.
-->

---

# Event Systems

- A stream is an observation of a run
- `updates` carries the values a node returned
- A namespace names the subgraph that produced the update
- Custom events report progress to stream consumers
- A custom event does not update graph state

<!-- NOTES:
Source : demo05-events-and-synchronisation.ipynb a and b ; langgraph/pregel/main.py, stream ; langgraph/config.py, get_stream_writer, in installed langgraph 1.2.15. Custom writes are stream observations, not state-channel writes.
-->

---

# Subgraph Streaming

- `version="v2"` yields a dict with `type`, `ns` and `data`

```python
for part in graph.stream(
    {"part_no": "CE-CF-02"},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    print(part["ns"], part["data"])
```

- A non-empty `ns` marks the child node
- The parent update contains the keys the child returned

> `demo05 · events-and-synchronisation`

<!-- NOTES:
Checked on langgraph 1.2.15. The child namespace is the node name plus a generated id, so do not treat the id as stable. v2 is the stream() version; v3 is stream_events.
Source : demo05-events-and-synchronisation.ipynb a, event outputs ; langgraph/pregel/main.py, stream version v2 ; build/measurements-06.md. The child result also includes its retained part_no input ; it is not restricted to the lookup node's finding update.
-->

---

# v3 Projections

- `stream_events(version="v3")` returns a `GraphRunStream`
- The caller drives the run by iterating a projection
- `run.subgraphs` yields a handle as each child starts
- Each child handle exposes a `values` projection
- v3 is experimental in langgraph 1.2.15

<!-- NOTES:
Skippable. The warning is LangChainBetaWarning from Pregel.stream_events. SubgraphRunStream.path is a tuple, status moves from started to completed, and run.output is the parent state. Consume the child inside the discovery loop; projections are single-consumer. Source : langgraph/stream/run_stream.py in 1.2.15.
Source : demo05-events-and-synchronisation.ipynb a ; langgraph/stream/run_stream.py, GraphRunStream and SubgraphRunStream, and langgraph/pregel/main.py, stream_events. Child iteration drives the root pump too ; consuming children within discovery is the demo pattern, not a required parent/child scheduling barrier.
-->

---

# Custom Events

- `get_stream_writer` publishes a value beside the state update

```python
writer = get_stream_writer()
writer({"event": "lookup-started", "part_no": state["part_no"]})
return {"finding": finding}
```

- The stream asks for `custom` and `updates`
- The custom payload is not written into state

> `demo05b · custom-events`

<!-- NOTES:
Checked on langgraph 1.2.15. get_stream_writer returns a callable inside a graph run. Calling it outside a runnable context raises RuntimeError. The demo prints events from stream().
Source : demo05-events-and-synchronisation.ipynb b ; langgraph/config.py, get_stream_writer ; build/measurements-06.md. The slide snippet abbreviates lookup_with_events ; finding is the inventory lookup result.
-->

---

# State Broadcasting

- One node publishes a snapshot on a shared key
- Seller and buyer both read that key
- Each returns its own observation
- `operator.add` collects the observations
- The snapshot is the value published before the readers run

> `demo05c · broadcast-channel`

<!-- NOTES:
Skippable if the afternoon is short. The channel is one graph run. It is not a broker, and a branch does not see another branch's in-progress write. A real stock movement still needs a current authorised read. Say that in the room; the slide states the snapshot rule.
Source : demo05-events-and-synchronisation.ipynb c ; langgraph/pregel/main.py, Pregel bulk-synchronous execution description ; build/measurements-06.md.
-->

---

# Synchronization

- A join lists the nodes it waits for
- `defer=True` holds a node until other pending nodes finish
- The collector checks that parts and manuals both reported
- An incomplete set raises before `collected` is returned

```python
builder.add_edge(["parts", "manuals"], "collect")
```

- The alternative uses separate edges and a deferred collector :

```python
builder.add_node("collect", collect, defer=True)
builder.add_edge("parts", "collect")
builder.add_edge("manuals", "collect")
```

> `demo05d · fan-in-and-barriers`

<!-- NOTES:
Both forms are in demo05 d. The manuals branch is one node deeper than parts, so a premature collect would see a partial list. defer waits for the longer branch. Checked on langgraph 1.2.15: add_node defer=False is the default.
Source : demo05-events-and-synchronisation.ipynb d, join_graph and collect ; langgraph/graph/state.py, add_edge and add_node defer, in installed langgraph 1.2.15. The snippet lists two independent alternatives ; the plain join uses a list edge, while the deferred collector has separate incoming edges.
-->

---

# Conflict Resolution

- One owner can run agents with opposing goals
- Yair's crew post puts a seller bot beside a buyer bot
- Yair calls the pair "a conflict of interest i've chosen to ignore"
- Those bots share one computer and the same browser logins
- Code settles the seller's and buyer's proposals

<!-- NOTES:
Quote with permission given 13 October 2026. Source : build/research-2026-10.md section 5, Yair @finebutwhy, public post. No stable URL was recorded in the research file; do not invent one. The seller and buyer here are proposals against Veenhaven stock. Nothing is sent and the database is not updated. "Nothing gets sent without my ok" is the approval gate, which module 07 owns.
Source : build/research-2026-10.md section 5, Yair @finebutwhy public post and permission record ; demo06-conflicts.ipynb and demo07-buyer-and-seller.ipynb. The visible quote matches the research text verbatim.
-->

---

# Conflicting Writes

- Two nodes may write the same key in one step
- An unreduced key accepts one value per step
- A second value raises `InvalidUpdateError`
- A list with `operator.add` keeps both proposals
- The conflict stays visible for the settlement step

> `demo06 · conflicts`

<!-- NOTES:
The error text on langgraph 1.2.15 starts "At key 'decision': Can receive only one value per step." The demo prints that first line. Seller proposes sell and buyer proposes retain for CE-CF-02. No model call in this section.
Source : demo06-conflicts.ipynb a ; langgraph/channels/last_value.py, LastValue.update ; build/measurements-06.md.
-->

---

# Voting

- Independent roles vote on one proposal
- Each vote keeps the role, the action and the reason
- The reserve is a policy input supplied with the facts
- A majority is a count over the returned votes
- Shared evidence can make the votes agree for the same reason

> `demo06b · voting`

<!-- NOTES:
Roles are inventory, workshop and procurement. The proposal sells four CE-CF-02 from stock 6 with reserve 4, which would leave stock below the reserve. The model may still vote sell. Read the reasons. Do not treat a unanimous vote as a measured property of the model.
Source : demo06-conflicts.ipynb b, voter, votes and counts ; build/measurements-06.md. Independence means separate invocations with role prompts ; the shared model and evidence do not make their errors statistically independent.
-->

---

# Judge and Tie-Break

- A fixed tie supplies one sell vote and one retain vote
- The judge records an action and a reason
- Code selects the majority and retains stock on a tie

```python
chosen = "sell" if sell_votes > retain_votes else "retain"
if chosen == "sell" and available - quantity < reserve:
    return "retain"
```

- A tie resolves to retain
- A majority that breaks the reserve is overridden

> `demo06c · judge-and-tie-break`

<!-- NOTES:
The judge call can go either way. The printed rule results are deterministic: the tied pair retains because of the tie, and two sell votes for a quantity that breaks the reserve also retain. Say that the reason is evidence and the return value is the rule.
Source : demo06-conflicts.ipynb c, resolve and printed results ; build/measurements-06.md. Code selects the majority with retain on tie before checking a proposed sale against the reserve. The model judge is a separate demonstration ; its output does not feed resolve.
-->

---

# Seller and Buyer

- Seller proposes a quantity to release
- Buyer proposes a quantity to keep
- Settlement keeps at least the reserve
- Retention is the greater of the reserve and the buyer's quantity
- The sale is capped by the seller's quantity and the remaining surplus
- The result records `external_action` as false

> `demo07 · buyer-and-seller`

<!-- NOTES:
CE-CF-02 stock is 6 at Rietpoort, price 420 euro, name traction cooling fan. The reserve 4 is made up for the policy. Quantities come from the model and will vary. The settlement numbers are a function of those proposals. No row in service.db is updated.
Source : demo07-buyer-and-seller.ipynb a, propose and settle ; build/measurements-06.md. The buyer request is capped at available stock before applying the reserve. The shown stock is above the reserve ; this example does not replenish an already deficient reserve.
-->

---

# Least Privilege

- Each agent receives the tool for its own draft
- `ToolRuntime` carries the principal into the tool
- The published tool schema contains `quantity` only
- `authorise` rejects the other role's operation
- Shared browser logins expose the same authenticated services

> `demo07b · least-privilege-per-agent`

<!-- NOTES:
The lethal trifecta, as used in the research notes: private data, untrusted content, and an outbound action. Shared browser logins put all three on every bot in the crew. The credential labels in the demo are synthetic. Production isolation still needs separate identities and a check at the downstream service. A prompt or a hidden schema does not provide that check. The model usually calls the one tool it has; if it answers without the tool, the explicit authorise denial still prints.
Source : demo07-buyer-and-seller.ipynb b, tool schemas and denial ; langchain/tools/tool_node.py, ToolRuntime re-export ; build/research-2026-10.md section 5. Shared browser sessions expose their authenticated services ; this does not imply access to every unrelated credential on the computer.
-->

---

# Summary : Agent Communication

- Message passing sends a selected payload ; shared state shares keys
- Handoffs cross graphs with `Command` and `Command.PARENT`
- Agent Protocol and A2A connect agents across processes
- MCP exposes tools an agent can call
- Event systems stream subgraphs, v3 projections and custom events
- State broadcasting publishes one snapshot for every reader
- Conflict resolution keeps both writes, then applies a vote, a judge or a tie rule
- Synchronization joins branches with fan-in and deferred nodes
- Least privilege gives each agent its own credentials and tools

<!-- NOTES:
Source : demo01 through demo07 in notebooks/06-agent-communication/ ; build/measurements-06.md ; installed langgraph 1.2.15, langgraph-api 0.16.0, langchain 1.4.5 and deepagents 0.7.24 implementations cited on the preceding slides.
-->
