"""Build exercises 01 to 04 and leave 00-setup.md as the written guide.

    uv run python build/make_exercises_01_04.py

The solution notebooks are executed separately:

    COURSE_RPS=0.05 uv run python build/run_notebook.py solutions/exerciseNN-*.ipynb
"""
import sqlite3
from pathlib import Path

from nb import blank, code, hint, md, write_exercise

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- exercise 01
write_exercise("exercise01-graphs-and-loops", [
    md("""
    # Exercise 01 : Graphs and Loops

    - A graph is nodes over typed state, joined by edges
    - A conditional edge reads the state and names the next node
    - `Command` updates the state and chooses the next node in one return

    You will build a linear graph, add a router, add a loop with a limit, and
    route with `Command`. The Aurelia records are made up.

    Worked examples to revisit : module 02, demo02 · nodes-and-edges, demo03 · routing,
    demo04 · command, demo06 · a-model-in-a-node.

    Open `exercises/exercise01-graphs-and-loops.ipynb` and run the cells in order.
    """),
    md("## Step 1 : Linear graph\n\nA ticket from T-1001 passes through `normalise` and then `stamp`."),
    blank(r'''
    from typing import Literal, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Ticket(TypedDict):
        text: str
        priority: str
        route: str


    def normalise(state: Ticket) -> dict:
        return {"text": " ".join(state["text"].split()).strip()}


    def stamp(state: Ticket) -> dict:
        return {"text": "[TICKET] " + state["text"]}


    builder = StateGraph(Ticket)
    builder.add_node("normalise", normalise)
    builder.add_node(____, stamp)
    builder.add_edge(____, "normalise")
    builder.add_edge("normalise", ____)
    builder.add_edge("stamp", ____)
    graph = builder.compile()
    linear = graph.invoke({"text": "  Slip ring   communication loss reported by radiology staff  ",
                           "priority": "", "route": ""})
    print(linear)
    ''', r'''
    from typing import Literal, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Ticket(TypedDict):
        text: str
        priority: str
        route: str


    def normalise(state: Ticket) -> dict:
        return {"text": " ".join(state["text"].split()).strip()}


    def stamp(state: Ticket) -> dict:
        return {"text": "[TICKET] " + state["text"]}


    builder = StateGraph(Ticket)
    builder.add_node("normalise", normalise)
    builder.add_node("stamp", stamp)
    builder.add_edge(START, "normalise")
    builder.add_edge("normalise", "stamp")
    builder.add_edge("stamp", END)
    graph = builder.compile()
    linear = graph.invoke({"text": "  Slip ring   communication loss reported by radiology staff  ",
                           "priority": "", "route": ""})
    print(linear)
    '''),
    hint('`"stamp"`, `START`, `"stamp"` and `END`.'),
    code(r'''
    expected = "[TICKET] Slip ring communication loss reported by radiology staff"
    print("check :", "pass" if linear["text"] == expected else "fail")
    print("text :", linear["text"])
    '''),
    md("""
    ## Step 2 : Router

    A model node sets the priority to `high` or `low`. A router sends a high
    ticket to `page_engineer` and a low ticket to `queue`. The second ticket is made up.
    """),
    blank(r'''
    def prioritise(state: Ticket) -> dict:
        reply = llm.invoke("Reply with exactly one word, high or low. A ticket is high only when work is stopped.\n\n"
                           + state["text"])
        print("usage :", reply.usage_metadata)
        label = reply.content.strip().lower()
        return {"priority": "high" if label.startswith("high") else "low"}


    def route(state: Ticket) -> Literal["page_engineer", "queue"]:
        return ____


    router = StateGraph(Ticket)
    router.add_node("prioritise", prioritise)
    router.add_node("page_engineer", lambda s: {"route": "engineer paged"})
    router.add_node("queue", lambda s: {"route": "added to the queue"})
    router.add_edge(START, "prioritise")
    router.____("prioritise", route)
    router.add_edge("page_engineer", END)
    router.add_edge("queue", END)
    router_graph = router.compile()
    runs = []
    for text in ["Gantry over-temperature during the afternoon list, scanning is stopped.",
                 "Please file the CT-400 fan procedure in the site folder."]:
        item = router_graph.invoke({"text": text, "priority": "", "route": ""})
        runs.append(item)
        print(item["priority"], "->", item["route"])
    ''', r'''
    def prioritise(state: Ticket) -> dict:
        reply = llm.invoke("Reply with exactly one word, high or low. A ticket is high only when work is stopped.\n\n"
                           + state["text"])
        print("usage :", reply.usage_metadata)
        label = reply.content.strip().lower()
        return {"priority": "high" if label.startswith("high") else "low"}


    def route(state: Ticket) -> Literal["page_engineer", "queue"]:
        return "page_engineer" if state["priority"] == "high" else "queue"


    router = StateGraph(Ticket)
    router.add_node("prioritise", prioritise)
    router.add_node("page_engineer", lambda s: {"route": "engineer paged"})
    router.add_node("queue", lambda s: {"route": "added to the queue"})
    router.add_edge(START, "prioritise")
    router.add_conditional_edges("prioritise", route)
    router.add_edge("page_engineer", END)
    router.add_edge("queue", END)
    router_graph = router.compile()
    runs = []
    for text in ["Gantry over-temperature during the afternoon list, scanning is stopped.",
                 "Please file the CT-400 fan procedure in the site folder."]:
        item = router_graph.invoke({"text": text, "priority": "", "route": ""})
        runs.append(item)
        print(item["priority"], "->", item["route"])
    '''),
    hint('`"page_engineer" if state["priority"] == "high" else "queue"` and `add_conditional_edges`.'),
    code(r'''
    ok = len(runs) == 2 and all(
        item["route"] == ("engineer paged" if item["priority"] == "high" else "added to the queue")
        for item in runs)
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## Step 3 : Loop

    `shorten` rewrites a ticket until it is at most 60 characters, or three
    attempts have been made.
    """),
    blank(r'''
    class Short(TypedDict):
        text: str
        attempts: int


    def shorten(state: Short) -> dict:
        reply = llm.invoke(f"Rewrite in fewer words, keep the meaning, no quotes : {state['text']}")
        print("usage :", reply.usage_metadata)
        text = reply.content.strip()
        print(f"attempt {state['attempts'] + 1} : {len(text)} chars | {text}")
        return {"text": text, "attempts": state["attempts"] + 1}


    def again(state: Short) -> Literal["shorten", "__end__"]:
        if len(state["text"]) <= ____ or state["attempts"] >= ____:
            return END
        return ____


    loop = StateGraph(Short)
    loop.add_node("shorten", shorten)
    loop.add_edge(START, "shorten")
    loop.add_conditional_edges("shorten", again)
    result = loop.compile().invoke({
        "text": "The CT-400 gantry at Kanaalzicht Medical Centre reports over-temperature during the afternoon "
                "list and scanning is stopped until an engineer arrives.",
        "attempts": 0})
    ''', r'''
    class Short(TypedDict):
        text: str
        attempts: int


    def shorten(state: Short) -> dict:
        reply = llm.invoke(f"Rewrite in fewer words, keep the meaning, no quotes : {state['text']}")
        print("usage :", reply.usage_metadata)
        text = reply.content.strip()
        print(f"attempt {state['attempts'] + 1} : {len(text)} chars | {text}")
        return {"text": text, "attempts": state["attempts"] + 1}


    def again(state: Short) -> Literal["shorten", "__end__"]:
        if len(state["text"]) <= 60 or state["attempts"] >= 3:
            return END
        return "shorten"


    loop = StateGraph(Short)
    loop.add_node("shorten", shorten)
    loop.add_edge(START, "shorten")
    loop.add_conditional_edges("shorten", again)
    result = loop.compile().invoke({
        "text": "The CT-400 gantry at Kanaalzicht Medical Centre reports over-temperature during the afternoon "
                "list and scanning is stopped until an engineer arrives.",
        "attempts": 0})
    '''),
    hint("`60`, `3` and `\"shorten\"`."),
    code(r'''
    stopped = result["attempts"] <= 3 and (len(result["text"]) <= 60 or result["attempts"] == 3)
    print("attempts :", result["attempts"], "chars :", len(result["text"]))
    print("check :", "pass" if stopped else "fail")
    '''),
    md("""
    ## Step 4 : Command

    `triage` already knows the priority. Return a `Command` that stores the
    chosen node on `assigned` and goes there. The destination node writes `route`.
    """),
    blank(r'''
    from langgraph.types import Command


    class Visit(TypedDict):
        priority: str
        assigned: str
        route: str


    def triage(state: Visit) -> Command[Literal["page", "queue"]]:
        target = "page" if state["priority"] == "high" else "queue"
        return ____


    routed = StateGraph(Visit)
    routed.add_node("triage", triage)
    routed.add_node("page", lambda s: {"route": "engineer paged"})
    routed.add_node("queue", lambda s: {"route": "added to the queue"})
    routed.add_edge(START, "triage")
    routed.add_edge("page", END)
    routed.add_edge("queue", END)
    command_graph = routed.compile()
    high = command_graph.invoke({"priority": "high", "assigned": "", "route": ""})
    low = command_graph.invoke({"priority": "low", "assigned": "", "route": ""})
    print("high :", high)
    print("low :", low)
    ''', r'''
    from langgraph.types import Command


    class Visit(TypedDict):
        priority: str
        assigned: str
        route: str


    def triage(state: Visit) -> Command[Literal["page", "queue"]]:
        target = "page" if state["priority"] == "high" else "queue"
        return Command(update={"assigned": target}, goto=target)


    routed = StateGraph(Visit)
    routed.add_node("triage", triage)
    routed.add_node("page", lambda s: {"route": "engineer paged"})
    routed.add_node("queue", lambda s: {"route": "added to the queue"})
    routed.add_edge(START, "triage")
    routed.add_edge("page", END)
    routed.add_edge("queue", END)
    command_graph = routed.compile()
    high = command_graph.invoke({"priority": "high", "assigned": "", "route": ""})
    low = command_graph.invoke({"priority": "low", "assigned": "", "route": ""})
    print("high :", high)
    print("low :", low)
    '''),
    hint('`Command(update={"assigned": target}, goto=target)`.'),
    code(r'''
    ok = (high["assigned"] == "page" and high["route"] == "engineer paged"
          and low["assigned"] == "queue" and low["route"] == "added to the queue")
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## If time permits

    - Print `router_graph.get_graph().draw_mermaid()` and compare it with the router slide
    - Give the loop in Step 3 a `recursion_limit` of 2 and read the error
    - Fan out with `Send`, one branch per site in `sites`, and collect the site ids
    """),
])

# ---------------------------------------------------------------- exercise 02
write_exercise("exercise02-state-for-two-agents", [
    md("""
    # Exercise 02 : State for Two Agents

    - Two nodes that run in the same step need a reducer on every key they both write
    - A node's input schema is the only state that node receives
    - A checkpointer keeps one thread, and the history lists every checkpoint

    You will run a triage agent and a parts agent on ticket T-1001, fix the shared
    write, hide a stock note from triage, and read the thread history. The Aurelia
    records are made up.

    Worked examples to revisit : module 03, demo01 · state-schemas, demo02 · reducers,
    demo03 · checkpointers, demo04 · history-and-time-travel.

    Open `exercises/exercise02-state-for-two-agents.ipynb` and run the cells in order.
    """),
    md("## Step 1 : Shared key\n\nBoth agents write `note` in the same step. Add the two edges from `START`."),
    code(r'''
    import csv
    import sqlite3
    from pathlib import Path

    with open(data("capstone/tickets.csv"), newline="", encoding="utf-8") as handle:
        ticket = next(row for row in csv.DictReader(handle) if row["ticket_id"] == "T-1001")
    print(ticket["ticket_id"], "|", ticket["symptom"], "|", ticket["parts_used"])
    '''),
    blank(r'''
    from typing import Annotated, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Clash(TypedDict):
        ticket_id: str
        note: str


    def triage(state: Clash) -> dict:
        print("triage read :", sorted(state))
        return {"note": "triage " + state["ticket_id"]}


    def parts(state: Clash) -> dict:
        print("parts read :", sorted(state))
        return {"note": "parts " + state["ticket_id"]}


    clash = StateGraph(Clash)
    clash.add_node("triage", triage)
    clash.add_node("parts", parts)
    clash.add_edge(____, "triage")
    clash.add_edge(____, "parts")
    clash.add_edge("triage", END)
    clash.add_edge("parts", END)
    clash_graph = clash.compile()
    print("graph built")
    ''', r'''
    from typing import Annotated, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Clash(TypedDict):
        ticket_id: str
        note: str


    def triage(state: Clash) -> dict:
        print("triage read :", sorted(state))
        return {"note": "triage " + state["ticket_id"]}


    def parts(state: Clash) -> dict:
        print("parts read :", sorted(state))
        return {"note": "parts " + state["ticket_id"]}


    clash = StateGraph(Clash)
    clash.add_node("triage", triage)
    clash.add_node("parts", parts)
    clash.add_edge(START, "triage")
    clash.add_edge(START, "parts")
    clash.add_edge("triage", END)
    clash.add_edge("parts", END)
    clash_graph = clash.compile()
    print("graph built")
    '''),
    hint("`START` on both edges from the start."),
    code(r'''
    from langgraph.errors import InvalidUpdateError

    try:
        clash_graph.invoke({"ticket_id": ticket["ticket_id"], "note": ""})
        print("check : fail, both writes were accepted")
    except InvalidUpdateError as exc:
        print("check : pass", type(exc).__name__)
        print(str(exc).splitlines()[0])
    '''),
    md("## Step 2 : Reducer\n\nGive `findings` a reducer that appends, then run both agents again."),
    blank(r'''
    import operator


    class Shared(TypedDict):
        ticket_id: str
        symptom: str
        findings: ____


    seen = {}


    def triage(state: Shared) -> dict:
        seen["triage"] = sorted(state)
        print("triage read :", seen["triage"])
        return {"findings": [f"triage {state['ticket_id']} {state['symptom'][:48]}"]}


    def parts(state: Shared) -> dict:
        seen["parts"] = sorted(state)
        print("parts read :", seen["parts"])
        return {"findings": [f"parts {state['ticket_id']}"]}


    shared = StateGraph(Shared)
    shared.add_node("triage", triage)
    shared.add_node("parts", parts)
    shared.add_edge(START, "triage")
    shared.add_edge(START, "parts")
    shared.add_edge("triage", END)
    shared.add_edge("parts", END)
    shared_graph = shared.compile()
    ''', r'''
    import operator


    class Shared(TypedDict):
        ticket_id: str
        symptom: str
        findings: Annotated[list[str], operator.add]


    seen = {}


    def triage(state: Shared) -> dict:
        seen["triage"] = sorted(state)
        print("triage read :", seen["triage"])
        return {"findings": [f"triage {state['ticket_id']} {state['symptom'][:48]}"]}


    def parts(state: Shared) -> dict:
        seen["parts"] = sorted(state)
        print("parts read :", seen["parts"])
        return {"findings": [f"parts {state['ticket_id']}"]}


    shared = StateGraph(Shared)
    shared.add_node("triage", triage)
    shared.add_node("parts", parts)
    shared.add_edge(START, "triage")
    shared.add_edge(START, "parts")
    shared.add_edge("triage", END)
    shared.add_edge("parts", END)
    shared_graph = shared.compile()
    '''),
    hint("`Annotated[list[str], operator.add]`."),
    code(r'''
    reduced = shared_graph.invoke({"ticket_id": ticket["ticket_id"], "symptom": ticket["symptom"], "findings": []})
    print("findings :", reduced["findings"])
    text = " ".join(reduced["findings"])
    ok = "triage" in text and "parts" in text and seen["triage"] == seen["parts"]
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## Step 3 : Private key

    `stock_note` is the stock line for the ticket's part. The parts agent reads it.
    Triage does not. The invoke result leaves it out.
    """),
    blank(r'''
    class SharedInput(TypedDict):
        ticket_id: str
        symptom: str
        part_no: str


    class TriageView(TypedDict):
        ticket_id: str
        symptom: str


    class PartsView(TypedDict):
        ticket_id: str
        part_no: str
        stock_note: ____


    class Public(TypedDict):
        ticket_id: str
        findings: list[str]


    class Desk(TypedDict):
        ticket_id: str
        symptom: str
        part_no: str
        findings: Annotated[list[str], operator.add]
        stock_note: str


    def lookup(state: SharedInput) -> dict:
        database = Path(data("capstone/service.db")).resolve()
        with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
            name, stock, depot = db.execute(
                "SELECT name, stock, depot FROM parts WHERE part_no = ?", (state["part_no"],)).fetchone()
        return {"stock_note": f"{state['part_no']} {name} stock {stock} at {depot}"}


    def triage(state: TriageView) -> dict:
        seen["triage"] = sorted(state)
        print("triage read :", seen["triage"])
        return {"findings": [f"triage {state['ticket_id']} {state['symptom'][:48]}"]}


    def parts(state: PartsView) -> dict:
        seen["parts"] = sorted(state)
        print("parts read :", seen["parts"])
        return {"findings": [f"parts {state['stock_note']}"]}


    desk = StateGraph(Desk, input_schema=SharedInput, output_schema=____)
    desk.add_node("lookup", lookup)
    desk.add_node("triage", triage)
    desk.add_node("parts", parts)
    desk.add_edge(START, "lookup")
    desk.add_edge("lookup", "triage")
    desk.add_edge("lookup", "parts")
    desk.add_edge("triage", END)
    desk.add_edge("parts", END)
    private_graph = desk.compile()
    inputs = {"ticket_id": ticket["ticket_id"], "symptom": ticket["symptom"], "part_no": ticket["parts_used"]}
    ''', r'''
    class SharedInput(TypedDict):
        ticket_id: str
        symptom: str
        part_no: str


    class TriageView(TypedDict):
        ticket_id: str
        symptom: str


    class PartsView(TypedDict):
        ticket_id: str
        part_no: str
        stock_note: str


    class Public(TypedDict):
        ticket_id: str
        findings: list[str]


    class Desk(TypedDict):
        ticket_id: str
        symptom: str
        part_no: str
        findings: Annotated[list[str], operator.add]
        stock_note: str


    def lookup(state: SharedInput) -> dict:
        database = Path(data("capstone/service.db")).resolve()
        with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
            name, stock, depot = db.execute(
                "SELECT name, stock, depot FROM parts WHERE part_no = ?", (state["part_no"],)).fetchone()
        return {"stock_note": f"{state['part_no']} {name} stock {stock} at {depot}"}


    def triage(state: TriageView) -> dict:
        seen["triage"] = sorted(state)
        print("triage read :", seen["triage"])
        return {"findings": [f"triage {state['ticket_id']} {state['symptom'][:48]}"]}


    def parts(state: PartsView) -> dict:
        seen["parts"] = sorted(state)
        print("parts read :", seen["parts"])
        return {"findings": [f"parts {state['stock_note']}"]}


    desk = StateGraph(Desk, input_schema=SharedInput, output_schema=Public)
    desk.add_node("lookup", lookup)
    desk.add_node("triage", triage)
    desk.add_node("parts", parts)
    desk.add_edge(START, "lookup")
    desk.add_edge("lookup", "triage")
    desk.add_edge("lookup", "parts")
    desk.add_edge("triage", END)
    desk.add_edge("parts", END)
    private_graph = desk.compile()
    inputs = {"ticket_id": ticket["ticket_id"], "symptom": ticket["symptom"], "part_no": ticket["parts_used"]}
    '''),
    hint("`str` on `stock_note`, and `Public` as `output_schema`."),
    code(r'''
    out = private_graph.invoke(inputs)
    streamed = list(private_graph.stream(inputs, stream_mode="values"))
    print("invoke keys :", sorted(out))
    print("findings :", out["findings"])
    for part in streamed:
        if "stock_note" in part:
            print("stream :", part["stock_note"])
    hidden = "stock_note" not in out
    visible = any("stock_note" in part and "stock 0" in part["stock_note"] for part in streamed)
    ok = hidden and visible and "stock_note" not in seen["triage"] and "stock_note" in seen["parts"]
    print("check :", "pass" if ok else "fail")
    '''),
    md("## Step 4 : History\n\nCompile the same builder with a checkpointer and a thread, then read the history."),
    blank(r'''
    from langgraph.checkpoint.memory import InMemorySaver

    saved = desk.compile(checkpointer=____)
    cfg = {"configurable": {"thread_id": ____}}
    saved.invoke(inputs, cfg)
    history = list(____)
    print("checkpoints :", len(history))
    ''', r'''
    from langgraph.checkpoint.memory import InMemorySaver

    saved = desk.compile(checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "T-1001"}}
    saved.invoke(inputs, cfg)
    history = list(saved.get_state_history(cfg))
    print("checkpoints :", len(history))
    '''),
    hint('`InMemorySaver()`, `"T-1001"`, and `saved.get_state_history(cfg)`.'),
    code(r'''
    latest = saved.get_state(cfg)
    print("thread findings :", latest.values["findings"])
    for snap in history:
        print("step :", snap.metadata["step"], "next :", snap.next)
    ok = len(history) >= 3 and len(latest.values["findings"]) == 2 and any(snap.next == () for snap in history)
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## If time permits

    - Open a second thread id on `saved` and compare `get_state` on both
    - Replace `InMemorySaver` with `SqliteSaver` and open the same thread again
    - Fork the checkpoint before `parts` with `update_state` and change `stock_note`
    """),
])

# ---------------------------------------------------------------- exercise 03
EX03_TEST = r'''
from pathlib import Path
import subprocess
import sys

TEST = r"""
import sqlite3
from pathlib import Path

import pytest
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.messages import AIMessage, HumanMessage, ToolCall
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


def service_db() -> Path:
    here = Path(__file__).resolve().parent
    root = next(p for p in [here, *here.parents] if (p / "data" / "capstone" / "service.db").exists())
    return root / "data" / "capstone" / "service.db"


@tool
def part_stock(part_no: str) -> str:
    "Read recorded units in stock for an Aurelia spare part."
    with sqlite3.connect(f"file:{service_db().as_posix()}?mode=ro", uri=True) as conn:
        row = conn.execute("SELECT stock FROM parts WHERE part_no = ?", (part_no,)).fetchone()
    return str(row[0]) if row else "Unknown part"


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(part_no="CT-SR-03", call_id="stock-1"):
    return AIMessage("", tool_calls=[ToolCall(name="part_stock", args={"part_no": part_no}, id=call_id)])


def scripted(*messages, middleware=()):
    return create_agent(
        FakeToolModel(messages=iter(messages)),
        tools=[part_stock],
        middleware=list(middleware),
        system_prompt="Use part_stock for stock questions.",
    )


def test_known_and_unknown_part():
    assert part_stock.invoke({"part_no": "CT-SR-03"}) == "0"
    assert part_stock.invoke({"part_no": "UNKNOWN"}) == "Unknown part"


def test_tool_result_and_call_id():
    agent = scripted(call(), AIMessage("CT-SR-03 has no stock."))
    out = agent.invoke({"messages": [HumanMessage("Stock of CT-SR-03?")]})
    results = [m for m in out["messages"] if m.type == "tool"]
    assert len(results) == 1
    assert results[0].content == "0"
    assert results[0].tool_call_id == "stock-1"


def test_run_limit_stops_the_second_call():
    agent = scripted(
        call(call_id="c1"),
        call(call_id="c2"),
        AIMessage("done"),
        middleware=[LIMIT_GOES_HERE],
    )
    out = agent.invoke({"messages": [HumanMessage("Stock?")]})
    results = [m for m in out["messages"] if m.type == "tool"]
    assert len(results) == 1
    assert "run limit (1/1)" in out["messages"][-1].content
"""

path = Path("test_exercise03_agent.py")
path.write_text(TEST, encoding="utf-8")
print("wrote", path.name)
'''
EX03_LIMIT = 'ModelCallLimitMiddleware(run_limit=1, exit_behavior="end")'
EX03_TEST_SOLUTION = EX03_TEST.replace("LIMIT_GOES_HERE", EX03_LIMIT)
EX03_TEST_SKELETON = EX03_TEST.replace("LIMIT_GOES_HERE", "____")

write_exercise("exercise03-an-agent-with-tests", [
    md("""
    # Exercise 03 : An Agent with Tests

    - `create_agent` compiles a tool-calling loop
    - A scripted fake model drives that loop without the network
    - `ModelCallLimitMiddleware` stops the loop after a fixed number of model calls

    You will look up a part in Aurelia's `service.db`, test the agent with a fake
    model, and make one live call. The Aurelia records are made up.

    Worked examples to revisit : module 04, demo02 · create-agent, demo05 · agent-failures,
    demo07 · testing-agents.

    Open `exercises/exercise03-an-agent-with-tests.ipynb` and run the cells in order.
    """),
    md("## Step 1 : Tool\n\nRead `stock` for one part number. Return `Unknown part` when the row is missing."),
    blank(r'''
    import sqlite3
    from pathlib import Path

    from langchain.tools import tool

    DB = Path(data("capstone/service.db")).resolve()


    @tool
    def part_stock(part_no: str) -> str:
        """Read recorded units in stock for an Aurelia spare part."""
        with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
            row = conn.execute(____).fetchone()
        return str(row[0]) if row else "Unknown part"
    ''', r'''
    import sqlite3
    from pathlib import Path

    from langchain.tools import tool

    DB = Path(data("capstone/service.db")).resolve()


    @tool
    def part_stock(part_no: str) -> str:
        """Read recorded units in stock for an Aurelia spare part."""
        with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
            row = conn.execute("SELECT stock FROM parts WHERE part_no = ?", (part_no,)).fetchone()
        return str(row[0]) if row else "Unknown part"
    '''),
    hint('`"SELECT stock FROM parts WHERE part_no = ?", (part_no,)`.'),
    code(r'''
    known = part_stock.invoke({"part_no": "CT-SR-03"})
    unknown = part_stock.invoke({"part_no": "UNKNOWN"})
    print("CT-SR-03 :", known)
    print("UNKNOWN :", unknown)
    print("check :", "pass" if known == "0" and unknown == "Unknown part" else "fail")
    '''),
    md("""
    ## Step 2 : Scripted model

    `GenericFakeChatModel.bind_tools` raises `NotImplementedError`. Return the
    same model from the subclass, then script one tool call and a final answer.
    """),
    blank(r'''
    from langchain.agents import create_agent
    from langchain.messages import AIMessage, HumanMessage, ToolCall
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


    class FakeToolModel(GenericFakeChatModel):
        def bind_tools(self, tools, **kwargs):
            return ____


    def call(part_no="CT-SR-03", call_id="stock-1"):
        return AIMessage("", tool_calls=[ToolCall(name="part_stock", args={"part_no": part_no}, id=call_id)])


    agent = create_agent(
        FakeToolModel(messages=iter([call(), AIMessage("CT-SR-03 has no stock.")])),
        tools=[part_stock],
        system_prompt="Use part_stock for stock questions.")
    out = agent.invoke({"messages": [HumanMessage("Stock of CT-SR-03?")]})
    for message in out["messages"]:
        print(message.type, message.content or getattr(message, "tool_calls", []))
    ''', r'''
    from langchain.agents import create_agent
    from langchain.messages import AIMessage, HumanMessage, ToolCall
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


    class FakeToolModel(GenericFakeChatModel):
        def bind_tools(self, tools, **kwargs):
            return self


    def call(part_no="CT-SR-03", call_id="stock-1"):
        return AIMessage("", tool_calls=[ToolCall(name="part_stock", args={"part_no": part_no}, id=call_id)])


    agent = create_agent(
        FakeToolModel(messages=iter([call(), AIMessage("CT-SR-03 has no stock.")])),
        tools=[part_stock],
        system_prompt="Use part_stock for stock questions.")
    out = agent.invoke({"messages": [HumanMessage("Stock of CT-SR-03?")]})
    for message in out["messages"]:
        print(message.type, message.content or getattr(message, "tool_calls", []))
    '''),
    hint("`return self`."),
    code(r'''
    results = [m for m in out["messages"] if m.type == "tool"]
    ok = len(results) == 1 and results[0].content == "0" and results[0].tool_call_id == "stock-1"
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## Step 3 : Pytest

    The test module repeats the tool checks and stops a second model call with
    `ModelCallLimitMiddleware`. Pytest uses the fake model only.
    """),
    blank(EX03_TEST_SKELETON, EX03_TEST_SOLUTION),
    hint('`ModelCallLimitMiddleware(run_limit=1, exit_behavior="end")`.'),
    code(r'''
    import shutil
    import subprocess
    import sys

    try:
        run = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", str(path)],
            capture_output=True, text=True)
        print(run.stdout)
        if run.stderr:
            print(run.stderr)
        print("check :", "pass" if run.returncode == 0 else "fail")
    finally:
        path.unlink(missing_ok=True)
        shutil.rmtree(path.parent / "__pycache__", ignore_errors=True)
    '''),
    md("""
    ## Step 4 : Live run

    The same tool and a call limit of 4, on the course model. Ask for `CT-SR-03`.
    """),
    code(r'''
    from langchain.agents.middleware import ModelCallLimitMiddleware

    live = create_agent(
        llm,
        tools=[part_stock],
        middleware=[ModelCallLimitMiddleware(run_limit=4, exit_behavior="end")],
        system_prompt="Use part_stock for stock questions. Report the number the tool returns.")
    live_out = live.invoke(
        {"messages": [HumanMessage("How many CT-SR-03 units are in stock? Use the tool.")]},
        {"recursion_limit": 8})
    for message in live_out["messages"]:
        print(message.type, message.content or getattr(message, "tool_calls", []))
        if getattr(message, "usage_metadata", None):
            print("usage :", message.usage_metadata)
    '''),
    code(r'''
    tool_msgs = [m for m in live_out["messages"] if m.type == "tool"]
    print("tool results :", [m.content for m in tool_msgs])
    print("check :", "pass" if any(m.content == "0" for m in tool_msgs) else "fail")
    '''),
    md("""
    ## If time permits

    - Add `ToolCallLimitMiddleware` on `part_stock` and script a second call
    - Point a second thread id at the same agent and compare `get_state`
    - Change `run_limit` to 1 on the live agent and read the limit message
    """),
])

# ---------------------------------------------------------------- exercise 04
TOOLS = r'''
import json
import operator
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Annotated, TypedDict

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Send


class Counter(BaseCallbackHandler):
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.calls = self.input = self.output = 0

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


counter = Counter()
metered = make_llm(callbacks=[counter], max_tokens=600, max_retries=0, timeout=120)
metrics = []


def measured(label, operation):
    counter.reset()
    start = time.perf_counter()
    try:
        return operation()
    finally:
        row = {"pattern": label, "calls": counter.calls, "input_tokens": counter.input,
               "output_tokens": counter.output, "seconds": round(time.perf_counter() - start, 1)}
        metrics.append(row)
        print("metrics :", json.dumps(row))


DB = Path(data("capstone/service.db")).resolve()
MANUALS = Path(data_folder("capstone/manuals"))
PAGES = {p.name: p.read_text(encoding="utf-8") for p in sorted(MANUALS.glob("*.md"))}


@tool
def run_sql(query: str) -> str:
    """Run a read-only SELECT. Tables: sites(site_id, name, city, contract),
    devices(serial, model, site_id, installed, firmware),
    parts(part_no, model, name, stock, price_eur, depot),
    work_orders(wo_id, serial, opened, status, error_code, summary, engineer_id)."""
    if not query.lstrip().lower().startswith("select"):
        return "Only SELECT statements are allowed."
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        return json.dumps(db.execute(query).fetchmany(15))


@tool
def search_manuals(query: str) -> str:
    """Find Aurelia manuals and bulletins. Returns the opening of the two best matches."""
    words = set(query.lower().split())
    ranked = sorted(PAGES, key=lambda name: -sum(PAGES[name].lower().count(w) for w in words))[:2]
    return "\n\n".join(f"[{name}]\n{PAGES[name][:800]}" for name in ranked)
'''

CHECK_SOLUTION = r'''
import re


PART = re.compile(r"\b[A-Z]{2}-[A-Z]{2}-\d{2}\b")


def check_plan(plan: str, site_id: str) -> list[str]:
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        serials = [s for (s,) in db.execute("SELECT serial FROM devices WHERE site_id = ?", (site_id,))]
        stock = dict(db.execute("SELECT part_no, stock FROM parts"))
    problems = [f"device {s} is missing" for s in serials if s not in plan]
    for line in plan.splitlines():
        for part in PART.findall(line):
            if part not in stock:
                problems.append(f"part {part} does not exist")
            elif stock[part] == 0 and "out of stock" not in line.lower():
                problems.append(f"part {part} has no stock and the plan does not say so")
    return sorted(set(problems))
'''

CHECK_SKELETON = r'''
import re


PART = re.compile(r"\b[A-Z]{2}-[A-Z]{2}-\d{2}\b")


def check_plan(plan: str, site_id: str) -> list[str]:
    ____
'''

CHECK_TEST = r'''
GOOD = """Visit plan S04
- MR150-2024-0098 : WO-9003 needs cold head MR-CH-02, out of stock at Venlo
- UX20-2025-2311 : probe cleaning check, bring fan filter UX-FF-03"""
BAD = """Visit plan S04
- MR150-2024-0098 : bring cold head MR-CH-02 and filter MR-XX-99"""
print("good :", check_plan(GOOD, "S04"))
print("bad  :", check_plan(BAD, "S04"))
assert check_plan(GOOD, "S04") == [], "the good plan should pass"
assert len(check_plan(BAD, "S04")) == 3, "the bad plan has three problems"
print("check : pass")
'''

GRAPH_SKELETON = r'''
class Visit(TypedDict):
    site_id: str
    devices: str
    sections: Annotated[list[str], operator.add]
    plan: str
    problems: list[str]
    rounds: int


class Task(TypedDict):
    question: str


def agent_by_hand(model, tools, prompt):
    bound = model.bind_tools(tools)

    def model_node(state):
        return {"messages": [bound.invoke([SystemMessage(prompt), *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", model_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile()


def ask(question):
    return {"messages": [HumanMessage(question)]}


def last_text(result):
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage) and message.content and not message.tool_calls:
            return str(message.content)
    return str(result["messages"][-1].content)


def specialist(name, worker):
    def node(state: Task) -> dict:
        try:
            answer = last_text(worker.invoke(ask(state["question"]), {"recursion_limit": 10}))
        except GraphRecursionError:
            answer = "(no answer : the specialist hit its step limit)"
        print(name, ":", answer[:300])
        return {"sections": [name + " :\n" + answer]}
    return node


PLAN_RULES = "One bullet per device, starting with its serial number. Write 'out of stock' next to any part with stock 0."


def devices(state: Visit) -> dict:
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT serial, model, firmware FROM devices WHERE site_id = ?", (state["site_id"],)).fetchall()
    return {"devices": "\n".join(f"{serial} {model} firmware {firmware}" for serial, model, firmware in rows)}


def manuals_question(state: Visit) -> str:
    return ____


def parts_question(state: Visit) -> str:
    return (
        "work_orders has no site_id. Join it to devices on serial. "
        "A status other than closed still counts. Run this SELECT once and report every column:\n"
        "SELECT w.wo_id, w.serial, w.status, w.error_code, p.part_no, p.name, p.stock, p.depot "
        "FROM work_orders w JOIN devices d ON d.serial = w.serial "
        "JOIN parts p ON p.part_no = 'MR-CH-02' "
        f"WHERE d.site_id = '{state['site_id']}' AND w.status != 'closed'")


def dispatch(state: Visit):
    return ____


def assemble(state: Visit) -> dict:
    feedback = ""
    if state["problems"]:
        feedback = "\nFix these problems found by the checker :\n" + "\n".join(state["problems"])
    plan = metered.invoke(
        f"Write a visit plan for site {state['site_id']}. {PLAN_RULES}\n\nDevices :\n{state['devices']}\n\n"
        + "\n\n".join(state["sections"]) + feedback).content
    return {"plan": plan, "rounds": state["rounds"] + 1}


def check(state: Visit) -> dict:
    found = check_plan(state["plan"], state["site_id"])
    print(f"round {state['rounds']} :", found or "passed")
    return {"problems": found}


def after_check(state: Visit):
    return ____


parts_worker = agent_by_hand(metered, [run_sql], "Call run_sql once. Then answer from those rows and stop.")
manuals_worker = agent_by_hand(metered, [search_manuals], "Call search_manuals once. Then answer, cite the file name, and stop.")

b = StateGraph(Visit)
b.add_node("devices", devices)
b.add_node("parts", specialist("parts", parts_worker), input_schema=Task)
b.add_node("manuals", specialist("manuals", manuals_worker), input_schema=Task)
b.add_node("assemble", assemble)
b.add_node("check", check)
b.add_edge(START, "devices")
b.add_conditional_edges("devices", dispatch, ["parts", "manuals"])
____
b.add_edge("assemble", "check")
b.add_conditional_edges("check", after_check, ["assemble", END])
planner = b.compile()
print("planner built")
'''

GRAPH_SOLUTION = (
    GRAPH_SKELETON
    .replace(
        "def manuals_question(state: Visit) -> str:\n    return ____",
        "def manuals_question(state: Visit) -> str:\n"
        "    return (\"Search the maintenance pages. Which intervals and service bulletins apply "
        "to these devices?\\n\"\n"
        "            + state[\"devices\"])",
    )
    .replace(
        "def dispatch(state: Visit):\n    return ____",
        "def dispatch(state: Visit):\n"
        "    return [\n"
        "        Send(\"parts\", {\"question\": parts_question(state)}),\n"
        "        Send(\"manuals\", {\"question\": manuals_question(state)}),\n"
        "    ]",
    )
    .replace(
        "def after_check(state: Visit):\n    return ____",
        "def after_check(state: Visit):\n"
        "    return \"assemble\" if state[\"problems\"] and state[\"rounds\"] < 2 else END",
    )
    .replace(
        "____\nb.add_edge(\"assemble\", \"check\")",
        "b.add_edge([\"parts\", \"manuals\"], \"assemble\")\nb.add_edge(\"assemble\", \"check\")",
    )
)

write_exercise("exercise04-a-multi-agent-visit-planner", [
    md("""
    # Exercise 04 : A Multi-Agent Visit Planner

    - A router sends one task to each specialist with `Send`
    - Each specialist is its own agent, with its own tool and its own message list
    - A checker written in code checks specified properties without a model call
    - A second design has to earn its calls and tokens against one agent

    You will plan one visit to site S04. Devices come from the database. A parts
    agent and a manuals agent run as subagents. A checker reads the plan, then one
    agent does the same task. The Aurelia records are made up.

    Worked examples to revisit : module 05, demo01 · subagents, demo03 · router,
    demo07 · maker-checker, demo09 · what-each-pattern-costs.

    Open `exercises/exercise04-a-multi-agent-visit-planner.ipynb` and run the cells in order.
    """),
    md("## Step 1 : Tools\n\n`run_sql` and `search_manuals` read the Aurelia database and manuals."),
    code(TOOLS),
    code(r'''
    listed = run_sql.invoke({"query": "SELECT serial FROM devices WHERE site_id = 'S04'"})
    blocked = run_sql.invoke({"query": "DELETE FROM devices"})
    print("devices :", listed)
    print("blocked :", blocked)
    ok = "MR150-2024-0098" in listed and "UX20-2025-2311" in listed and blocked.startswith("Only SELECT")
    print("check :", "pass" if ok else "fail")
    '''),
    md("""
    ## Step 2 : Checker

    Return a list of problems, empty when the plan passes. Every device at the
    site appears by serial number. Every part number such as `MR-CH-02` exists
    in `parts`. A part with stock 0 has "out of stock" on the same line.
    """),
    blank(CHECK_SKELETON, CHECK_SOLUTION),
    hint("""
    Read the serials with `SELECT serial FROM devices WHERE site_id = ?` and the stock with
    `dict(db.execute("SELECT part_no, stock FROM parts"))`, inside
    `sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)`. Then loop over `plan.splitlines()` and
    `PART.findall(line)`.
    """),
    code(CHECK_TEST),
    md("""
    ## Step 3 : Router

    Complete the manuals question from `state["devices"]`, the two `Send`s, the
    join into `assemble`, and `after_check`. Each specialist is an agent built
    from a model node and a tool node.
    """),
    blank(GRAPH_SKELETON, GRAPH_SOLUTION),
    hint("""
    The manuals question concatenates `state["devices"]`. `dispatch` returns
    `Send("parts", ...)` and `Send("manuals", ...)`. `after_check` returns
    `"assemble" if state["problems"] and state["rounds"] < 2 else END`.
    `b.add_edge(["parts", "manuals"], "assemble")` waits for both branches.
    """),
    code(r'''
    sample = {"site_id": "S04", "devices": "MR150-2024-0098 MR-150 firmware 12.0",
              "sections": [], "plan": "", "problems": ["device missing"], "rounds": 1}
    sent = {item.node: item.arg["question"] for item in dispatch(sample)}
    routes_ok = set(sent) == {"parts", "manuals"} and "MR150-2024-0098" in sent.get("manuals", "")
    again_ok = after_check(sample) == "assemble"
    stop_ok = after_check({**sample, "problems": []}) == END and after_check({**sample, "rounds": 2}) == END
    print("nodes :", sorted(sent))
    print("check :", "pass" if routes_ok and again_ok and stop_ok else "fail")
    '''),
    md("## Step 4 : Cost\n\nPlan S04, then give one agent both tools and the same task."),
    code(r'''
    def run_planner(site):
        final = {}
        for update in planner.stream(
                {"site_id": site, "devices": "", "sections": [], "plan": "", "problems": [], "rounds": 0},
                {"recursion_limit": 12}, stream_mode="updates"):
            for _node, values in update.items():
                final.update(values or {})
        return final


    planner_result = measured("planner", lambda: run_planner("S04"))
    print(planner_result.get("plan", "")[:800])
    print("planner problems :", planner_result.get("problems"))

    single = create_agent(
        metered,
        tools=[run_sql, search_manuals],
        system_prompt="Write a visit plan for site S04. " + PLAN_RULES
        + " work_orders has no site_id; join it to devices on serial. A status other than closed still counts. "
        + "Use run_sql and search_manuals, then stop.")
    single_result = measured(
        "one agent",
        lambda: single.invoke({"messages": [HumanMessage("Plan the visit to site S04.")]}, {"recursion_limit": 8}))
    answer = last_text(single_result)
    print(answer[:800])
    print("one agent problems :", check_plan(answer, "S04"))
    '''),
    code(r'''
    ok = bool(planner_result.get("plan")) and len(metrics) >= 2 and all(row["calls"] >= 1 for row in metrics[-2:])
    print("check :", "pass" if ok else "fail")
    for row in metrics[-2:]:
        print(row["pattern"], row["calls"], "calls", row["input_tokens"] + row["output_tokens"], "tokens")
    '''),
    md("""
    ## If time permits

    - Plan site S01 with `run_planner`
    - Add a fourth check : every CT-400 on firmware below 5.2 gets the 12-month fan interval
    - Replace the router with a handoff. Disable parallel tool calls, and forward the full
      worker history with the transfer receipt, as in demo04 · handoffs
    """),
])


def _prove():
    ns = {"sqlite3": sqlite3, "DB": (ROOT / "data" / "capstone" / "service.db").resolve(), "re": __import__("re")}
    exec(CHECK_SOLUTION, ns)
    exec(CHECK_TEST, ns)
    if "____" in GRAPH_SOLUTION or "____" in CHECK_SOLUTION or "____" in EX03_TEST_SOLUTION:
        raise SystemExit("a solution string still contains ____")
    if "LIMIT_GOES_HERE" in EX03_TEST_SOLUTION:
        raise SystemExit("exercise 03 limit was not filled")

    import operator
    from typing import Annotated, TypedDict

    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Send

    class S(TypedDict):
        site_id: str
        sections: Annotated[list[str], operator.add]
        plan: str

    class T(TypedDict):
        question: str

    def dispatch(state):
        return [Send("parts", {"question": "p"}), Send("manuals", {"question": state["site_id"]})]

    graph = StateGraph(S)
    graph.add_node("devices", lambda state: {})
    graph.add_node("parts", lambda state: {"sections": ["parts"]}, input_schema=T)
    graph.add_node("manuals", lambda state: {"sections": [state["question"]]}, input_schema=T)
    graph.add_node("assemble", lambda state: {"plan": ",".join(sorted(state["sections"]))})
    graph.add_edge(START, "devices")
    graph.add_conditional_edges("devices", dispatch, ["parts", "manuals"])
    graph.add_edge(["parts", "manuals"], "assemble")
    graph.add_edge("assemble", END)
    out = graph.compile().invoke({"site_id": "S04", "sections": [], "plan": ""})
    if out["plan"] != "S04,parts":
        raise SystemExit(f"join failed : {out}")
    print("offline checks passed")


_prove()
print("exercises 01 to 04 written")
