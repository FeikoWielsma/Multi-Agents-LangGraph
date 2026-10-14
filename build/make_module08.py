"""Build module 08 on deepagents 0.7.24.

Ports the layered harness and workspace examples from ARI510 demos29 and 30.
Academy supplies the topic order only; all bus examples are course code.
"""
import argparse

from nb import code, md, section, write_demo

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--demos", nargs="+", type=int, help="Regenerate only these demo numbers")
SELECTED = parser.parse_args().demos

MODULE = "08-deep-agents"

COMMON = r'''
import json
import sqlite3
import threading
import time
from pathlib import Path

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, FilesystemBackend, StoreBackend, CompositeBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class Counter(BaseCallbackHandler):
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.calls = self.input = self.output = self.invalid = self.errors = 0

    def on_chat_model_start(self, serialized, messages, **kwargs):
        with self.lock:
            self.calls += 1

    def on_llm_end(self, response, **kwargs):
        with self.lock:
            for generations in response.generations:
                for generation in generations:
                    message = getattr(generation, "message", None)
                    usage = getattr(message, "usage_metadata", None) or {}
                    self.input += usage.get("input_tokens", 0)
                    self.output += usage.get("output_tokens", 0)
                    self.invalid += len(getattr(message, "invalid_tool_calls", []) or [])

    def on_llm_error(self, error, **kwargs):
        with self.lock:
            self.errors += 1


counter = Counter()
llm = make_llm(callbacks=[counter], max_tokens=1800, max_retries=0)
metrics = []
LIMIT = {"recursion_limit": 24}
DB = Path(data("demo-world/service.db")).resolve()
MANUALS = Path(data_folder("demo-world/manuals"))
PAGES = {p.name: p.read_text(encoding="utf-8") for p in sorted(MANUALS.glob("*.md"))}
WORKSPACE = (Path.cwd() / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)


def ask(text):
    return {"messages": [HumanMessage(text)]}


def answer(result):
    return str(next(m.content for m in reversed(result["messages"])
                    if isinstance(m, AIMessage) and m.content and not m.tool_calls))


def measured(label, operation):
    counter.reset()
    start = time.perf_counter()
    try:
        return operation()
    finally:
        row = dict(label=label, calls=counter.calls, input_tokens=counter.input,
                   output_tokens=counter.output, malformed=counter.invalid, errors=counter.errors,
                   seconds=round(time.perf_counter() - start, 1))
        metrics.append(row)
        print("metrics :", json.dumps(row))


async def measured_async(label, operation):
    counter.reset()
    start = time.perf_counter()
    try:
        return await operation()
    finally:
        row = dict(label=label, calls=counter.calls, input_tokens=counter.input,
                   output_tokens=counter.output, malformed=counter.invalid, errors=counter.errors,
                   seconds=round(time.perf_counter() - start, 1))
        metrics.append(row)
        print("metrics :", json.dumps(row))


def show(result):
    print("tools :", [m.name for m in result["messages"] if m.type == "tool"])
    print("answer :", answer(result))


@tool
def part_stock(part: str) -> str:
    """Look up stock, storage location and name for a Veenhaven Bus part number."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, name, stock, depot FROM parts WHERE part_no = ?",
                          (part.upper(),)).fetchall()
    return json.dumps(rows)


@tool
def fault_guidance(error_code: str) -> str:
    """Find the manual's meaning, first action and replacement condition for a bus error code."""
    return "\n".join(f"[{name}]\n{line}" for name, text in PAGES.items()
                     for line in text.splitlines()
                     if line.startswith("| " + error_code.upper() + " |")) or "Unknown error code."


STOCK_TASK = "Look up CE-CF-02 stock and location. Answer briefly from the tool."
MANUAL_TASK = "Look up F-CE-110. Give the first action and replacement condition, citing the file."
QUESTION = ("Bus CE12-2021-0117 shows F-CE-110. How many CE-CF-02 cooling fans are in stock, "
            "at which location, and what are the manual's first action and replacement condition? Be brief.")
'''


def demo(number, slug, title, cells):
    if SELECTED is not None and number not in SELECTED:
        return
    write_demo(MODULE, f"demo{number:02d}-{slug}", [
        md(f"# Demo {number:02d} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        *cells,
        md("## Things to try\n\nOptional : we can change the bus task and compare the answer, calls and tokens."),
    ])


demo(1, "deep-agent-from-scratch", "Deep Agent from scratch", [
    section("a · the-loop", "We start with a tool-calling agent on the bus database. We add one harness feature at a time, following ARI510 demo29."),
    code(COMMON),
    code('''
    plain = create_agent(llm, tools=[part_stock])
    result = measured("plain", lambda: plain.invoke(ask(STOCK_TASK), LIMIT))
    show(result)
    '''),
    section("b · a-todo-list", "We add a todo tool and request a plan explicitly. Todos record intended work; they do not enforce the order of tool calls."),
    code('''
    planned = create_agent(llm, tools=[part_stock], middleware=[TodoListMiddleware()])
    result = measured("todos", lambda: planned.invoke(ask(
        "First write a todo, then " + STOCK_TASK + " Mark it completed before answering."), LIMIT))
    show(result)
    print("todos :", result.get("todos"))
    '''),
    section("c · files", "We put files in graph state with a merge reducer. Our write tool returns a short confirmation while the content stays in the files key."),
    code('''
    from typing import Annotated

    def merge_files(old, new):
        return {**(old or {}), **(new or {})}

    class ScratchState(AgentState):
        files: Annotated[dict[str, str], merge_files]

    @tool
    def write_note(path: str, content: str, runtime: ToolRuntime) -> Command:
        """Save a short note in virtual state files."""
        return Command(update={"files": {path: content}, "messages": [
            ToolMessage("Saved " + path, tool_call_id=runtime.tool_call_id)]})

    @tool
    def read_note(path: str, runtime: ToolRuntime) -> str:
        """Read a virtual state file."""
        return runtime.state.get("files", {}).get(path, "Missing file")

    @tool
    def list_notes(runtime: ToolRuntime) -> str:
        """List virtual state files."""
        return json.dumps(sorted(runtime.state.get("files", {})))

    files_agent = create_agent(llm, tools=[part_stock, write_note, read_note, list_notes],
                               state_schema=ScratchState, middleware=[TodoListMiddleware()])
    result = measured("files", lambda: files_agent.invoke(ask(
        STOCK_TASK + " Save the result in /stock.md with write_note, then answer."), LIMIT))
    show(result)
    print("files :", result.get("files"))
    '''),
    section("d · subagents", "We delegate the lookup to an agent with its own messages. The parent receives the final answer and saves it in a file; the worker's intermediate tool results stay out of the parent's messages."),
    code('''
    worker = create_agent(llm, tools=[part_stock], system_prompt="Use part_stock and return compact facts.")
    worker_messages = []

    @tool
    def task(description: str) -> str:
        """Delegate a self-contained Veenhaven Bus parts lookup to the parts worker."""
        result = worker.invoke(ask(description), LIMIT)
        worker_messages.append(result["messages"])
        return answer(result)

    scratch = create_agent(llm, tools=[task, write_note, read_note, list_notes],
                           state_schema=ScratchState, middleware=[TodoListMiddleware()],
                           system_prompt="Delegate lookups with task. Save compact findings with write_note.")
    result = measured("scratch-subagent", lambda: scratch.invoke(ask(
        STOCK_TASK + " Delegate the lookup and save the answer in /stock.md."), LIMIT))
    show(result)
    print("files :", result.get("files"))
    print("worker tools :", [[m.name for m in history if m.type == "tool"] for history in worker_messages])
    '''),
])

demo(2, "create-deep-agent", "create_deep_agent", [
    section("a · defaults", "We replace the hand-built features with the harness. In deepagents 0.7.24 the default tools include files, execute and task; write_todos requires middleware. A state backend cannot execute a shell command."),
    code(COMMON),
    code('''
    packaged = create_deep_agent(model=llm, tools=[part_stock],
        system_prompt="Use the parts tool. Save a short finding in /stock.md, then answer.")
    print("tool schemas :", sorted(packaged.get_graph().nodes["tools"].data.tools_by_name))
    result = measured("default-harness", lambda: packaged.invoke(ask(STOCK_TASK), LIMIT))
    show(result)
    print("files :", sorted(result.get("files", {})))
    print("todos :", result.get("todos"))
    '''),
    section("b · write-todos", "We opt in to planning. The model can revise the list, and completion is still a claim that needs checking against the actual tool results."),
    code('''
    planner = create_deep_agent(model=llm, tools=[part_stock], middleware=[TodoListMiddleware()])
    result = measured("harness-planning", lambda: planner.invoke(ask(
        "Write one todo for this lookup, perform it, mark it completed, then answer. " + STOCK_TASK), LIMIT))
    show(result)
    print("todos :", result.get("todos"))
    '''),
])

demo(3, "the-filesystem", "The filesystem", [
    section("a · virtual-files", "We seed a virtual file in the input state. The model reads a selected range; the path belongs to the backend and does not name a host file."),
    code(COMMON),
    code('''
    agent = create_deep_agent(model=llm)
    inputs = {**ask("Read /manual.md and report the first action for F-CE-110. Cite /manual.md."),
              "files": {"/manual.md": create_file_data(PAGES["ce-12-error-codes.md"])}}
    result = measured("virtual-read", lambda: agent.invoke(inputs, LIMIT))
    show(result)
    print("files :", sorted(result.get("files", {})))
    print("host file :", Path("manual.md").exists())
    '''),
    section("b · offloading-large-results", "We lower the offload threshold for this demonstration. A tool returns all bus manuals; middleware saves the large result and replaces it with a path and preview. The path in that preview is the result to trust. A source count the model reads from the preview can be wrong."),
    code('''
    from deepagents.middleware.filesystem import FilesystemMiddleware
    from langchain.agents.middleware import wrap_model_call

    captured = []

    @wrap_model_call
    def capture_tool_results(request, handler):
        captured.extend(str(m.content) for m in request.messages if m.type == "tool")
        return handler(request)

    @tool
    def all_manuals() -> str:
        """Export all Veenhaven Bus manuals with their source names."""
        return "\\n\\n".join(f"[{name}]\\n{text}" for name, text in PAGES.items())

    backend = StateBackend()
    offloader = create_deep_agent(model=llm, tools=[all_manuals], backend=backend,
        middleware=[FilesystemMiddleware(backend=backend, tool_token_limit_before_evict=600),
                    capture_tool_results])
    result = measured("offload", lambda: offloader.invoke(ask(
        "Call all_manuals once. Report the saved result path and source count from its preview. "
        "Do not read the complete export."), LIMIT))
    show(result)
    print("raw characters :", len(all_manuals.invoke({})))
    print("model tool results :", captured)
    print("saved paths :", sorted(result.get("files", {})))
    '''),
])

demo(4, "backends", "Backends", [
    section("a · state", "We write a file in one thread and read it in a later turn. The checkpointer preserves that thread's state; a new thread starts with separate files."),
    code(COMMON),
    code('''
    state_agent = create_deep_agent(model=llm, backend=StateBackend(), checkpointer=InMemorySaver())
    config = {**LIMIT, "configurable": {"thread_id": "state-a"}}
    first = measured("state-write", lambda: state_agent.invoke(ask(
        "Write /note.md with this text: CE-CF-02 is the traction cooling fan. Then stop."), config))
    second = measured("state-read", lambda: state_agent.invoke(ask("Read /note.md and report its content."), config))
    show(second)
    print("other thread :", state_agent.get_state({"configurable": {"thread_id": "state-b"}}).values)
    '''),
    section("b · filesystem", "We use real files below a virtual root. Path traversal is rejected by the filesystem backend. File paths alone do not restrict a shell."),
    code('''
    disk_root = WORKSPACE / "backends"
    disk_root.mkdir(exist_ok=True)
    disk = FilesystemBackend(root_dir=disk_root, virtual_mode=True)
    (disk_root / "note.md").write_text("CE-CF-02 is the traction cooling fan.", encoding="utf-8")
    disk_agent = create_deep_agent(model=llm, backend=disk)
    result = measured("filesystem", lambda: disk_agent.invoke(ask("Read /note.md and report its content."), LIMIT))
    show(result)
    try:
        print("traversal :", disk.read("/../pyproject.toml"))
    except ValueError as exc:
        print("traversal :", str(exc))
    '''),
    section("c · store", "We supply the namespace callback required by this pin. Different graph threads can share a store namespace; a separate user namespace prevents the other user's file from appearing."),
    code('''
    from langgraph.store.memory import InMemoryStore

    store = InMemoryStore()
    shared = StoreBackend(store=store, namespace=lambda _runtime: ("veen-service", "user-a"))
    print("write :", shared.write("/policy.md", "Briefings are written in English."))
    store_agent = create_deep_agent(model=llm, backend=shared, store=store)
    result = measured("store-new-thread", lambda: store_agent.invoke(ask(
        "Read /policy.md and report its content."), {**LIMIT, "configurable": {"thread_id": "store-b"}}))
    show(result)
    other = StoreBackend(store=store, namespace=lambda _runtime: ("veen-service", "user-b"))
    print("other user :", other.read("/policy.md"))
    '''),
    section("d · composite", "We route /memory/ to the shared store and leave scratch files in state. The route prefix is removed before the store receives the path. InMemoryStore lasts only for this process."),
    code('''
    mixed = CompositeBackend(default=StateBackend(), routes={"/memory/": shared})
    mixed_agent = create_deep_agent(model=llm, backend=mixed, store=store)
    result = measured("composite", lambda: mixed_agent.invoke(ask(
        "Read /memory/policy.md. Save its text in /scratch.md, then answer briefly."), LIMIT))
    show(result)
    print("state files :", sorted(result.get("files", {})))
    print("store files :", shared.ls("/"))
    '''),
])

demo(5, "permissions-and-execution", "Permissions and execution", [
    section("a · permissions", "Write rules are matched in order. A write under /reports/ is allowed, and every other write is denied. A read with no matching rule proceeds."),
    code(COMMON),
    code('''
    from deepagents import FilesystemPermission

    rules = [
        FilesystemPermission(operations=["write"], paths=["/reports/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]
    gated = create_deep_agent(model=llm, permissions=rules, system_prompt=(
        "Use only write_file. Write /scratch.md with the single word fan. "
        "If that call is denied, write /reports/fan.md with the single word fan. Then stop."))
    result = measured("permissions", lambda: gated.invoke(ask(
        "Write the note, using the fallback path if the first write is denied."), LIMIT))
    show(result)
    for message in result["messages"]:
        if message.type == "tool":
            print(message.name, ":", str(message.content)[:240])
    print("files :", sorted(result.get("files", {})))
    '''),
    section("b · the-interpreter", "We attach the QuickJS interpreter and ask the model to write JavaScript that totals ticket hours. A read-only tool loads the rows into the REPL through programmatic tool calling. The rows stay in the environment; only the calculation comes back to the model. We print the generated code and check its result against Python."),
    code('''
    import csv
    import importlib.metadata as metadata
    import xml.etree.ElementTree as ET
    from decimal import Decimal
    from deepagents.backends.protocol import SandboxBackendProtocol
    from langchain_quickjs import CodeInterpreterMiddleware, PTCOption

    with Path(data("demo-world/tickets.csv")).open(encoding="utf-8", newline="") as handle:
        tickets = list(csv.DictReader(handle))

    @tool
    def ticket_rows() -> str:
        """Load all Veenhaven Bus tickets as JSON rows with depot_id, hours and parts_used."""
        return json.dumps(tickets)

    ptc: PTCOption = [ticket_rows]
    interpreter = CodeInterpreterMiddleware(ptc=ptc, subagents=False, mode="turn",
        memory_limit=16 * 1024 * 1024, timeout=2, max_ptc_calls=2, max_result_chars=1200)
    analyst = create_deep_agent(model=llm, middleware=[interpreter], system_prompt=(
        "Use only eval. Load ticket data inside JavaScript with JSON.parse(await tools.ticketRows({})). "
        "Compute from those rows; do not return or print the raw rows. Return the requested JSON "
        "using JSON.stringify as the last expression. Then answer briefly from the result."))
    print("versions :", metadata.version("deepagents"), metadata.version("langchain-quickjs"))
    print("tools :", sorted(analyst.get_graph().nodes["tools"].data.tools_by_name))
    result = await measured_async("quickjs-tickets", lambda: analyst.ainvoke(ask(
        "For depot D01, count tickets and sum hours only where parts_used is empty. "
        "Return JSON with count and hours. In the same JSON add host APIs with "
        "typeof process, typeof require and typeof fetch. Use one eval call."), LIMIT))
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []):
            if call["name"] == "eval":
                print("JavaScript :\\n" + call["args"]["code"])
        if message.type == "tool" and message.name == "eval":
            print("sandbox :", message.content)
            computed = json.loads(ET.fromstring(message.content).text)
    show(result)
    selected = [row for row in tickets if row["depot_id"] == "D01" and not row["parts_used"]]
    expected = {"count": len(selected), "hours": float(sum(Decimal(row["hours"]) for row in selected))}
    print("Python check :", expected)
    assert {key: computed[key] for key in expected} == expected
    '''),
    md("We expose only the ticket loader to JavaScript. `eval` has no built-in host filesystem, network or process API. An exposed Python tool still runs with the host's permissions. The VM timeout covers JavaScript execution; waiting for a host tool can take longer. `execute` remains a separate shell tool, and a state backend does not make that shell a sandbox."),
    section("c · a-local-shell", "LocalShellBackend runs the host shell with the workspace folder as its working directory. virtual_mode confines file tools to that folder and leaves execute unrestricted, so the command is one echo and the process environment is not inherited. The tool result is the command output ; the model's retelling can change the spacing."),
    code('''
    from deepagents.backends import LocalShellBackend

    SHELL = WORKSPACE / "shell"
    SHELL.mkdir(exist_ok=True)
    local = LocalShellBackend(root_dir=SHELL, virtual_mode=True, inherit_env=False)
    print("cwd :", local.cwd)
    print("sandbox :", isinstance(local, SandboxBackendProtocol))
    shell_agent = create_deep_agent(model=llm, backend=local, system_prompt=(
        "Call execute once with exactly this command: echo veenhaven. "
        "Report the output and stop. Do not use another tool."))
    result = measured("local-shell", lambda: shell_agent.invoke(ask("Run the echo."), LIMIT))
    show(result)
    for message in result["messages"]:
        if message.type == "tool":
            print(message.name, ":", str(message.content)[:300])
    '''),
])

demo(6, "memory-and-skills", "Memory and skills", [
    section("a · agents-md", "memory loads AGENTS.md into the system prompt at the start of the run. The vest rule is not in the bus tools, so an answer that names it came from that file."),
    code(COMMON),
    code('''
    remembered = create_deep_agent(model=llm, memory=["/AGENTS.md"],
        system_prompt="Answer from the project memory. Do not call tools.")
    files = {"/AGENTS.md": create_file_data(
        "# Veenhaven service desk\\n\\nBriefings are written in English.\\n"
        "Every visitor wears a high-visibility vest.\\n")}
    result = measured("memory", lambda: remembered.invoke(
        {**ask("What must every visitor wear? One sentence."), "files": files}, LIMIT))
    show(result)
    '''),
    section("b · skills", "A skill is a folder with SKILL.md. The prompt receives the name and description. The instructions stay in the file until the agent reads them. The vest line is required by the skill ; any other rule in the answer is the model's."),
    code('''
    skilled = create_deep_agent(model=llm, skills=["/skills/"], checkpointer=InMemorySaver(),
        system_prompt="When a skill applies, read its SKILL.md and follow it. Do not use the shell.")
    files = {"/skills/safety-briefing/SKILL.md": create_file_data(
        "---\\nname: safety-briefing\\n"
        "description: Use when asked for safety rules before a depot visit.\\n---\\n\\n"
        "List exactly three rules as bullets. Always mention the high-visibility vest.\\n")}
    config = {**LIMIT, "configurable": {"thread_id": "briefing"}}
    result = measured("skills", lambda: skilled.invoke(
        {**ask("Give the depot visit safety briefing."), "files": files}, config))
    show(result)
    print("skills :", [item.get("name") for item in skilled.get_state(config).values.get("skills_metadata") or []])
    '''),
    section("c · tools-bound-to-skills", "metadata.include_tools names tools the skill may use. They stay off the model request until the skill is pinned or its file is read. Setting skills_metadata to None drops the cached index so the next run loads the files again."),
    code('''
    from deepagents.middleware.skills import SkillsMiddleware

    @tool
    def order_fan(part: str) -> str:
        """Place a simulated cooling-fan order and return the confirmation sentence."""
        return "Ordered " + part.upper() + ". This does not change stock."

    skill_backend = StateBackend()
    skill_tools = SkillsMiddleware(backend=skill_backend, sources=["/skills/"], tools=[order_fan])
    bound = create_deep_agent(model=llm, backend=skill_backend, skills=["/skills/"],
        middleware=[skill_tools], checkpointer=InMemorySaver(),
        system_prompt="Follow the pinned skill. Do not write files.")
    static_names = sorted(bound.get_graph().nodes["tools"].data.tools_by_name)
    print("static tools include order_fan :", "order_fan" in static_names)
    files = {"/skills/order-fan/SKILL.md": create_file_data(
        "---\\nname: order-fan\\n"
        "description: Use when asked to order the traction cooling fan.\\n"
        "metadata:\\n  include_tools: order_fan\\n---\\n\\n"
        "Call order_fan with part CE-CF-02. Report the returned sentence and stop.\\n")}
    config = {**LIMIT, "configurable": {"thread_id": "skills"}}
    result = measured("bound-skill", lambda: bound.invoke({
        **ask("Follow the pinned skill."), "files": files, "pinned_skills": ["order-fan"]}, config))
    show(result)
    print("cached skills :", [item.get("name") for item in bound.get_state(config).values.get("skills_metadata") or []])
    bound.update_state(config, {"skills_metadata": None})
    print("after reset :", bound.get_state(config).values.get("skills_metadata"))
    '''),
])

demo(7, "subagents", "Subagents", [
    section("a · dict-subagents", "A dict subagent is isolated. It receives the task description, not the parent messages. create_deep_agent also adds a general-purpose subagent when none is supplied under that name."),
    code(COMMON),
    code('''
    from langchain_core.callbacks import BaseCallbackHandler

    seen = []

    class Sizes(BaseCallbackHandler):
        def on_chat_model_start(self, serialized, messages, **kwargs):
            seen.append(sum(len(batch) for batch in messages))

    llm = make_llm(callbacks=[counter, Sizes()], max_tokens=1800, max_retries=0)
    parts = {"name": "parts", "description": "Looks up stock and location for one part number.",
             "system_prompt": "Use part_stock. Return the stock and location.", "tools": [part_stock]}
    team = create_deep_agent(model=llm, subagents=[parts], system_prompt=(
        "Call task with subagent_type parts. Put the part number in the description. Do not write files."))
    task_tool = team.get_graph().nodes["tools"].data.tools_by_name["task"]
    print("listed :", [line.strip() for line in task_tool.description.splitlines() if line.strip().startswith("- ")])
    seen.clear()
    result = measured("dict-subagent", lambda: team.invoke(ask(
        "How many CE-CF-02 are in stock, and where? Delegate to parts."), LIMIT))
    show(result)
    print("message counts :", seen)
    '''),
    section("b · compiled-subagent", "CompiledSubAgent wraps a graph that already has a messages channel. The parent still calls it through task, and the graph does not inherit the harness middleware."),
    code('''
    manuals_graph = create_agent(llm, tools=[fault_guidance],
        system_prompt="Use fault_guidance. Return the first action and the replacement condition.")
    compiled = {"name": "manuals-graph", "description": "A compiled agent for one bus error code.",
                "runnable": manuals_graph}
    parent = create_deep_agent(model=llm, subagents=[compiled], system_prompt=(
        "Call task with subagent_type manuals-graph and include the error code. Do not write files."))
    seen.clear()
    result = measured("compiled", lambda: parent.invoke(ask(
        "What is the first action for F-CE-110? Delegate to manuals-graph."), LIMIT))
    show(result)
    print("message counts :", seen)
    '''),
    section("c · fork-mode", "mode fork passes the parent messages into the subagent and appends the task description. The description can omit the error code because that code is already in the conversation."),
    code('''
    forked = {"name": "manuals-fork", "description": "Continues this conversation and looks up the error already named.",
              "system_prompt": "Use fault_guidance on the error code in the conversation. Return the first action.",
              "tools": [fault_guidance], "mode": "fork"}
    parent = create_deep_agent(model=llm, subagents=[forked], system_prompt=(
        "Call task with subagent_type manuals-fork. The description is: return the first action. "
        "Do not repeat the error code in the description. Do not write files."))
    seen.clear()
    result = measured("fork", lambda: parent.invoke(ask(
        "Bus CE12-2021-0117 shows F-CE-110. Delegate the first-action lookup."), LIMIT))
    show(result)
    print("message counts :", seen)
    for message in result["messages"]:
        if getattr(message, "tool_calls", None):
            print("calls :", message.tool_calls)
    '''),
])

demo(8, "dynamic-subagents", "Dynamic subagents", [
    section("a · fan-out-in-code", "We first run the application-owned Python loop. Then a Deep Agent writes its own JavaScript fan-out in eval. The script calls the configured manuals subagent once per error code through task and collects both answers. The configured team stays fixed; the script chooses the dispatches."),
    code(COMMON),
    code('''
    worker = create_agent(llm, tools=[fault_guidance],
        system_prompt="Use fault_guidance. Return the first action in one sentence.")
    codes = ["F-CE-110", "F-CE-305"]

    def fanout():
        found = []
        for code in codes:
            found.append(answer(worker.invoke(ask("First action for " + code + "."), LIMIT)))
        return found

    print("Python answers :", measured("python-fanout", fanout))
    '''),
    code('''
    import xml.etree.ElementTree as ET
    from langchain_quickjs import CodeInterpreterMiddleware

    def show_eval(result):
        values = []
        for message in result["messages"]:
            for call in getattr(message, "tool_calls", []):
                if call["name"] == "eval":
                    print("JavaScript :\\n" + call["args"]["code"])
            if message.type == "tool" and message.name == "eval":
                print("sandbox :", message.content)
                values.append(json.loads(ET.fromstring(message.content).text))
        show(result)
        assert values, "The agent must run interpreter code."
        return values[-1]

    manuals = {"name": "manuals", "description": "Finds the first action for a bus error code.",
               "tools": [fault_guidance],
               "system_prompt": "Use fault_guidance once. Return the first action briefly. Do not use files."}
    dispatcher = create_deep_agent(model=llm, subagents=[manuals], middleware=[
        CodeInterpreterMiddleware(mode="turn", timeout=2, max_ptc_calls=2,
                                  max_subagent_concurrency=2, max_result_chars=1600)],
        system_prompt=("Use only eval, with one JavaScript script. Use Promise.all and map to call "
            "top-level task once per supplied error code, subagentType manuals. "
            "Give each dispatch responseSchema for an object with error_code and action, both strings. "
            "Return JSON.stringify of the collected objects as the last expression. Then answer briefly."))
    result = await measured_async("quickjs-fanout", lambda: dispatcher.ainvoke(ask(
        "Run a first-action lookup for F-CE-110 and F-CE-305 using interpreter fan-out. "
        "Each task description must include its error code."), LIMIT))
    found = show_eval(result)
    print("coverage :", sorted(row["error_code"] for row in found))
    assert sorted(row["error_code"] for row in found) == sorted(codes)
    assert all(row["action"] for row in found)
    '''),
    md("The JavaScript API uses `subagentType`, while the normal Python task tool uses `subagent_type`. `responseSchema` gives the script structured objects and is supported by declarative subagents. The concurrency cap limits simultaneous dispatches per REPL. It does not cap the total number of tasks, and `max_ptc_calls` counts `tools.*` calls only. A task inside eval skips the parent's per-task approval; we can gate eval or put approval inside the worker."),
    section("b · splitting-a-long-input", "The manuals stay in a Python variable. One call receives every manual. The other path splits the files in code and calls the model on each third, so no call holds the whole set. We then let the Deep Agent load these chunks into JavaScript and dispatch the same model on each piece. The root sees compact findings while the source text stays in the environment."),
    code('''
    from langchain_core.messages.utils import count_tokens_approximately

    names = sorted(PAGES)
    joined = "\\n\\n".join(f"[{name}]\\n{PAGES[name]}" for name in names)
    chunks = []
    step = (len(names) + 2) // 3
    for start in range(0, len(names), step):
        group = names[start:start + step]
        chunks.append("\\n\\n".join(f"[{name}]\\n{PAGES[name]}" for name in group))
    print("files :", len(names), "characters :", len(joined))
    print("approximate tokens :", count_tokens_approximately([HumanMessage(joined)]),
          [count_tokens_approximately([HumanMessage(chunk)]) for chunk in chunks])

    def flat(message):
        content = message.content
        if isinstance(content, list):
            return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)
        return str(content)

    def whole():
        return flat(llm.invoke("Manuals follow. First action for F-CE-110, one sentence.\\n\\n" + joined))

    def split_calls():
        sizes = []
        found = []
        for index, chunk in enumerate(chunks, start=1):
            before = counter.input
            text = flat(llm.invoke(
                "Excerpt of bus manuals. If F-CE-110 appears, give its first action in one sentence. "
                "Otherwise reply NONE.\\n\\n" + chunk))
            sizes.append(counter.input - before)
            found.append(text)
            print("chunk", index, ":", text[:220])
        print("split input tokens :", sizes, "max :", max(sizes))
        return [text for text in found if "NONE" not in text.upper()]

    print("whole :", measured("whole-prompt", whole))
    print("split :", measured("split-calls", split_calls))
    '''),
    code('''
    from langchain.agents.middleware import wrap_model_call

    usage_rows = []
    root_has_corpus = []

    class UsageRows(BaseCallbackHandler):
        def __init__(self, role):
            self.role = role

        def on_llm_end(self, response, **kwargs):
            for generations in response.generations:
                for generation in generations:
                    usage = getattr(generation.message, "usage_metadata", None) or {}
                    usage_rows.append({"role": self.role, "input": usage.get("input_tokens", 0),
                                       "output": usage.get("output_tokens", 0)})

    @wrap_model_call
    async def inspect_root(request, handler):
        messages = ([request.system_message] if request.system_message else []) + list(request.messages)
        text = "\\n".join(flat(message) for message in messages)
        root_has_corpus.append(any(chunk in text for chunk in chunks))
        return await handler(request)

    @tool
    def manual_chunks() -> str:
        """Load JSON containing three bus-manual text chunks. Use them inside the interpreter."""
        return json.dumps(chunks)

    root_llm = make_llm(callbacks=[counter, UsageRows("root")], max_tokens=1800, max_retries=0)
    reader_llm = make_llm(callbacks=[counter, UsageRows("reader")], max_tokens=1800, max_retries=0)
    reader = create_agent(reader_llm, system_prompt=(
        "Read this excerpt only. If F-CE-110 appears, give its first action and replacement condition "
        "in one sentence. Otherwise reply NONE."))
    environment_agent = create_deep_agent(model=root_llm, subagents=[
        {"name": "reader", "description": "Reads one derived manual chunk.", "runnable": reader}],
        middleware=[CodeInterpreterMiddleware(ptc=[manual_chunks], mode="turn", timeout=2,
                    max_ptc_calls=1, max_subagent_concurrency=1, max_result_chars=1600), inspect_root],
        system_prompt=("Use only eval once. Load JSON.parse(await tools.manualChunks({})) into a variable. "
            "For every chunk call top-level task with subagentType reader and description containing "
            "that chunk plus the F-CE-110 question. This is a compiled reader: do not use responseSchema. "
            "Collect findings with Promise.all and map. Return JSON.stringify of findings only, "
            "never the chunks. Then give a brief answer."))
    result = await measured_async("quickjs-environment", lambda: environment_agent.ainvoke(ask(
        "Find the first action and replacement condition for F-CE-110 across the manual chunks. "
        "Keep the bulk input in the interpreter and delegate one lookup per chunk."), LIMIT))
    findings = show_eval(result)
    print("provider usage :", json.dumps(usage_rows))
    print("root received a complete chunk :", root_has_corpus)
    print("largest root input :", max(row["input"] for row in usage_rows if row["role"] == "root"))
    print("largest reader input :", max(row["input"] for row in usage_rows if row["role"] == "reader"))
    assert len(findings) == len(chunks)
    assert not any(root_has_corpus)
    assert any("80" in text and "fan" in text.lower() for text in findings)
    '''),
    md("We use a compiled reader with the same model and no extra tools. The root writes the orchestration code; the loader puts the input in its environment without a parent ToolMessage containing that input. This is one level of the RLM idea. These manuals fit in a single prompt, so extra harness tokens and calls can outweigh the smaller reader prompts. A reader can miss a relevant passage and return NONE. We compare each printed finding with its source chunk."),
])

demo(9, "control", "Control", [
    section("a · interrupt-on", "interrupt_on pauses before write_file and waits for a decision. Approving resumes the same thread. The write does not run while the interrupt is pending."),
    code(COMMON),
    code('''
    gated = create_deep_agent(model=llm, interrupt_on={"write_file": True}, checkpointer=InMemorySaver(),
        system_prompt="Call write_file once for /note.md with the text fan stock checked. Then stop. Do not use another tool.")
    config = {**LIMIT, "configurable": {"thread_id": "approve-write"}}
    paused = measured("interrupt", lambda: gated.invoke(ask("Write the note."), config, version="v2"))
    print("pending :", len(paused.interrupts))
    print("actions :", paused.interrupts[0].value["action_requests"])
    print("files while paused :", sorted(gated.get_state(config).values.get("files", {})))
    resumed = measured("approved", lambda: gated.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}), config, version="v2"))
    print("pending after approve :", len(resumed.interrupts))
    show(resumed.value)
    print("files :", sorted(resumed.value.get("files", {})))
    '''),
    section("b · summarisation", "This model has no profile, so the harness default waits for 170000 tokens and then keeps 6 messages. We replace that middleware with a 3-message trigger so one short lookup stores the older turn."),
    code('''
    from deepagents.backends.utils import file_data_to_string
    from deepagents.middleware.summarization import SummarizationMiddleware, compute_summarization_defaults

    print("defaults :", compute_summarization_defaults(llm))
    backend = StateBackend()
    tight = SummarizationMiddleware(model=llm, backend=backend, trigger=("messages", 3),
        keep=("messages", 2), truncate_args_settings=None)
    compact = create_deep_agent(model=llm, tools=[part_stock], backend=backend, middleware=[tight],
        system_prompt="Use part_stock once, then answer in one sentence. Do not write files.")
    result = measured("summarise", lambda: compact.invoke(ask(STOCK_TASK), LIMIT))
    show(result)
    print("files :", sorted(result.get("files", {})))
    for path, payload in sorted(result.get("files", {}).items()):
        if "conversation_history" in path:
            print(path, ":", file_data_to_string(payload)[:400])
    '''),
])

demo(10, "deep-agent-or-graph", "Deep Agent or graph", [
    section("a · stage-3-against-stage-4", "One service-desk question goes through a supervisor graph, the module 05 shape, and through a Deep Agent with two subagents. We compare the answer, the calls, the tokens and the lines in each builder."),
    code(COMMON),
    code('''
    import inspect
    import re
    from typing import Literal
    from pydantic import BaseModel, Field
    from langgraph.graph import END, START, StateGraph
    from typing_extensions import TypedDict

    def flat(message):
        content = message.content
        if isinstance(content, list):
            return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)
        return str(content)

    def completeness(text):
        lowered = text.lower()
        return {"stock": bool(re.search(r"\\b(6|six)\\b", lowered)) and "rietpoort" in lowered,
                "action": "fan" in lowered and "airflow" in lowered and bool(re.search(r"\\b(80|eighty)\\b", lowered))}

    class Decision(BaseModel):
        next: Literal["parts", "manuals", "finish"]
        task: str = Field(description="Instruction for the selected worker")

    class TeamState(TypedDict):
        question: str
        findings: dict[str, str]
        next: str
        task: str
        rounds: int
        answer: str

    def build_graph():
        workers = {
            "parts": create_agent(llm, tools=[part_stock], system_prompt="Use part_stock. Return stock and location."),
            "manuals": create_agent(llm, tools=[fault_guidance], system_prompt="Use fault_guidance. Return the first action and replacement condition."),
        }

        def supervise(state):
            if len(state["findings"]) == 2 or state["rounds"] >= 2:
                return {"next": "finish"}
            decision = llm.with_structured_output(Decision).invoke(
                "Choose an unfinished worker. parts owns stock. manuals owns the error code. "
                "Do not repeat a worker.\\n" + state["question"] + "\\nCompleted: " + json.dumps(state["findings"]))
            print("supervisor :", decision.next)
            return {"next": decision.next, "task": decision.task}

        def worker(name):
            def node(state):
                text = answer(workers[name].invoke(ask(state["task"]), LIMIT))
                return {"findings": {**state["findings"], name: text}, "rounds": state["rounds"] + 1}
            return node

        graph = StateGraph(TeamState)
        graph.add_node("supervisor", supervise)
        for name in workers:
            graph.add_node(name, worker(name))
            graph.add_edge(name, "supervisor")
        graph.add_node("finish", lambda state: {"answer": flat(llm.invoke(
            "Answer from these findings only. Keep the numbers.\\n" + state["question"]
            + "\\n" + "\\n".join(state["findings"].values())))})
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", lambda state: state["next"], ["parts", "manuals", "finish"])
        graph.add_edge("finish", END)
        return graph.compile()

    def build_deep():
        parts = {"name": "parts", "description": "Stock and depot location for a part number.",
                 "system_prompt": "Use part_stock. Return stock and location.", "tools": [part_stock]}
        manuals = {"name": "manuals", "description": "First action and replacement condition for an error code.",
                   "system_prompt": "Use fault_guidance. Return the first action and replacement condition.",
                   "tools": [fault_guidance]}
        return create_deep_agent(model=llm, subagents=[parts, manuals], system_prompt=(
            "Call task for parts and task for manuals. Answer in one sentence from their results. Do not write files."))

    print("graph lines :", len(inspect.getsource(build_graph).splitlines()))
    print("deep lines :", len(inspect.getsource(build_deep).splitlines()))
    wide = {"recursion_limit": 30}
    graph_result = measured("graph", lambda: build_graph().invoke(
        {"question": QUESTION, "findings": {}, "rounds": 0, "next": "", "task": "", "answer": ""}, wide))
    print("graph answer :", graph_result["answer"])
    print("graph checks :", completeness(graph_result["answer"]))
    deep_result = measured("deep", lambda: build_deep().invoke(ask(QUESTION), wide))
    show(deep_result)
    print("deep checks :", completeness(answer(deep_result)))
    '''),
])

