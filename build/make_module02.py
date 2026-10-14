from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb import code, md, section, write_demo

MODULE = "02-graph-fundamentals"

write_demo(MODULE, "demo01-graphs-and-state-machines", [
    md("""
    # Demo 01 : Graphs and state machines

    Run the cells in order and watch. There is nothing to write.
    """),
    section("a · directed-graphs", "We represent each step as a node and each allowed transition as a directed edge."),
    code("""
    from typing import TypedDict
    from langgraph.graph import END, START, StateGraph

    class Job(TypedDict):
        status: str
        history: list[str]

    def step(status: str):
        def update(state: Job) -> dict:
            return {"status": status, "history": [*state["history"], status]}
        return update

    graph = StateGraph(Job)
    graph.add_node("diagnose", step("diagnosed"))
    graph.add_node("parts", step("waiting for parts"))
    graph.add_node("repair", step("closed"))
    graph.add_edge(START, "diagnose")
    graph.add_edge("diagnose", "parts")
    graph.add_edge("parts", "repair")
    graph.add_edge("repair", END)
    lifecycle = graph.compile()
    print("history:", lifecycle.invoke({"status": "open", "history": ["open"]})["history"])
    print(lifecycle.get_graph().draw_mermaid())
    """),
    section("b · work-order-lifecycle", "We add a retry path to show a cyclic state machine with a fixed route back to diagnosis."),
    code("""
    from typing import Literal

    class WorkOrder(TypedDict):
        status: str
        attempts: int

    def diagnose(state: WorkOrder) -> dict:
        return {"status": "diagnosed", "attempts": state["attempts"] + 1}

    def route(state: WorkOrder) -> Literal["parts", "diagnose"]:
        return "parts" if state["attempts"] == 1 else "diagnose"

    loop = StateGraph(WorkOrder)
    loop.add_node("diagnose", diagnose)
    loop.add_node("parts", lambda s: {"status": "waiting for parts"})
    loop.add_edge(START, "diagnose")
    loop.add_conditional_edges("diagnose", route)
    loop.add_edge("parts", END)
    result = loop.compile().invoke({"status": "open", "attempts": 0})
    print("status:", result["status"], "attempts:", result["attempts"])
    """),
    md("""
    ## Things to try

    - Add an inspection node between diagnosis and parts
    - Route a second failed diagnosis to a manual review node
    """),
], setup=False)

write_demo(MODULE, "demo02-nodes-and-edges", [
    md("""
    # Demo 02 : Nodes and edges

    Run the cells in order and watch. There is nothing to write.
    """),
    section("a · nodes-and-edges", "We pass typed state through two ordinary Python nodes."),
    code("""
    from typing import TypedDict
    from langgraph.graph import END, START, StateGraph

    class Number(TypedDict):
        value: int

    builder = StateGraph(Number)
    builder.add_node("double", lambda state: {"value": state["value"] * 2})
    builder.add_node("add_ten", lambda state: {"value": state["value"] + 10})
    builder.add_edge(START, "double")
    builder.add_edge("double", "add_ten")
    builder.add_edge("add_ten", END)
    graph = builder.compile()
    print("result:", graph.invoke({"value": 5}))
    """),
    section("b · start-end-entry", "We use `set_entry_point` as a named alternative to an edge from `START`."),
    code("""
    entry = StateGraph(Number)
    entry.add_node("double", lambda state: {"value": state["value"] * 2})
    entry.set_entry_point("double")
    entry.set_finish_point("double")
    print("entry result:", entry.compile().invoke({"value": 7}))
    """),
    md("""
    ## Things to try

    - Add a third node to the first graph
    - Use `set_entry_point` and `set_finish_point` on the same node
    """),
], setup=False)

write_demo(MODULE, "demo03-routing", [
    md("""
    # Demo 03 : Routing

    Run the cells in order and watch. There is nothing to write.
    """),
    section("a · conditional-edges", "We route a work order from its current priority."),
    code("""
    from typing import Literal, TypedDict
    from langgraph.graph import END, START, StateGraph

    class Ticket(TypedDict):
        priority: str
        destination: str

    def route(state: Ticket) -> Literal["page", "queue"]:
        return "page" if state["priority"] == "urgent" else "queue"

    builder = StateGraph(Ticket)
    builder.add_node("page", lambda s: {"destination": "engineer"})
    builder.add_node("queue", lambda s: {"destination": "work queue"})
    builder.add_node("route", lambda s: {})
    builder.add_edge(START, "route")
    builder.add_conditional_edges("route", route)
    builder.add_edge("page", END)
    builder.add_edge("queue", END)
    graph = builder.compile()
    for priority in ("urgent", "normal"):
        print(priority, "->", graph.invoke({"priority": priority, "destination": ""})["destination"])
    """),
    section("b · path-map", "We map router labels to node names, keeping routing decisions separate from graph labels."),
    code("""
    mapped = StateGraph(Ticket)
    mapped.add_node("route", lambda s: {})
    mapped.add_node("page", lambda s: {"destination": "engineer"})
    mapped.add_node("queue", lambda s: {"destination": "work queue"})
    mapped.add_edge(START, "route")
    mapped.add_conditional_edges("route", lambda s: s["priority"], {"urgent": "page", "routine": "queue"})
    mapped.add_edge("page", END)
    mapped.add_edge("queue", END)
    print("mapped:", mapped.compile().invoke({"priority": "routine", "destination": ""}))
    """),
    section("c · recursion-limit", "We cap a retrying graph at two supersteps and display LangGraph's recursion error."),
    code("""
    from langgraph.errors import GraphRecursionError
    from langgraph.graph import END, START, StateGraph

    class Retry(TypedDict):
        attempts: int

    retry = StateGraph(Retry)
    retry.add_node("again", lambda s: {"attempts": s["attempts"] + 1})
    retry.add_edge(START, "again")
    retry.add_edge("again", "again")
    try:
        retry.compile().invoke({"attempts": 0}, {"recursion_limit": 2})
    except GraphRecursionError as exc:
        print(type(exc).__name__)
    """),
    md("""
    ## Things to try

    - Add a second route label to `path_map`
    - Give the retry graph a conditional exit
    """),
], setup=False)

write_demo(MODULE, "demo04-command-and-send", [
    md("""
    # Demo 04 : Command and Send

    Run the cells in order and watch. There is nothing to write.
    """),
    section("a · command", "We return a state update and the next node from the same node."),
    code("""
    from typing import Literal, TypedDict
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command

    class Visit(TypedDict):
        priority: str
        assigned: str

    def triage(state: Visit) -> Command[Literal["urgent", "routine"]]:
        target = "urgent" if state["priority"] == "urgent" else "routine"
        return Command(update={"assigned": target}, goto=target)

    builder = StateGraph(Visit)
    builder.add_node("triage", triage)
    builder.add_node("urgent", lambda s: {})
    builder.add_node("routine", lambda s: {})
    builder.add_edge(START, "triage")
    builder.add_edge("urgent", END)
    builder.add_edge("routine", END)
    print("route:", builder.compile().invoke({"priority": "urgent", "assigned": ""})["assigned"])
    """),
    section("b · send-map-reduce", "We create one runtime branch per depot and collect each deterministic report."),
    code("""
    import operator
    from typing import Annotated, TypedDict
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Send

    class Summary(TypedDict):
        depots: list[str]
        reports: Annotated[list[str], operator.add]
        summary: str

    class Depot(TypedDict):
        name: str

    def fan_out(state: Summary):
        return [Send("report", {"name": name}) for name in state["depots"]]

    def report(state: Depot) -> dict:
        return {"reports": [f"{state['name']}: checked"]}

    def collect(state: Summary) -> dict:
        return {"summary": f"{len(state['reports'])} depots checked"}

    builder = StateGraph(Summary)
    builder.add_node("report", report)
    builder.add_node("collect", collect)
    builder.add_conditional_edges(START, fan_out, ["report"])
    builder.add_edge("report", "collect")
    builder.add_edge("collect", END)
    result = builder.compile().invoke({"depots": ["Rietpoort", "Broekdam", "Veldhaven"], "reports": [], "summary": ""})
    print("reports:", sorted(result["reports"]))
    print("summary:", result["summary"])
    """),
    section("c · deferred-nodes", "We mark a final aggregation node as deferred so it runs after the parallel branches finish."),
    code("""
    deferred = StateGraph(Summary)
    deferred.add_node("report", report)
    deferred.add_node("collect", collect, defer=True)
    deferred.add_conditional_edges(START, fan_out, ["report"])
    deferred.add_edge("report", "collect")
    deferred.add_edge("collect", END)
    result = deferred.compile().invoke({"depots": ["Rietpoort", "Broekdam"], "reports": [], "summary": ""})
    print("deferred summary:", result["summary"])
    """),
    md("""
    ## Things to try

    - Add another depot to the map-reduce input
    - Change the collected report format and run both graphs again
    """),
], setup=False)

write_demo(MODULE, "demo05-compiling-and-apis", [
    md("""
    # Demo 05 : Compiling and APIs

    Run the cells in order and watch. There is nothing to write.
    """),
    section("a · compile-and-visualise", "We compile a builder once, inspect its Mermaid description, then invoke it."),
    code("""
    from typing import TypedDict
    from langgraph.graph import END, START, StateGraph

    class Message(TypedDict):
        text: str

    builder = StateGraph(Message)
    builder.add_node("normalise", lambda s: {"text": s["text"].strip().title()})
    builder.add_edge(START, "normalise")
    builder.add_edge("normalise", END)
    graph = builder.compile()
    print(graph.get_graph().draw_mermaid())
    print("result:", graph.invoke({"text": "  broken validator  "}))
    """),
    section("b · functional-api", "We express the same sequence with `entrypoint` and `task` functions."),
    code("""
    from langgraph.func import entrypoint, task

    @task
    def normalise(text: str) -> str:
        return text.strip().title()

    @entrypoint()
    def workflow(text: str) -> str:
        return normalise(text).result()

    print("functional result:", workflow.invoke("  broken validator  "))
    """),
    md("""
    ## Things to try

    - Invoke both workflows with a different input string
    - Add a second task before the entrypoint returns
    """),
], setup=False)

write_demo(MODULE, "demo06-a-model-in-a-node", [
    md("""
    # Demo 06 : A model in a node

    Run the cells in order and watch. The model supplies one judgment inside a deterministic graph.
    """),
    section("a · a-model-in-a-node", "We let the model classify one work order ; every other step is a plain function."),
    code("""
    from typing import Literal, TypedDict
    from langgraph.graph import END, START, StateGraph

    class WorkOrder(TypedDict):
        description: str
        category: str
        destination: str

    def classify(state: WorkOrder) -> dict:
        category = llm.invoke(
            "Classify the work order as mechanical or electrical. Reply with one word.\\n" + state["description"]
        ).content.strip().lower()
        return {"category": "electrical" if "elect" in category else "mechanical"}

    def route(state: WorkOrder) -> Literal["electrical", "mechanical"]:
        return state["category"]

    builder = StateGraph(WorkOrder)
    builder.add_node("classify", classify)
    builder.add_node("electrical", lambda s: {"destination": "electrical bay"})
    builder.add_node("mechanical", lambda s: {"destination": "mechanical bay"})
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route)
    builder.add_edge("electrical", END)
    builder.add_edge("mechanical", END)
    result = builder.compile().invoke({
        "description": "The starter motor clicks and the engine will not turn over.",
        "category": "", "destination": ""
    })
    print("category:", result["category"])
    print("destination:", result["destination"])
    """),
    md("""
    ## Things to try

    - Replace the work order with a clearly electrical fault
    - Add a deterministic node after the selected destination
    """),
])
