---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Production Deployment
---

# Production Agent Services

- Agent services need operational controls :
  - An HTTP API with threads, runs and streaming
  - Durable checkpoint storage shared by workers
  - Evaluation and monitoring on real traffic
  - Cost, concurrency and security controls
- Agent Server serves LangGraph graphs and Deep Agents
- Veenhaven Bus exposes stock lookup and fault diagnosis graphs
- The service desk preserves conversation state across requests

<!-- NOTES:
Source : build/plan.md module 09 and build/course-map.md module 09 ; https://docs.langchain.com/langsmith/agent-server ; demos 01, 02, 05, 07 and 08 provide the Veenhaven examples and operational controls.
Timing : Wednesday afternoon, after Deep Agents. Use the committed notebook outputs for the slide block ; allow separate time for exercises and the capstone. Live delivery timing is unmeasured. Cut Managed Deep Agents, DeltaChannel and the LangSmith trainer demo first when time is short.
Port : ARI510 11 Production Deployment, refocused on Agent Server, async subagents and multi-agent evaluation. Stack pin : langgraph 1.2.15, deepagents 0.7.24, agentevals 0.0.9.
-->

---

# LangGraph API

- Agent Server exposes the LangGraph API over HTTP
- Core resources :
  - Assistants : a configured graph and its defaults
  - Threads : durable conversation state
  - Runs : one execution of an assistant on a thread
- The same API backs `langgraph dev`, self-hosted Agent Server and LangSmith Deployment
- Clients use `langgraph-sdk` ; Studio is a browser client of the same API

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/agent-server ; installed langgraph-sdk 0.4.7 client.py resource classes ; demo01. Studio and hosting use the documented Agent Server API.
Website outline term : LangGraph API. Source : docs.langchain.com Agent Server / LangGraph Platform concepts.
-->

---

# Agent Server Resources

- An assistant binds a `graph_id` from `langgraph.json` to runtime defaults
- A thread holds checkpointed state across runs
- A run applies input to an assistant on a thread and returns status and results
- Background runs support join, cancel and stream
- Follow-ups reuse the same thread id so prior messages remain available

<!-- NOTES:
Source : Installed langgraph-sdk 0.4.7 client.py AssistantsClient, ThreadsClient and RunsClient ; demo01 c ; https://docs.langchain.com/langsmith/agent-server.
demo01 c exercises assistants.search, threads.create, runs.wait, runs.list and threads.get_state.
-->

---

# langgraph.json

- The server loads graphs from a project configuration file :

```json
{
  "dependencies": ["."],
  "graphs": {
    "service": "./graphs.py:service",
    "researcher": "./graphs.py:researcher",
    "supervisor": "./graphs.py:supervisor"
  },
  "env": "../../.env"
}
```

- Each entry points at a compiled graph export
- The server supplies checkpointing ; exported graphs omit a private checkpointer
- Dependencies install into the server environment from the project folder

> `demo01 · agent-server`

<!-- NOTES:
Source : Installed langgraph-cli 0.4.33 config.py ; demo01 a generated configuration ; https://docs.langchain.com/langsmith/agent-server (graph exports and server-injected checkpointer). This example uses compiled exports ; factories are also supported.
Port : ARI510 The Local Agent Server. langgraph.json is written by the notebook and is gitignored under notebooks/.
-->

---

# langgraph dev and Studio

- Local development starts with :

```bash
uv run langgraph dev --no-browser --port 2134
```

- Studio opens against the server base URL in the browser
- EU accounts pass `--studio-url https://eu.smith.langchain.com`
- `/ok` reports readiness before the first client call
- Async subagents need concurrent run slots : `--n-jobs-per-worker`

> `demo01b · langgraph-dev-and-studio`

<!-- NOTES:
Source : Installed langgraph-cli 0.4.33 dev --help verifies every displayed flag ; langgraph-api 0.16.0 api/meta.py supplies /ok ; demo01 b. Ports and EU Studio selection are executed settings recorded in measurements-09.md.
Classroom demos use ports 2134 and 2135. Other modules may use different ports in the same checkout.
-->

---

# Threads and Runs in Practice

- `assistants.search` lists the registered graphs
- `threads.create` gives the stock conversation a thread id
- `runs.wait` returns the stock lookup result
- A follow-up on the same thread can refer to CE-CF-02
- `runs.list` and `threads.get_state` show saved history
- The SDK is the integration surface for application code

> `demo01c · threads-and-runs`

<!-- NOTES:
Source : demo01 c executed output ; installed langgraph-sdk 0.4.7 client.py assistants.search, threads.create, runs.wait, runs.list and threads.get_state. Follow-up recall is observed on Luna, not guaranteed for arbitrary prompts.
-->

---

# Streaming to Clients

- Clients consume server-sent events through the SDK stream
- Common stream modes :
  - `messages` / `messages-tuple` : model chunks with node metadata
  - `updates` : completed node writes
  - `values` : full state after each step
- `stream_subgraphs=True` includes nested graph events
- Clients display chunks before the run finishes

> `demo02 · serving-in-practice`

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/streaming ; installed langgraph-sdk 0.4.7 schema.py StreamMode and client.py runs.stream ; demo02 a. Displaying chunks early is a UI capability ; no latency comparison was measured.
Port : ARI510 Streaming over HTTP, moved onto Agent Server SSE instead of a custom FastAPI loop. Website outline term : streaming.
-->

---

# Stream Modes and Subgraphs

- `langgraph_node` identifies the model node for client filtering
- `stream_subgraphs=True` includes specialist events
- A list of stream modes requests tokens and node updates together
- `threads.get_state` reads the saved state after the stream ends

<!-- NOTES:
Source : demo02 a prints langgraph_node metadata and namespaced subgraph events ; installed SDK runs.stream accepts a list of stream modes and stream_subgraphs ; threads.get_state reads the checkpoint. https://docs.langchain.com/langsmith/streaming.
-->

---

# Double-Texting and Concurrency

- `multitask_strategy` controls a second run on a busy thread
- `reject` returns HTTP 409 while the first run occupies the thread
- `enqueue` waits for the current run, then starts
- `interrupt` stops the current run and retains its saved state
- `rollback` stops the current run and removes its checkpoints
- Provider quotas and worker capacity both bound concurrency

> `demo02b · double-texting`

<!-- NOTES:
Source : Installed langgraph-sdk 0.4.7 schema.py MultitaskStrategy and client.py ; demo02 b executes reject (HTTP 409) and enqueue. https://docs.langchain.com/langsmith/double-texting ; interrupt and rollback semantics are documentation-backed, not separately demonstrated here.
Installed langgraph-sdk multitask_strategy values exercised : reject and enqueue.
-->

---

# Persistence Backends

- Production Agent Server persists thread checkpoints in a database
- Local `langgraph dev` uses on-disk development storage under `.langgraph_api`
- PostgreSQL is the default production checkpoint backend
- Retention policies follow product and compliance requirements
- A Store holds application memory across threads

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/agent-server (persistence and Store) ; demo02 c prints local .langgraph_api files. PostgreSQL is the default, not the only configurable checkpoint backend. Retention is an application design recommendation.
Website outline : persistence backends, checkpoint storage. Module 03 already taught InMemorySaver, SqliteSaver and PostgreSQL as concepts.
-->

---

# Checkpoint Storage and TTLs

- Shared checkpoint storage supports multiple worker processes
- TTL policies delete expired threads or prune older checkpoints
- Backups and access controls apply to thread data as to any customer store
- Development storage survives a local restart and is not a production database

> `demo02c · persistence-across-restarts`

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/configure-ttl ; demo02 c restart equality. TTL is not universally an idle timer : delete expiry does not refresh with activity ; keep_latest refreshes after runs or state updates. Backups and access controls are operational recommendations.
demo02 c stops and restarts langgraph dev in the same directory and checks message equality before a follow-up.
-->

---

# DeltaChannel

- `DeltaChannel` is beta in LangGraph 1.2.15
- Checkpoints store writes and periodic snapshots for reducer channels
- Replay applies ancestor writes to reconstruct accumulated state
- Incremental storage limits repeated writes of accumulated values
- Reducers must be deterministic and invariant to write batching

<!-- NOTES:
Source : Installed langgraph 1.2.15 channels/delta.py DeltaChannel docstring and implementation : beta, ancestor-write replay, periodic snapshots, deterministic batching-invariant reducer. build/research-2026-10.md section 3 records the release. Storage sizing was not measured in this module.
Skippable. Point back to module 03 DeltaChannel demo. No new measurement claimed here.
-->

---

# Async Subagents

- An `AsyncSubAgent` targets any Agent Protocol server
- Co-deployed graphs omit `url` and use in-process ASGI transport
- The parent must run asynchronously on Agent Server for ASGI transport
- Tools on the parent :
  - `start_async_task`, `check_async_task`, `update_async_task`
  - `cancel_async_task`, `list_async_tasks`
- Remote servers pass `url` and optional `headers`

> `demo03 · async-subagents`

<!-- NOTES:
Source : Installed deepagents 0.7.24 middleware/async_subagents.py AsyncSubAgent and _ClientCache ; build/research-2026-10.md section 4 ; demo03. https://docs.langchain.com/oss/python/deepagents/async-subagents. These are Agent Protocol targets ; URL omission selects ASGI transport.
Research section 4 and deepagents async-subagents docs. On 0.7.24 AsyncSubAgent fields are name, description, graph_id, optional url, headers, mode. Local ASGI needs an async parent entrypoint such as ainvoke ; Agent Server satisfies that. The executed local demo uses --n-jobs-per-worker 8 ; the CLI default is 10. This is a tested setting, not a minimum worker requirement.
-->

---

# Async Task Lifecycle

- `start_async_task` launches a background run and returns a task id
- `check_async_task` reads current status and results
- `update_async_task` interrupts the current run and starts a new run on its thread
- `cancel_async_task` stops a held or running task
- `list_async_tasks` reports tracked tasks, optionally filtered by status
- Updates retain the task id and replace the run id

<!-- NOTES:
Source : Installed deepagents 0.7.24 middleware/async_subagents.py _build_start_tool, _build_check_tool, _build_update_tool, _build_cancel_tool and _build_list_tool ; demo03 executed all five. update uses multitask_strategy="interrupt" on the existing thread.
Skippable detail slide for the five tools. Measured in demo03 against co-deployed supervisor and researcher graphs.
-->

---

# Co-deployed Graphs

- Supervisor and worker graphs ship in one `langgraph.json`
- The supervisor is a Deep Agent with an `AsyncSubAgent` entry
- The worker is an ordinary compiled graph with a `messages` key
- The parent addresses the worker by `graph_id`
- Veenhaven Bus delegates stock research to the `researcher` graph

<!-- NOTES:
Source : demo03 and notebooks/09-production-deployment/graphs.py supervisor and researcher exports ; installed deepagents AsyncSubAgent graph_id field and ASGI client path. Co-deployment does not require one process in a scaled deployment.
-->

---

# Firstmate Orchestration

- `firstmate` coordinates coding agents through processes and files
- One first mate dispatches each task to a crewmate in its own git worktree
- The orchestrator dispatches, watches, steers and cancels tasks
- State lives on disk ; a watcher wakes the orchestrator on events
- Separate worktrees isolate each coding agent's changes

<!-- NOTES:
Source : build/research-2026-10.md section 5 firstmate snapshot, 13 October 2026 ; https://github.com/kunchenguid/firstmate. Process/file state, watcher and worktree claims come from that repository research ; no live firstmate run in this module.
Skippable bridge slide. Plan : the same shape outside LangGraph. Research 2026-10 section 5 ; firstmate github.com/kunchenguid/firstmate, about 7.9K stars on 13 October 2026. Trainer demo is module 10 demo05.
-->

---

# A2A on Agent Server

- Every assistant exposes `/a2a/{assistant_id}` where `assistant_id` is a UUID
- The agent card lives at `/.well-known/agent-card.json?assistant_id=...`
- Binding : A2A v1.0 JSON-RPC, send, stream, get, cancel and list tasks
- `contextId` identifies the Agent Server thread
- State must include a `messages` key
- `assistants.search` resolves graph names to assistant UUIDs

> `demo04 · a2a-on-agent-server`

<!-- NOTES:
Source : Installed langgraph-api 0.16.0 api/a2a.py routes, known_methods, UUID validation and contextId-to-thread mapping ; demo04 executed card discovery and SendMessage. build/research-2026-10.md section 3 ; https://docs.langchain.com/langsmith/server-a2a. A2A protocolVersion 1.0 is distinct from the JSON-RPC envelope version 2.0.
Pointer back to module 06. Research 2026-10 section 3. On langgraph-api 0.16.0 graph names are rejected ; resolve the UUID with assistants.search first. demo04 discovers the Deep Agent card and calls the stock graph through A2A on the same server.
-->

---

# Deployment Options

- Self-hosted Agent Server : your process, your database, your network
- LangSmith Deployment : managed Agent Server from the same `langgraph.json`
- Local `langgraph dev` matches the API surface used in deployment
- Operations ownership, region and compliance determine the hosting choice

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/agent-server and its hosting options ; installed langgraph-cli configuration and demo01. API compatibility does not establish production durability or performance for langgraph dev. Hosting criteria are design recommendations.
Website outline : deployment, cloud deployment.
-->

---

# Managed Deep Agents

- Hosted runtime in LangSmith for the Deep Agents harness
- Public beta ; the service runs on US LangSmith Cloud
- An agent is a folder : instructions, skills, subagents, tools
- CLI : `mda dev` locally, `mda deploy` to LangSmith
- The beta SDK is not open source
- The October plan records Plus at about $39 per seat per month

<!-- NOTES:
Source : build/research-2026-10.md section 3 and build/plan.md Settled on 13 October, Managed Deep Agents decision. https://www.langchain.com/blog/introducing-managed-deep-agents and https://docs.langchain.com/langsmith/python/managed-deep-agents-cli ; dated public beta claims include US hosting, folder structure, mda dev/deploy and SDK source availability. mda is a separate SDK, absent from the course environment. The approximately $39 price is the dated plan figure, not a current quote ; no deployment executed.
Skippable. Slide only per plan decisions. Sources : Introducing Managed Deep Agents ; public beta blog ; research-2026-10 section 3. Do not run mda deploy in class without a US account and paid plan.
-->

---

# Scaling Strategies

- Stateless API processes share thread state through PostgreSQL
- Long runs belong in workers ; clients poll or subscribe
- Local concurrency uses `--n-jobs-per-worker`
- Production concurrency uses `N_JOBS_PER_WORKER`
- Provider quotas bound model requests across all workers
- More workers add run capacity within database and provider limits

<!-- NOTES:
Source : https://docs.langchain.com/langsmith/agent-server ; installed langgraph-cli 0.4.33 dev --help and langgraph-api 0.16.0 config/__init__.py N_JOBS_PER_WORKER. CLI flag is local development ; environment variable is the production setting. Scaling is architecture guidance, not a throughput benchmark.
Port : ARI510 Scalability Considerations. Website outline term : scaling.
-->

---

# Evaluating a Multi-Agent System

- Four levels, from outside in :
  - Final response : correctness and completeness
  - Single step : tool selection and arguments
  - Trajectory : tool-call sequence and evidence
  - Multi-turn : completion of the conversation goal
- Specialist scores isolate errors before synthesis
- A correct specialist result does not guarantee a correct synthesis

<!-- NOTES:
Source : ARI510 11 Production Deployment, Evaluating an Agent ; build/plan.md module 09 ; demo05 compares final answer, trajectory and specialist scores. Four evaluation levels are a teaching taxonomy, not a package default. https://docs.langchain.com/langsmith/evaluate-graph.
Port : ARI510 Evaluating an Agent, extended for multi-agent.
-->

---

# Final Answer Evaluation

- Code scorers check required facts against tool evidence
- Text checks miss false claims and reject valid paraphrases
- Expected stock and depot values come from the database

> `demo05 · evaluating-agents`

<!-- NOTES:
Source : demo05 a stock evidence and code checks against service.db ; ARI510 demo32 port. Regex checks are a smoke test : stock plus depot does not prove the absence of extra false claims. https://docs.langchain.com/langsmith/evaluate-graph.
Port : ARI510 demo32 final answer checks on Veenhaven Bus CE-CF-02.
-->

---

# Trajectory Match

- `agentevals` compares live tool calls with a reference trajectory
- Four match modes on 0.0.9 :
  - `strict` : same message roles and matching calls per message
  - `unordered` : same tool-call coverage across messages
  - `subset` : outputs introduce no calls beyond the reference
  - `superset` : outputs include at least the reference calls
- Strict matching ignores prose and call order within one message

> `demo05b · trajectory-match`

<!-- NOTES:
Source : Installed agentevals 0.0.9 trajectory/match.py, strict.py, unordered.py, subset.py, superset.py and utils.py ; demo05 b. Strict compares message count, role and matching tool calls per message ; it ignores prose and permits call reorder inside one message. Other modes compare tool-call coverage ; arguments match exactly by default. Review probe in measurements-09.md verifies these distinctions.
Verified against agentevals 0.0.9 create_trajectory_match_evaluator.
-->

---

# Trajectory Judge

- `create_trajectory_llm_as_judge` scores a full conversation with a rubric
- Judge input includes the task, tool calls, results and answer
- Human labels calibrate a judge used as a release gate
- Judges inherit model biases ; read the reasoning on a sample

> `demo05c · trajectory-judge`

<!-- NOTES:
Source : Installed agentevals 0.0.9 trajectory/llm.py create_trajectory_llm_as_judge signature ; demo05 c executed rubric and boolean trajectory_accuracy score. https://docs.langchain.com/langsmith/llm-as-judge ; human calibration and reading reasoning are evaluation recommendations.
-->

---

# Specialist and System Evaluation

- Specialist evaluation checks its tools and facts
- System evaluation checks every required fact in the combined answer
- Failures separate into tool coverage, specialist quality and synthesis loss

> `demo05d · each-agent`

<!-- NOTES:
Source : demo05 d executes parts/manuals tool coverage, specialist judges and combined facts ; build/plan.md module 09. The categories are diagnostic guidance, not automatic error classification by agentevals.
-->

---

# A LangSmith Experiment

- The trainer experiment writes a dataset to EU LangSmith
- Code evaluators score a stock fact and `part_stock` coverage
- Account or permission failures are reported ; the local agent still runs
- Online evaluators reuse the same rubrics on sampled production traces

> `demo06 · a-langsmith-experiment`

<!-- NOTES:
Source : demo06 executed EU dataset, experiment, code evaluators and per-example scores ; installed langsmith 0.14.8 Client.evaluate, ExperimentResultRow and EvaluationResult. https://docs.langchain.com/langsmith/evaluate-graph ; online reuse is a design recommendation requiring a production evaluator adapter. Exceptions print only their class, never raw credential-bearing messages.
Trainer demo. LANGSMITH_ENDPOINT must be the EU API. Never print keys.
-->

---

# Monitoring

- Run traces record model inputs, tool calls, results and failures
- LangSmith Trajectories show one chronological view across parent and subagents
- Online evals score a sample of production runs automatically
- Dashboards track cost per run, latency, error rate and judge scores
- Quality-score alerts flag regressions in sampled runs

<!-- NOTES:
Source : build/research-2026-10.md section 3 LangSmith Trajectories ; ARI510 monitoring port ; https://docs.langchain.com/langsmith/observability and https://docs.langchain.com/langsmith/online-evaluations. Cost/token/latency fields depend on integration reporting. Sampled alerts can miss failures ; they do not guarantee detection.
Port : ARI510 Monitoring and Observability plus Trajectories from research section 3 (LangSmith 24-25 September 2026). Website outline term : monitoring.
-->

---

# Cost Optimisation

- Separate model instances support different agent token budgets
- Compact handoffs reduce synthesis input tokens in the stock demo
- Provider prompt caching reuses stable prefixes :
  - Instructions and tools precede changing content
  - Eligibility and retention depend on routing and the provider
- Prompt caching still sends a request ; it is not an application response cache
- Usage reports separate input, cached input and output tokens

> `demo07 · cost`

> `demo07b · prompt-caching`

<!-- NOTES:
Source : demo07 a executed transcript versus summary tokens ; demo07 b executed provider-reported cache reads. build/measurements-09.md records the figures and model. Model-per-agent, prefix ordering and separate token accounting are design guidance ; caching eligibility depends on the provider.
Website outline : cost optimization. Luna may report zero cache reads through OpenRouter ; the notebook states that outcome without promising a saving.
-->

---

# Sandbox Return Channel

- Tool errors return to the agent for recovery
- Error text can contain an injected instruction
- Fixed error codes remove untrusted recovery text
- Application code validates the stock lookup outside the agent
- The reader has no egress tool or secret

> `demo08 · injection-through-an-error`

<!-- NOTES:
Source : demo08 raw error carries an instruction and records a local dummy egress attempt ; fixed-code version removes that payload, omits export_report and performs a validated application lookup. ARI510 demo34 and Academy Deep Agents notes 5.5 ; images/trust-boundaries.svg. No external message is sent ; compliance or refusal in one run is not a security guarantee.
Academy Deep Agents notes 5.5, rewritten in our words. Port spirit of ARI510 demo34 onto a tool error return channel. Figure : images/trust-boundaries.svg. Neither compliance nor refusal in the raw-error demo establishes a security guarantee.
-->

---

# Summary : Production Deployment

- Agent Server serves assistants, threads and runs from `langgraph.json`
- Async subagents delegate background runs to worker graphs
- A2A exposes assistants through a separate protocol endpoint
- Clients stream events and read saved thread state
- Agent Server supports self-hosted and managed deployments
- Evaluations score final answers, trajectories and specialists
- Token measurements guide handoffs and prompt caching
- Error messages cross a trust boundary

<!-- NOTES:
Source : Module 09 demos 01-08 and measurements-09.md ; https://docs.langchain.com/langsmith/agent-server ; build/research-2026-10.md sections 3 and 4. Each summary point is supported by its topic slide and executed demo or cited architecture documentation.
-->
