"""Build module 04. Ports ARI510 demos11, 12, 21 and 32 onto Veenhaven Bus."""
from nb import code, md, section, write_demo

MODULE = "04-building-agents"

TOOLS = '''
import json
import sqlite3

from langchain.tools import tool

DB = data("demo-world/service.db")


@tool
def bus_info(fleet_no: str) -> str:
    """Look up a Veenhaven bus model and depot by its fleet number."""
    with sqlite3.connect(DB) as conn:
        row = conn.execute(
            "SELECT model, depot_id FROM buses WHERE fleet_no = ?", (fleet_no,)
        ).fetchone()
    return json.dumps(dict(zip(["model", "depot_id"], row))) if row else "Unknown bus"


@tool
def parts_for_model(model: str) -> str:
    """List spare parts, stock and storage depots for a bus model such as CE-12."""
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT part_no, name, stock, depot FROM parts WHERE model = ?", (model,)
        ).fetchall()
    return json.dumps([dict(zip(["part_no", "name", "stock", "depot"], row)) for row in rows])


tools = [bus_info, parts_for_model]
question = {"messages": [("human", "Which door actuator fits bus CE12-2021-0117, and is it in stock? Look up the bus first.")]}
'''

FAKE = '''
from langchain.messages import AIMessage, HumanMessage, ToolCall
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
'''


def demo(number, slug, title, cells, setup=True):
    write_demo(MODULE, f"demo{number:02}-{slug}", [
        md(f"# Demo {number:02} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        *cells,
        md("## Things to try\n\nOptional : change the bus or part identifier and run the example again."),
    ], setup=setup)


demo(1, "react-as-a-graph", "ReAct as a graph", [
    section("a · by-hand", "We build the model and tool nodes ourselves. The bus lookup supplies the model identifier needed by the parts lookup."),
    code(TOOLS),
    code('''
    from langchain.messages import SystemMessage, ToolMessage
    from langgraph.graph import END, START, MessagesState, StateGraph

    bound = llm.bind_tools(tools)
    tool_by_name = {t.name: t for t in tools}
    prompt = SystemMessage("Look up the bus before looking up its parts. Report unknown records. Use the database for stock.")


    def call_model(state: MessagesState):
        return {"messages": [bound.invoke([prompt, *state["messages"]])]}


    def run_tools(state: MessagesState):
        results = []
        for call in state["messages"][-1].tool_calls:
            value = tool_by_name[call["name"]].invoke(call["args"])
            results.append(ToolMessage(value, tool_call_id=call["id"], name=call["name"]))
        return {"messages": results}


    def route(state: MessagesState):
        return "tools" if state["messages"][-1].tool_calls else END


    def final_answer(state: MessagesState):
        return {"messages": [llm.invoke([prompt, *state["messages"],
                                       ("human", "Answer from the available results. State any missing lookup.")])]}


    single = StateGraph(MessagesState)
    single.add_node("agent", call_model)
    single.add_node("tools", run_tools)
    single.add_node("final", final_answer)
    single.add_edge(START, "agent")
    single.add_conditional_edges("agent", route, {"tools": "tools", END: "final"})
    single.add_edge("tools", "final")
    single.add_edge("final", END)
    result = single.compile().invoke(question)
    for message in result["messages"]:
        print(message.type, getattr(message, "tool_calls", None) or message.content)
    '''),
    md("We give the model a fresh turn after each tool result. A single pass may stop with only the bus model, or guess the parts argument before reading the bus lookup. The loop permits the dependent lookup."),
    code('''
    loop = StateGraph(MessagesState)
    loop.add_node("agent", call_model)
    loop.add_node("tools", run_tools)
    loop.add_edge(START, "agent")
    loop.add_conditional_edges("agent", route)
    loop.add_edge("tools", "agent")
    result = loop.compile().invoke(question, {"recursion_limit": 16})
    for message in result["messages"]:
        print(message.type, getattr(message, "tool_calls", None) or message.content)
    print("model calls:", sum(m.type == "ai" for m in result["messages"]))
    '''),
    section("b · toolnode-and-tools-condition", "We replace tool dispatch and routing with the prebuilt components. The model node and the stopping condition stay the same."),
    code('''
    from langgraph.prebuilt import ToolNode, tools_condition

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    graph = builder.compile()
    for update in graph.stream(question, {"recursion_limit": 16}, stream_mode="updates"):
        for node, value in update.items():
            for message in value["messages"]:
                print(node, message.type, getattr(message, "tool_calls", None) or message.content)
    print(graph.get_graph().draw_mermaid())
    '''),
])

demo(2, "create-agent", "create_agent", [
    section("a · create-agent", "We build the same loop from a model and a tool list."),
    code(TOOLS),
    md("We supply the same tools to `create_agent`. The return value is a compiled LangGraph graph, and invocation returns its final state."),
    code('''
    from langchain.agents import create_agent

    agent = create_agent(llm, tools=tools,
                         system_prompt="Look up the bus first. Use the database for stock. Report unknown records.")
    result = agent.invoke(question, {"recursion_limit": 16})
    for message in result["messages"]:
        print(message.type, getattr(message, "tool_calls", None) or message.content)
    print("graph type:", type(agent).__name__)
    print("nodes:", list(agent.get_graph().nodes))
    print("tool schema:", bus_info.args)
    '''),
    section("b · agent-as-a-node", "We put the compiled agent inside a parent graph. Shared message state passes into and out of the agent node."),
    code('''
    from langgraph.graph import END, START, MessagesState, StateGraph


    class VisitState(MessagesState):
        handover: str


    def handover(state: VisitState):
        return {"handover": "Workshop review required. " + str(state["messages"][-1].content)}


    parent = StateGraph(VisitState)
    parent.add_node("parts_agent", agent)
    parent.add_node("handover", handover)
    parent.add_edge(START, "parts_agent")
    parent.add_edge("parts_agent", "handover")
    parent.add_edge("handover", END)
    out = parent.compile().invoke(question)
    print("handover:", out["handover"])
    '''),
    section("c · custom-agent-state", "We extend `AgentState` with a depot and a lookup counter. A model hook adds the depot to the prompt, and a tool reads state through `ToolRuntime`. The runtime argument stays out of the tool schema."),
    code('''
    from langchain.agents import AgentState
    from langchain.agents.middleware import after_model, dynamic_prompt
    from langchain.tools import ToolRuntime
    from typing_extensions import NotRequired


    class DepotState(AgentState):
        depot: str
        model_calls: NotRequired[int]


    @dynamic_prompt
    def depot_prompt(request):
        return f"You assist the workshop at {request.state['depot']}. Use depot_parts for stock."


    @after_model(state_schema=DepotState)
    def count_calls(state, runtime):
        return {"model_calls": state.get("model_calls", 0) + 1}


    @tool
    def depot_parts(runtime: ToolRuntime) -> str:
        """List spare parts and stock at the current workshop depot."""
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT model, part_no, name, stock FROM parts WHERE depot = ?",
                                (runtime.state["depot"],)).fetchall()
        return json.dumps([dict(zip(["model", "part_no", "name", "stock"], row)) for row in rows])


    depot_agent = create_agent(llm, tools=[depot_parts], state_schema=DepotState,
                               middleware=[depot_prompt, count_calls])
    out = depot_agent.invoke({"depot": "Rietpoort", "messages": [
        ("human", "Is a CE-12 door actuator available at my workshop? Use the tool.")]})
    print("depot:", out["depot"])
    print("model calls:", out["model_calls"])
    print("tool schema:", depot_parts.args)
    print("answer:", out["messages"][-1].content)
    '''),
])

demo(3, "middleware-hooks", "Middleware hooks", [
    section("a · middleware-hooks", "We observe the agent lifecycle and the model and tool calls."),
    code(TOOLS),
    md("We log the lifecycle and each model and tool call. Hooks observe or update state, while wrappers control whether the handler runs."),
    code('''
    from langchain.agents import create_agent
    from langchain.agents.middleware import AgentMiddleware, wrap_tool_call


    class Logger(AgentMiddleware):
        def before_agent(self, state, runtime):
            print("agent: start")

        def before_model(self, state, runtime):
            print("model input messages:", len(state["messages"]))

        def after_model(self, state, runtime):
            print("requested tools:", [c["name"] for c in state["messages"][-1].tool_calls])

        def after_agent(self, state, runtime):
            print("agent: end")


    @wrap_tool_call
    def log_tool(request, handler):
        print("tool:", request.tool_call["name"], request.tool_call["args"])
        result = handler(request)
        print("result:", result.content)
        return result


    agent = create_agent(llm, tools=tools, middleware=[Logger(), log_tool],
                         system_prompt="Look up the bus before its parts. Use the database for stock.")
    out = agent.invoke(question, {"recursion_limit": 16})
    print("answer:", out["messages"][-1].content)
    '''),
    md("We keep logging outside the prompt. Logs can contain identifiers and tool data, so we limit access and redact sensitive fields before recording real traffic."),
])

demo(4, "node-failures", "Node failures", [
    section("a · retry-policy", "We inject a transient inventory failure. `max_attempts` includes the initial attempt, and the retry filter selects the exceptions that may repeat."),
    code('''
    from typing_extensions import TypedDict
    from langgraph.graph import END, START, StateGraph
    from langgraph.runtime import Runtime
    from langgraph.types import RetryPolicy


    class LookupState(TypedDict):
        part_no: str
        status: str


    def inventory(state: LookupState, runtime: Runtime):
        attempt = runtime.execution_info.node_attempt
        print("attempt:", attempt)
        if attempt < 3:
            raise ConnectionError("inventory temporarily unavailable")
        return {"status": "inventory available"}


    builder = StateGraph(LookupState)
    builder.add_node("inventory", inventory, retry_policy=RetryPolicy(
        max_attempts=3, initial_interval=0.01, jitter=False, retry_on=ConnectionError))
    builder.add_edge(START, "inventory")
    builder.add_edge("inventory", END)
    print(builder.compile().invoke({"part_no": "CE-DA-03", "status": "pending"}))
    '''),
    section("b · node-timeout", "We run async nodes with run and idle limits. Heartbeats refresh the idle clock, while the run limit remains fixed. Expected timeout exceptions are caught and printed."),
    code('''
    import asyncio
    from langgraph.errors import NodeTimeoutError
    from langgraph.types import TimeoutPolicy


    async def slow_inventory(state: LookupState, runtime: Runtime):
        try:
            await asyncio.sleep(0.5)
            return {"status": "late"}
        finally:
            print("slow node: cancelled or finished")


    async def progressing_inventory(state: LookupState, runtime: Runtime):
        for batch in range(4):
            await asyncio.sleep(0.03)
            runtime.heartbeat()
        return {"status": "completed with heartbeats"}


    async def timed(node, policy):
        builder = StateGraph(LookupState)
        builder.add_node("inventory", node, timeout=policy)
        builder.add_edge(START, "inventory")
        builder.add_edge("inventory", END)
        try:
            print(await builder.compile().ainvoke({"part_no": "CE-DA-03", "status": "pending"}))
        except NodeTimeoutError as exc:
            print("timeout:", exc.kind, "node:", exc.node)


    await timed(slow_inventory, TimeoutPolicy(run_timeout=0.08))
    await timed(slow_inventory, TimeoutPolicy(idle_timeout=0.08, refresh_on="heartbeat"))
    await timed(progressing_inventory, TimeoutPolicy(idle_timeout=0.08, refresh_on="heartbeat"))
    await timed(progressing_inventory, TimeoutPolicy(run_timeout=0.08, idle_timeout=0.08,
                                                    refresh_on="heartbeat"))

    try:
        invalid = StateGraph(LookupState)
        invalid.add_node("inventory", inventory, timeout=0.08)
        invalid.add_edge(START, "inventory")
        invalid.compile()
    except ValueError as exc:
        print("sync timeout:", str(exc).splitlines()[0])
    '''),
    section("c · error-handler", "We route an exhausted failure to a manual queue. The handler receives state and an injected `NodeError`. A failed attempt's state writes are discarded, but external side effects need their own protection."),
    code('''
    from langgraph.errors import NodeError
    from langgraph.types import Command


    def unavailable(state: LookupState, runtime: Runtime):
        print("attempt:", runtime.execution_info.node_attempt)
        raise ConnectionError("inventory unavailable")


    def on_error(state: LookupState, error: NodeError) -> Command:
        print("handler:", error.node, type(error.error).__name__)
        return Command(update={"status": "manual stock check required"}, goto="notify")


    def notify(state: LookupState):
        print("queue:", state["part_no"], state["status"])
        return {}


    builder = StateGraph(LookupState)
    builder.add_node("inventory", unavailable, error_handler=on_error,
                     retry_policy=RetryPolicy(max_attempts=2, retry_on=ConnectionError,
                                              initial_interval=0.01, jitter=False))
    builder.add_node("notify", notify)
    builder.add_edge(START, "inventory")
    builder.add_edge("inventory", END)
    builder.add_edge("notify", END)
    print(builder.compile().invoke({"part_no": "CE-DA-03", "status": "pending"}))
    '''),
    md("We combine an async timeout with the default retry filter and the same recovery handler. Each retry gets a fresh timeout budget, and `NodeTimeoutError` reaches the handler after retries are exhausted."),
    code('''
    async def timed_inventory(state: LookupState, runtime: Runtime):
        print("timed attempt:", runtime.execution_info.node_attempt)
        await asyncio.sleep(0.5)
        return {"status": "late"}


    builder = StateGraph(LookupState)
    builder.add_node("inventory", timed_inventory, timeout=TimeoutPolicy(run_timeout=0.08),
                     retry_policy=RetryPolicy(max_attempts=2, initial_interval=0.01, jitter=False),
                     error_handler=on_error)
    builder.add_node("notify", notify)
    builder.add_edge(START, "inventory")
    builder.add_edge("inventory", END)
    builder.add_edge("notify", END)
    print(await builder.compile().ainvoke({"part_no": "CE-DA-03", "status": "pending"}))
    '''),
], setup=False)

demo(5, "agent-failures", "Agent failures", [
    section("a · tool-errors", "We distinguish an execution failure from a valid empty stock result."),
    code(TOOLS),
    code(FAKE),
    md("We inject a stock-service timeout. Without a handler the run raises. `ToolErrorMiddleware` returns selected execution errors as error messages, which the real model can use to report the unavailable service."),
    code('''
    from langchain.agents import create_agent
    from langchain.agents.middleware import ToolErrorMiddleware


    @tool
    def live_stock(part_no: str) -> str:
        """Read live stock for a spare part number."""
        raise TimeoutError("stock service unavailable")


    fake = FakeToolModel(messages=iter([AIMessage("", tool_calls=[
        ToolCall(name="live_stock", args={"part_no": "CE-DA-03"}, id="stock-1")])]))
    try:
        create_agent(fake, tools=[live_stock]).invoke({"messages": [HumanMessage("Check stock.")]})
    except TimeoutError as exc:
        print("unhandled:", type(exc).__name__)


    def on_error(exc, request):
        if isinstance(exc, TimeoutError):
            return "Stock service unavailable. Do not infer stock. Ask for a manual stock check."
        return None


    safe = create_agent(llm, tools=[live_stock], middleware=[ToolErrorMiddleware(on_error)],
                        system_prompt="Use live_stock for stock. If unavailable, report that and stop.")
    out = safe.invoke({"messages": [("human", "Check stock for CE-DA-03.")]}, {"recursion_limit": 16})
    for message in out["messages"]:
        print(message.type, getattr(message, "status", ""), message.content)
    '''),
    section("b · model-fallback", "We fail the primary model locally, then use the course model as the fallback. This exercises the failure path without sending a request for an invalid model name."),
    code('''
    from langchain.agents.middleware import ModelFallbackMiddleware


    class UnavailableModel(FakeToolModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            print("primary: unavailable")
            raise ConnectionError("injected model outage")


    primary = UnavailableModel(messages=iter([]))
    agent = create_agent(primary, tools=tools, middleware=[ModelFallbackMiddleware(llm)],
                         system_prompt="Use the database for stock. Look up the bus before its parts.")
    out = agent.invoke(question, {"recursion_limit": 16})
    print("fallback answer:", out["messages"][-1].content)
    '''),
    section("c · call-limits", "We script repeated stock calls to expose both limits. Run limits reset per invocation. Thread limits accumulate when state is persisted with a checkpointer."),
    code('''
    from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware


    def repeated_stock():
        return FakeToolModel(messages=iter([
            AIMessage("", tool_calls=[ToolCall(name="bus_info", args={"fleet_no": "CE12-2021-0117"}, id="1")]),
            AIMessage("", tool_calls=[ToolCall(name="bus_info", args={"fleet_no": "CE12-2021-0117"}, id="2")]),
            AIMessage("Finished.")]))


    for middleware in [ModelCallLimitMiddleware(run_limit=1, exit_behavior="end"),
                       ToolCallLimitMiddleware(tool_name="bus_info", run_limit=1, exit_behavior="end")]:
        out = create_agent(repeated_stock(), tools=[bus_info], middleware=[middleware]).invoke(question)
        print("limit:", type(middleware).__name__)
        for message in out["messages"]:
            print(message.type, message.content or getattr(message, "tool_calls", []))
    '''),
])

demo(6, "tracing-with-langsmith", "Tracing with LangSmith", [
    section("a · trainer", "We enable tracing inside this trainer demo only. The endpoint comes from the EU-region `.env` setting, and the surrounding environment keeps its default tracing setting."),
    code(TOOLS),
    code('''
    import os
    import time
    from uuid import uuid4
    from langchain.agents import create_agent
    from langsmith import Client, trace, tracing_context

    PROJECT = "ARI520-module04-building-agents"
    print("project:", PROJECT)
    print("endpoint:", os.getenv("LANGSMITH_ENDPOINT", "not configured"))
    print("default tracing:", os.getenv("LANGSMITH_TRACING", "not configured"))
    agent = create_agent(llm, tools=tools,
                         system_prompt="Look up the bus before its parts. Use the database for stock.")
    out = None
    try:
        if not os.getenv("LANGSMITH_API_KEY") or not os.getenv("LANGSMITH_ENDPOINT"):
            raise RuntimeError("LangSmith key or EU endpoint is missing")
        client = Client(api_url=os.environ["LANGSMITH_ENDPOINT"],
                        api_key=os.environ["LANGSMITH_API_KEY"], timeout_ms=10000)
        list(client.list_projects(limit=1))
        with tracing_context(enabled=True, client=client, project_name=PROJECT):
            with trace("door-actuator-stock", run_type="chain", inputs=question,
                       run_id=uuid4()) as root_run:
                out = agent.invoke(question, {"recursion_limit": 16})
                root_run.end(outputs={"answer": out["messages"][-1].content})
        client.flush()
        project = next(client.list_projects(name=PROJECT, limit=1))
        for attempt in range(3):
            try:
                recorded = await client.runs.retrieve(str(root_run.id), project_id=str(project.id))
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.5)
        print("trace recorded:", recorded.id)
    except Exception as exc:
        print("tracing failed:", type(exc).__name__)
    if out is None:
        with tracing_context(enabled=False):
            out = agent.invoke(question, {"recursion_limit": 16})
    print("answer:", out["messages"][-1].content)
    print("default tracing after:", os.getenv("LANGSMITH_TRACING", "not configured"))
    '''),
    md("We inspect the named project in LangSmith for the model calls, tool arguments, results and timing. If recording fails, the answer still runs and the cell prints the failure type."),
])

TEST_SUPPORT = '''
from contextlib import closing
import sqlite3
from pathlib import Path
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolCall
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import InMemorySaver


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def stock_tool(db):
    @tool
    def check_stock(part_no: str) -> str:
        """Read recorded units in stock for a Veenhaven spare part."""
        with closing(sqlite3.connect(db)) as conn:
            row = conn.execute("SELECT stock FROM parts WHERE part_no = ?", (part_no,)).fetchone()
        return str(row[0]) if row else "Unknown part"
    return check_stock


def scripted(db, *messages):
    return create_agent(FakeToolModel(messages=iter(messages)), tools=[stock_tool(db)],
                        checkpointer=InMemorySaver())


def call(part_no="CE-DA-03", call_id="stock-1"):
    return AIMessage("", tool_calls=[ToolCall(name="check_stock", args={"part_no": part_no}, id=call_id)])
'''

TESTS = '''
import pytest


@pytest.fixture
def db(tmp_path):
    import shutil
    import urllib.request

    here = Path(__file__).resolve().parent
    root = next((p for p in [here, *here.parents] if (p / "data/demo-world/service.db").exists()), None)
    target = tmp_path / "service.db"
    if root:
        shutil.copyfile(root / "data/demo-world/service.db", target)
    else:
        urllib.request.urlretrieve("https://raw.githubusercontent.com/FeikoWielsma/Multi-Agents-LangGraph/main/data/demo-world/service.db", target)
    return target


def test_tool_result_and_call_id(db):
    agent = scripted(db, call(), AIMessage("CE-DA-03 has no stock."))
    out = agent.invoke({"messages": [HumanMessage("Stock of CE-DA-03?")]},
                       {"configurable": {"thread_id": "stock"}})
    results = [m for m in out["messages"] if m.type == "tool"]
    assert len(results) == 1
    assert results[0].content == "0"
    assert results[0].tool_call_id == "stock-1"


def test_unknown_part_is_explicit(db):
    assert stock_tool(db).invoke({"part_no": "UNKNOWN"}) == "Unknown part"


def test_memory_and_thread_isolation(db):
    agent = scripted(db, call(), AIMessage("No stock."), AIMessage("CE-DA-03."), AIMessage("No earlier lookup."))
    config = {"configurable": {"thread_id": "first"}}
    agent.invoke({"messages": [HumanMessage("Stock?")]}, config)
    agent.invoke({"messages": [HumanMessage("Which part?")]}, config)
    saved = agent.get_state(config).values["messages"]
    assert any(m.type == "tool" and m.content == "0" for m in saved)
    other = {"configurable": {"thread_id": "other"}}
    out = agent.invoke({"messages": [HumanMessage("Which part?")]}, other)
    assert [m.type for m in out["messages"]] == ["human", "ai"]
    assert len(agent.get_state(config).values["messages"]) == len(saved)
'''

demo(7, "testing-agents", "Testing agents", [
    section("a · scripted-fake-model", "We script tool calls with `GenericFakeChatModel`. Its `bind_tools` method needs a small subclass for agents with tools. These tests exercise the tool and graph wiring, without testing the real model's choices."),
    code('''
    import shutil
    import urllib.request

    from pathlib import Path
    here = Path.cwd()
    root = next((p for p in [here, *here.parents] if (p / "data/demo-world/service.db").exists()), None)
    DB = here / "service.db"
    if root:
        shutil.copyfile(root / "data/demo-world/service.db", DB)
    elif not DB.exists():
        urllib.request.urlretrieve("https://raw.githubusercontent.com/FeikoWielsma/Multi-Agents-LangGraph/main/data/demo-world/service.db", DB)
    '''),
    code(TEST_SUPPORT),
    code('''
    try:
        plain = GenericFakeChatModel(messages=iter([AIMessage("Hello.")]))
        create_agent(plain, tools=[stock_tool(DB)]).invoke({"messages": [HumanMessage("Stock?")]})
    except NotImplementedError:
        print("plain fake: bind_tools is not implemented")
    agent = scripted(DB, call(), AIMessage("CE-DA-03 is out of stock."))
    config = {"configurable": {"thread_id": "stock-demo"}}
    out = agent.invoke({"messages": [HumanMessage("Stock of CE-DA-03?")]}, config)
    for message in out["messages"]:
        print(message.type, message.content or getattr(message, "tool_calls", []))
    print("saved messages:", len(agent.get_state(config).values["messages"]))
    '''),
    section("b · pytest", "We write a test file next to the notebook and run pytest in a subprocess. We assert the real tool result, tool-call correspondence, saved history and thread isolation. The final answer is scripted and cannot prove answer quality."),
    code("from pathlib import Path\nimport subprocess\nimport sys\n\n"
         + f"test_source = {TEST_SUPPORT + TESTS!r}\n"
         + '''test_path = Path("test_module04_agent.py")
test_path.write_text(test_source, encoding="utf-8")
try:
    run = subprocess.run([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", str(test_path)],
                         capture_output=True, text=True)
    print(run.stdout)
    if run.stderr:
        print(run.stderr)
    run.check_returncode()
finally:
    DB.unlink(missing_ok=True)
'''),
], setup=False)

print("module 04 notebooks written")
