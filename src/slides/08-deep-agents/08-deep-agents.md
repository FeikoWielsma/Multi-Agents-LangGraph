---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Deep Agents
---

# What is an agent harness?

- An agent harness is the code around the model loop :
  - It stores files, offers tools and decides when a run stops
  - The model still chooses the next tool call
- `create_agent` is a small harness on the LangGraph runtime
- Deep Agents is a larger harness on `create_agent` :
  - Files, delegation, skills, memory and context limits ship together
  - The caller still owns the task, the tools and the permissions

<!-- NOTES:
Timing : about 150 minutes for this module, including ten demos. Capstone stage 4 sits in the rest of the morning. This is a planning allowance, not a measured duration.
Open with the difference between a loop the application wrote and a loop a package assembled. Module 05 built the patterns by hand ; this morning packages them.
Source : deepagents 0.7.24 package description, read 14 October 2026.
-->

---

# Framework, runtime, harness

- Three layers sit under one Deep Agent :
  - LangChain supplies the model, the tools and agent middleware
  - LangGraph runs the graph, the checkpointer and the store
  - Deep Agents adds files, the `task` tool and the context policy
- The pin is `deepagents` 0.7.24, on `langchain` 1.4.5 and `langgraph` 1.2.15
- The same patterns from module 05 are still visible in the middleware stack

<!-- NOTES:
Skippable if the room already has the three names straight from day 1. Do not spend time on install.
-->

---

# The agent loop

```python
plain = create_agent(llm, tools=[part_stock])
result = plain.invoke(ask(STOCK_TASK), LIMIT)
```

- The loop is model, tool, model
- One stock lookup on `openai/gpt-6-luna` :
  - `part_stock` ran once
  - 2 model calls, 194 input tokens, 45 output tokens
- The answer named 6 fans at Rietpoort
- The callback recorded 0 malformed tool calls

> `demo01 · deep-agent-from-scratch`

<!-- NOTES:
Port : ARI510 10 Deep Agents from Scratch and demo29. The four steps are create_agent, todos, files, then a task tool. Measured 14 October 2026, COURSE_RPS=0.07, reasoning off. ARI510 saw a malformed tool call on a weaker model ; record whatever demo01 through demo10 print in build/measurements-08.md.
-->

---

# A todo list

```python
planned = create_agent(
    llm, tools=[part_stock], middleware=[TodoListMiddleware()])
```

- `TodoListMiddleware` adds `write_todos`
- The list records intended work :
  - The run wrote one item, called `part_stock`, then marked it completed
  - The middleware does not enforce that order
- The same lookup cost more context :
  - 4 calls and 5502 input tokens
  - The plain agent used 2 calls and 194 input tokens

> `demo01b · a-todo-list`

<!-- NOTES:
The token jump is the middleware prompt, measured on this one question. Do not generalise it to every task. A completed todo is a claim ; the tool result is the evidence.
-->

---

# Files in state

```python
class ScratchState(AgentState):
    files: Annotated[dict[str, str], merge_files]
```

- Several tools write `files`, so the reducer merges dicts
- `write_note` returns a short confirmation :
  - The body stays under `files`
  - The message list does not have to carry it
- The lookup saved `/stock.md` and answered 6 fans at Rietpoort
- 3 model calls, 4160 input tokens, 0 malformed tool calls

> `demo01c · files`

<!-- NOTES:
The scratch files are plain strings. The harness later stores FileData dicts from create_file_data. Say that before demo03 so the two shapes do not get mixed up.
-->

---

# A task tool

```python
@tool
def task(description: str) -> str:
    """Delegate a parts lookup."""
    return answer(worker.invoke(ask(description), LIMIT))
```

- The worker is its own `create_agent` call, with its own messages
- The parent receives the final sentence :
  - The worker's tool was `part_stock`
  - The parent's tools were `task` and `write_note`
- 5 model calls, 4438 input tokens, 0 malformed tool calls
- Intermediate tool results stayed in the worker trace

> `demo01d · subagents`

<!-- NOTES:
This is the subagents pattern from module 05, written as one tool. The harness version of task is the next notebook. Isolation is the point : the parent does not see the SQL-shaped tool result, only the sentence.
-->

---

# create_deep_agent

```python
packaged = create_deep_agent(model=llm, tools=[part_stock])
```

- Default tools in 0.7.24 :
  - `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`
  - `execute` and `task`
- `write_todos` is absent until `TodoListMiddleware` is passed
- No caller prompt and no harness profile :
  - The authored system prompt is empty
  - `BASE_AGENT_PROMPT` has been deprecated since 0.7.0
  - Tool schemas and middleware fragments still reach the model
- The stock lookup called `part_stock` and `write_file` :
  - 3 model calls, 6272 input tokens, 91 output tokens
  - `todos` stayed empty, and the callback recorded 0 malformed tool calls

> `demo02 · create-deep-agent`

<!-- NOTES:
Verified against the installed graph : those nine tools, no write_todos. The empty authored prompt is the default when system_prompt is omitted and no harness profile matches. The counted stock lookup in the notebook passes a one-line system prompt, so the 6272 input tokens are not an empty-prompt run. BASE_AGENT_PROMPT remains as a deprecated attribute until 0.9.0. Passing model=None is also deprecated and would build claude-sonnet-4-6 ; every demo passes llm.
Source : deepagents/graph.py in 0.7.24.
-->

---

# Planning with write_todos

```python
planner = create_deep_agent(
    llm, tools=[part_stock], middleware=[TodoListMiddleware()])
```

- Planning is opt-in on this pin
- Three Codex harness profiles are the built-in exception :
  - `openai:gpt-5.1-codex`, `openai:gpt-5.2-codex`, `openai:gpt-5.3-codex`
  - Each profile adds `TodoListMiddleware` because its prompt talks about todos
- `openai/gpt-6-luna` matches no harness profile, so the demo passes the middleware itself
- A completed item is still a claim ; the tool result is the check
- That lookup used 4 calls and 13290 input tokens, with 0 malformed tool calls

> `demo02b · write-todos`

<!-- NOTES:
The Codex profile source is deepagents/profiles/harness/_openai_codex.py. Our ChatOpenAI instance reports provider openai and identifier openai/gpt-6-luna. Lookup found no profile on 14 October 2026.
-->

---

# The virtual filesystem

```python
inputs = {**ask("Read /manual.md and report the first action for F-CE-110."),
          "files": {"/manual.md": create_file_data(page)}}
```

- A path such as `/manual.md` names a backend file
- The notebook directory has no `manual.md` after the read
- `read_file` accepts `offset` and `limit` for a window of lines
- The seeded page is the CE-12 error-code manual

> `demo03 · the-filesystem`

<!-- NOTES:
create_file_data returns content, encoding and timestamps. The scratch demo stored a bare string ; say so if someone diffs the two files keys.
-->

---

# Offloading large results

- The default tool-result limit is 20000 tokens
- The demo lowers `tool_token_limit_before_evict` to 600 :
  - 31 manuals are 18795 characters on disk
  - The tool result was 19626 characters and was saved under `/large_tool_results/`
- The model saw the path and a preview, then reported 2 sources
- The printed length is the check ; the preview is too short to count the files

> `demo03b · offloading-large-results`

<!-- NOTES:
31 Markdown files under data/demo-world/manuals, 18795 characters, counted 14 October 2026. The notebook prints the tool result at 19626 characters. The eviction notice is _TOO_LARGE_TOOL_MSG in the pin.
-->

---

# State backend

```python
state_agent = create_deep_agent(
    model=llm, backend=StateBackend(), checkpointer=InMemorySaver())
```

- `StateBackend` is the default
- Files for a thread live in that thread's graph state
- The checkpointer returns them on the next turn of the same thread
- A second `thread_id` starts without those files
- The memory checkpointer ends when the process ends

> `demo04 · backends`

<!-- NOTES:
Durability of the checkpointer is module 09. Here the point is the scope : one thread, one process.
-->

---

# Filesystem backend

```python
disk = FilesystemBackend(root_dir=disk_root, virtual_mode=True)
```

- `virtual_mode=True` maps `/note.md` to a file under `root_dir`
- A path with `..` or `~`, or a path outside the root, raises `ValueError`
- The message from this pin is `Path traversal not allowed`
- Those rules cover the file tools
- A shell command is outside this check, which demo05 takes up

> `demo04b · filesystem`

<!-- NOTES:
Probed 14 October 2026 : FilesystemBackend.read("/../pyproject.toml") raised ValueError, Path traversal not allowed. The demo root is under notebooks/08-deep-agents/workspace/, gitignored.
-->

---

# Store backend

```python
shared = StoreBackend(
    store=store, namespace=lambda _runtime: ("veen-service", "user-a"))
```

- This pin requires the `namespace` callback
- Files under one namespace are visible to later invokes that use it
- A second namespace reads the same path as missing
- `InMemoryStore` keeps the rows until the process exits
- A durable store would keep them across processes ; this demo does not start one

> `demo04c · store`

<!-- NOTES:
StoreBackend(namespace=...) is required. An empty namespace raises ValueError. Wildcards in a component are rejected. The namespace here ignores runtime and returns a constant pair, which is enough to show sharing and isolation.
-->

---

# Composite backend

```python
mixed = CompositeBackend(
    default=StateBackend(), routes={"/memory/": shared})
```

- The longest matching prefix selects the backend
- `/memory/policy.md` is stored on the route as `/policy.md`
- A path with no matching prefix stays on the default, here state
- The file tools apply `permissions` ; a direct backend call skips them

> `demo04d · composite`

<!-- NOTES:
Prefix stripping is CompositeBackend in 0.7.24. permissions are documented on FilesystemMiddleware, and the create_deep_agent docstring says direct backend use does not apply them.
-->

---

# Permissions

```python
rules = [
    FilesystemPermission(operations=["write"], paths=["/reports/**"], mode="allow"),
    FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
]
```

- The first matching rule wins
- `mode` is `allow`, `deny` or `interrupt`
- An operation is `read` or `write`
- No matching rule means the call proceeds
- A subagent inherits the list, or replaces it with its own `permissions`

> `demo05 · permissions-and-execution`

<!-- NOTES:
Order is the whole example. If the deny-all rule is declared first, the /reports/ allow never runs. interrupt mode needs a checkpointer and installs HumanInTheLoopMiddleware. Subagent permissions replace the parent list ; they do not append.
-->

---

# The interpreter

```python
from langchain_quickjs import CodeInterpreterMiddleware
interpreter = CodeInterpreterMiddleware(
    ptc=[ticket_rows], subagents=False, mode="turn",
    memory_limit=16 * 1024 * 1024, timeout=2,
    max_ptc_calls=2, max_result_chars=1200)
analyst = create_deep_agent(model=llm, middleware=[interpreter])
```

- The model writes JavaScript in the `eval` tool
- `tools.ticketRows({})` loads ticket JSON through an allowed Python tool
- Filtering and summing run inside QuickJS ; only the result returns to the model
- Depot D01 tickets without parts total 4 tickets and 7.5 hours, matching Python
- QuickJS has no built-in host filesystem, network or process API
- An exposed tool still runs with the host's permissions

> `demo05b · the-interpreter`

<!-- NOTES:
Installed deepagents[quickjs] 0.7.24 and langchain-quickjs 0.3.9, inspected 14 October 2026. The import is from langchain_quickjs, not deepagents. Demo05 prints the model's generated JavaScript, the eval result and a Python Decimal check. The raw CSV rows enter JavaScript through PTC, without a parent tool message containing those rows. The notebook supplies a task-specific system prompt in addition to the wiring shown here. The read-only loader is an explicit BaseTool in ptc, so it need not appear in the static model tool list. Sandbox APIs are distinct from the still-registered execute tool. StateBackend does not provide shell isolation. Sources : installed middleware.py, _ptc.py and _repl.py ; https://docs.langchain.com/oss/python/deepagents/interpreters.
-->

---

# Interpreter limits

- Limits apply to different parts of the run :
  - `memory_limit` bounds the QuickJS heap
  - `timeout` counts VM execution time ; host calls can take longer
  - `max_ptc_calls` caps `tools.*` calls in one `eval`
  - `max_result_chars` truncates result and console output separately
- REPL state persists by `mode` :
  - `thread` across turns, `turn` within one turn, `call` for one invocation
- PTC calls bypass per-tool parent approval :
  - Gate `eval` or put approval in the called agent

<!-- NOTES:
Defaults inspected with inspect.signature and source on langchain-quickjs 0.3.9 : 64 MiB, 5 seconds VM time, 256 PTC calls, 4000 characters per result/stdout block, mode thread, subagents True, 32 simultaneous subagents per REPL. Demo05 lowers the limits. The package README calls the timeout wall-clock, but the installed docstring explicitly excludes time outside the VM. max_ptc_calls does not count top-level task dispatches. PTC host tools bypass the normal ToolNode/HITL path ; to gate an individual host tool, keep it out of PTC and call it normally. With thread mode, deployments that distrust their checkpointer can set snapshot_signing_key to authenticate persisted REPL state. No secret belongs in notebook output.
-->

---

# A local shell

```python
local = LocalShellBackend(
    root_dir=SHELL, virtual_mode=True, inherit_env=False)
```

- `execute` runs the host shell with `root_dir` as the working directory
- `virtual_mode` still confines the file tools to that directory
- `execute` can read and write outside it
- The command `echo veenhaven` returned `veenhaven`, exit code 0
- `inherit_env=False` leaves the process environment out of the command
- `SHELL` is `notebooks/08-deep-agents/workspace/shell/`
- `workspace/` is gitignored, so the demo's files stay out of the course tree

> `demo05c · a-local-shell`

<!-- NOTES:
Say the why out loud : virtual_mode is not a sandbox for the shell. The source docstring on LocalShellBackend says commands run with the user account and can reach any path. inherit_env=False is so the command process does not receive COURSE_API_KEY. Re-run on this Windows machine at COURSE_RPS=0.1 : echo veenhaven returned exit code 0, and the final answer also said veenhaven. The earlier run retold it as veen haven ; do not promise that model error. The package recommends human approval beside this backend ; interrupt_on is demo09.
-->

---

# Memory in AGENTS.md

```python
agent = create_deep_agent(model=llm, memory=["/AGENTS.md"])
```

- Each path is loaded at the start of the run
- The text is appended to the system prompt
- The file is Markdown ; HTML comments are removed before injection
- Several sources are concatenated in the order given
- Skill bodies stay out of that prompt until a skill is read or pinned

> `demo06 · memory-and-skills`

<!-- NOTES:
The vest rule is only in the seeded AGENTS.md, so an answer that names it was loaded from memory. If the model calls tools anyway, read the tool list with the room. MemoryState.memory_contents is private.
Source : deepagents/middleware/memory.py, agents.md spec linked from that module.
-->

---

# Skills

```yaml
name: safety-briefing
description: Use when asked for safety rules before a depot visit.
```

- `skills=["/skills/"]` scans child folders for `SKILL.md`
- `name` must match the folder : lower case, digits and single hyphens, at most 64 characters
- The prompt receives the name and the description
- The instructions below the frontmatter stay in the file until `read_file`
- Two sources with the same name : the later source wins

> `demo06b · skills`

<!-- NOTES:
Port : ARI510 10 Skills and Memory in Deep Agents. The three-rule briefing is our wording for the bus depot, not a copy of the Academy lab. Frontmatter limits in the pin : description 1024 characters, compatibility 500, file size 10 MB.
-->

---

# Tools bound to skills

- The 7 October 2026 skills change is in this pin :
  - `metadata.include_tools` is a space-separated list of tool names
  - Those tools are passed to `SkillsMiddleware`
  - A listed tool stays off the model request until the skill is read, or named in `pinned_skills`
- `pinned_skills` on `invoke` appends each skill body, then clears the list
- Set `skills_metadata` to `None` and the next run reads the files again

```yaml
metadata:
  include_tools: order_fan
```

> `demo06c · tools-bound-to-skills`

<!-- NOTES:
Source : LangChain blog "Revamping Skills in Deep Agents", 7 October 2026, as summarised in build/research-2026-10.md, and SkillsMiddleware in 0.7.24. include_tools is a space-separated string. A YAML list or a comma warns, and a list is then coerced with str(), which does not match tool names. The demo uses spaces. order_fan is absent from the static tool map. Label resolvers exist on SkillsMiddleware as a callable tools argument ; the demo uses the list form.
-->

---

# Dict subagents

```python
parts = {"name": "parts", "description": "Stock and location for one part.",
         "system_prompt": "Use part_stock.", "tools": [part_stock]}
team = create_deep_agent(model=llm, subagents=[parts])
```

- `task` takes `description` and `subagent_type`
- The default `mode` is `isolated` : the worker's messages are the description
- A `general-purpose` subagent is added when the caller did not pass that name :
  - It is offered the parent's tools
  - A harness profile can set `GeneralPurposeSubagentProfile(enabled=False)`

> `demo07 · subagents`

<!-- NOTES:
Print the task description lines in the demo so the room sees general-purpose next to parts. Isolated message counts are the short lists in the callback. Compare them with fork on the following slide.
-->

---

# CompiledSubAgent

```python
compiled = {"name": "manuals-graph",
            "description": "A compiled agent for one error code.",
            "runnable": manuals_graph}
```

- `runnable` is any graph whose state includes `messages`
- The harness does not wrap it in filesystem, skills or summarisation middleware
- The parent receives the last assistant text
- A non-empty `structured_response` is sent instead, as JSON
- `interrupt_on` from the parent is not copied onto this runnable

> `demo07b · compiled-subagent`

<!-- NOTES:
This is how a module 05 workflow becomes a worker without being rewritten as a dict. The demo's runnable is create_agent with fault_guidance, which is enough to show the wrapper. A custom StateGraph needs the messages key or task cannot read the result.
-->

---

# Fork mode

- `mode="fork"` is experimental in 0.7.24
- The worker receives the parent messages, then the task description
- Its `system_prompt` is appended to the prompt it inherited
- A fork cannot declare `skills`
- A fork that calls `task` is refused ; the refusal text tells it to finish the work itself
- The fork run used 8752 input tokens ; the compiled run used 4375
- The task description left out F-CE-110
- The answer was still to check the traction cooling fan

```python
forked = {"name": "manuals-fork", "description": "Looks up the error already named.",
          "tools": [fault_guidance], "mode": "fork"}
```

> `demo07c · fork-mode`

<!-- NOTES:
Beta warning is on the SubAgent docstring. The 8752 and 4375 figures are callback totals for each run, parent plus worker, measured 14 October 2026. The fork's task description did not name F-CE-110. Message counts were [2, 3, 5, 4] on the fork run and [2, 2, 4, 4] on the compiled run.
-->

---

# The general-purpose subagent

- The built-in name is `general-purpose`
- The pin's description offers research, file search and multi-step tasks
- It is inserted when no subagent uses that name
- `enabled=False` on `GeneralPurposeSubagentProfile` stops the insertion
- With no synchronous subagent left, `create_deep_agent` does not register `task`
- Async subagents use a different middleware and stay available either way

<!-- NOTES:
Skippable if demo07's printed tool description already made this concrete. Async subagents are module 09 ; name them and move on. Source : GENERAL_PURPOSE_SUBAGENT and create_deep_agent in 0.7.24.
-->

---

# Dynamic subagents

- Dynamic subagents dispatch configured workers from JavaScript, in beta
- The agent writes the fan-out and combines the returned objects :

```javascript
const codes = ["F-CE-110", "F-CE-305"];
const schema = {type: "object", properties: {
  error_code: {type: "string"}, action: {type: "string"}
}, required: ["error_code", "action"]};
const found = await Promise.all(codes.map(code => task({
  description: "First action for " + code,
  subagentType: "manuals",
  responseSchema: schema
})));
JSON.stringify(found)
```

- `responseSchema` returns structured values for declarative subagents
- `max_subagent_concurrency=2` caps simultaneous dispatches per REPL
- The Python comparison puts the dispatch loop in the application

> `demo08 · dynamic-subagents`

<!-- NOTES:
Course code, with shapes inspired by the Academy delegation notes. No Academy code. Demo08 first runs two plain workers from Python, then asks a Deep Agent to generate one eval using Promise.all/map. The slide factors the model's inline responseSchema into a variable ; it describes an object with error_code and action. The team is configured in Python, while the model writes the dispatch logic. Top-level task is separate from tools.* ; ptc=["task"] raises ValueError. JavaScript uses subagentType, label and responseSchema ; the underlying Python task tool uses subagent_type. Dynamic response schemas work with dict subagents and are rejected for CompiledSubAgent. task inside eval skips parent interrupt_on per dispatch ; gate eval, set subagents=False or configure approval in the worker. The concurrency limit is not a total task budget, and max_ptc_calls does not count task. Sources : installed langchain_quickjs _subagent.py and _repl.py ; https://docs.langchain.com/oss/python/deepagents/dynamic-subagents.
-->

---

# Recursive language models

- Zhang, Kraska and Khattab, MIT CSAIL, arXiv 2512.24601 :
  - A long input stays in an environment the model inspects from code
  - The model is called on the pieces, and the pieces can be split again
- The paper reports inputs on the order of 100 times the context window, on its tasks
- Zhang later describes two harness families :
  - One keeps the trajectory in the prompt
  - One orchestrates with code and sub-calls
- These 31 manuals fit in one call :
  - One prompt used 5121 input tokens and 20 output tokens
  - Three calls used 5192 input tokens, and the largest used 2010
- QuickJS loads the chunks through PTC and calls the same model as a reader :
  - The root writes the dispatch script and receives compact findings
  - The complete chunks stay out of the root's model requests
  - Five calls used 15983 input tokens ; the largest reader used 2199

> `demo08b · splitting-a-long-input`

<!-- NOTES:
Paper : arxiv.org/abs/2512.24601, v3 11 May 2026, via build/research-2026-10.md. The 100-times claim is that note's "about two orders of magnitude", on the paper's tasks, not on our manuals. Do not quote the Latent Space transcript unless you have just checked the page ; the paraphrase is the interview of 2 October 2026, latent.space/p/rlm. Prime Intellect : primeintellect.ai/blog/rlm, 1 January 2026. Completion run on 14 October 2026, COURSE_RPS=0.1 : whole prompt 5121 input and 20 output tokens ; Python split 5192 input, largest call 2010. The split returned NONE for chunk 2 even though it contains F-CE-110 ; chunk 1 still supplied the correct final action. QuickJS loads the three chunks through tools.manualChunks and sends each derived chunk to a compiled reader using the same model. Root requests contained no complete chunk, checked by async inspection middleware. Five calls used 15983 input, 207 output ; root calls 5055 and 5241 input, readers 1947, 2199 and 1541. Both relevant chunks returned the first action and 80-percent replacement condition in that run. The largest root call is 5241, so this demonstration does not lower the largest overall prompt versus 5121. The corpus fits ; harness overhead raises the total. This is one level of the RLM idea, not the paper's recursive benchmarks or context-window scale. Compiled readers reject dynamic responseSchema. Notebook-level await ainvoke keeps host calls and shared model clients on the notebook loop.
-->

---

# Orchestration shapes

- Many units of work, and a count known at run time, fit a loop in code :
  - Classify and act : one label selects one specialist
  - Fan-out and synthesise : one call per unit, then one combined answer
  - Adversarial verification : a second pass challenges the first
  - Generate and filter : keep the candidates that pass a check
  - Tournament : compare candidates and keep a winner
  - Loop until done : repeat until a condition, with an explicit cap
- A handful of fixed roles stays a dict of subagents
- The cap is the stopping rule for loop until done

<!-- NOTES:
Skippable when the morning is behind. The names follow the Academy delegation lesson ; the definitions are ours. Module 05 already used generate-and-filter and maker-checker. Point back there instead of re-teaching them.
-->

---

# interrupt_on

```python
gated = create_deep_agent(
    model=llm, interrupt_on={"write_file": True}, checkpointer=InMemorySaver())
gated.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config, version="v2")
```

- The pause is `HumanInTheLoopMiddleware` inside the harness
- A decision is `approve`, `edit`, `reject` or `respond`
- The graph needs a checkpointer, and resume continues the same thread
- A declarative subagent inherits the map unless it sets `interrupt_on` itself
- A `CompiledSubAgent` does not inherit it
- `FilesystemPermission` with `mode="interrupt"` builds the same pause for matching paths

> `demo09 · control`

<!-- NOTES:
Resume shape matches module 07 : {"decisions": [{"type": "approve"}]}. One decision per pending action, in order. The write must not have run while the interrupt is pending ; the demo prints the files at that moment.
-->

---

# Summarisation

- The default stack includes summarisation middleware
- Evicted messages are appended to `/conversation_history/{session}.md`
- `state["messages"]` keeps the original log ; the model sees the summary
- This model publishes no profile, so the default trigger is 170000 tokens and the keep window is 6 messages
- The demo replaces that middleware with a trigger of 3 messages so one lookup crosses it
- `compact_conversation` comes from `SummarizationToolMiddleware`, which the default stack does not add

> `demo09b · summarisation`

<!-- NOTES:
compute_summarization_defaults on the course ChatOpenAI returned trigger ("tokens", 170000), keep ("messages", 6), because profile is None. A model whose profile includes max_input_tokens gets fraction 0.85 and keep 0.10. The demo passes truncate_args_settings=None so the visible event is the summary, not argument clipping.
-->

---

# Context limits

- Three mechanisms run before a full summary :
  - A tool result over 20000 tokens is evicted to the filesystem
  - A human message over 50000 tokens is evicted the same way
  - Old `write_file` and `edit_file` arguments can be clipped at a lower threshold
- The summary call uses the agent model
- Fraction triggers apply when `max_input_tokens` is on the model profile
- `openai/gpt-6-luna`, constructed as `ChatOpenAI` for this course, has `profile is None`

<!-- NOTES:
Defaults from FilesystemMiddleware.__init__ and compute_summarization_defaults, 0.7.24. The 600-token demo in the filesystem notebook is a lowered tool limit, not the production default. Say that if someone copies it into a project.
-->

---

# Profiles

- Profiles are a beta API in two registries :
  - A provider profile changes how `resolve_model` builds the chat model
  - A harness profile changes prompts, tool visibility and extra middleware after that
- Built-in harness keys include the three Codex specs and Claude Haiku 4.5, Sonnet 4.6 and Opus 4.7
- Lookup for our instance uses provider `openai` and identifier `openai/gpt-6-luna`
- No key matches, so the profile is empty :
  - There is no base prompt and no system-prompt suffix
  - There are no excluded tools and no extra middleware
- Registering a profile is how a deployment would opt this model into planning or a shorter `task` list

<!-- NOTES:
Printed from _harness_profile_for_model on 14 October 2026. Keys also include several Nemotron routes. Provider profiles exist for openai, openrouter and nvidia ; we pass an already built ChatOpenAI, so the provider profile's constructor kwargs are not applied. Beta : deepagents.profiles docstring.
-->

---

# Deep Agents and the patterns

| Harness feature | Module 05 pattern |
| --- | --- |
| `write_todos` | One agent ; the plan is state |
| Skills, `include_tools` | Skills, with tools scoped to the file |
| `task`, isolated | Subagents |
| `mode="fork"` | The worker sees the parent history |
| `CompiledSubAgent` | A custom workflow behind one tool |
| Fan-out in Python | A custom workflow ; the loop is code |
| `interrupt_on` | An approval gate on a tool |

- One desk question, both builders :
  - Graph : 33 lines, 7 calls, 919 input tokens
  - Deep Agent : 8 lines, 6 calls, 11165 input tokens
  - Both named 6 fans at Rietpoort and the cooling-fan check

> `demo10 · deep-agent-or-graph`

<!-- NOTES:
Measured 14 October 2026, COURSE_RPS=0.07. The graph is the module 05 supervisor shape : structured choice of parts or manuals, then a compose step. The Deep Agent adds general-purpose unless a profile disables it ; the prompt names parts and manuals. Lines are inspect.getsource on the two builders, excluding the shared tools. Both completeness checks were true. The token gap is the harness prompt and tool schemas, not a longer answer.
-->

---

# The Claude Agent SDK

- The Agent SDK runs Claude Code's agent loop in the application's process
- The library includes file tools, a shell, subagents, skills, memory, permissions, sessions, hooks and MCP
- Python and TypeScript are the supported libraries
- The Client SDK calls the Claude API, and the application writes the tool loop
- Managed Agents run a hosted harness, with a cloud sandbox or a self-hosted sandbox
- Deep Agents is the harness in this course's process, on LangGraph, with the course model

<!-- NOTES:
Source : https://docs.anthropic.com/en/docs/claude-code/sdk , Agent SDK overview, fetched 14 October 2026. The page also points at code.claude.com/docs. Branding rule on that page : products may say Powered by Claude and may not present themselves as Claude Code. One slide only ; do not tour the SDK.
-->

---

# Codex

- The Codex SDK starts and resumes a local Codex thread
- TypeScript package `@openai/codex-sdk` requires Node.js 18 or later
- Python package `openai-codex` talks to the local app server over JSON-RPC
- `thread.run` continues the thread ; a thread id resumes an older one
- Sandbox presets on the Python SDK :
  - `read_only` reads files
  - `workspace_write` writes inside the workspace and configured roots
  - `full_access` runs without those filesystem restrictions
- Deep Agents keeps the loop in-process and takes the model the caller built

<!-- NOTES:
Source : https://developers.openai.com/codex/sdk , fetched 14 October 2026. The page's sample model name was gpt-6.1-sol ; do not treat that as our course model. The removed codex mcp-server binary is mentioned there ; skip it unless asked. Our Codex harness profiles are a different thing : prompt and todo defaults inside Deep Agents for three older Codex model specs.
-->

---

# The Academy course

- Introduction to Deep Agents, from LangChain Academy, is a free follow-up
- Six modules cover building, the execution environment, context, delegation, local deployment and Managed Deep Agents
- The public repo at `github.com/langchain-ai/lca-deepagents` has no licence
- This course keeps its own wording, its own examples and the Veenhaven data
- Their code pin is `deepagents` 0.7.0 ; this room is on 0.7.24

<!-- NOTES:
Structure notes are in build/academy-deepagents-notes.md, read 13 October 2026. Do not open their lesson pages and paste. Managed Deep Agents and async subagents return in module 09. If time is gone, this slide plus the summary are the close.
-->

---

# Summary : Deep Agents

- A harness packages files, skills, memory, subagents and context limits on `create_agent`
- Version 0.7 leaves the base prompt and `write_todos` to the caller, unless a profile adds them
- File tools, permission rules and `LocalShellBackend` are the execution environment in this pin
- Skills load on demand ; `include_tools` hides a tool until the skill is in context
- Isolated subagents see the task ; fork mode also sees the parent messages
- A long input can be split in code ; `interrupt_on` and summarisation bound a long run

<!-- NOTES:
Close by pointing at capstone stage 4 : the same desk as a Deep Agent, compared with stage 3. Exercises exercise08 and exercise09 are the lead's, optional in the course map. If a number on an earlier slide disagrees with the notebook, trust the notebook and build/measurements-08.md.
-->
