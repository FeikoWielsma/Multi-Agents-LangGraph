"""Build module 07. Ports ARI510 demo22's review and restart workflow."""
from nb import code, md, section, write_demo

MODULE = "07-advanced-workflows"

COMMON = r'''
import json
import operator
import sqlite3
import time
from pathlib import Path
from typing import Annotated, Literal, TypedDict
from uuid import uuid4

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command, interrupt

class Usage(BaseCallbackHandler):
    def __init__(self):
        self.calls = self.input_tokens = self.output_tokens = 0

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.calls += 1

    def on_llm_end(self, response, **kwargs):
        for batch in response.generations:
            for generation in batch:
                usage = generation.message.usage_metadata or {}
                self.input_tokens += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)

usage = Usage()
llm = make_llm(callbacks=[usage], max_retries=0, max_tokens=650)
started = time.perf_counter()
DB = Path(data("demo-world/service.db")).resolve()
with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    work_order = dict(conn.execute("SELECT * FROM work_orders WHERE wo_id = ?", ("BW-7001",)).fetchone())
    part = dict(conn.execute("SELECT * FROM parts WHERE part_no = ?", ("CE-CF-02",)).fetchone())
print("work order:", work_order)
print("part:", part)

def config(label):
    return {"configurable": {"thread_id": f"07-{label}-{uuid4()}"}, "recursion_limit": 30}
'''

METRICS = '''
print("metrics:", json.dumps({"model": MODEL, "calls": usage.calls,
      "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
      "seconds": round(time.perf_counter() - started, 1)}))
'''


def demo(number, slug, title, cells, optional):
    write_demo(MODULE, f"demo{number:02d}-{slug}", [
        md(f"# Demo {number:02d} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        *cells, code(METRICS), md("## Things to try\n\nOptional : " + optional),
    ])

REVIEW = r'''
class Reply(TypedDict):
    complaint: str
    draft: str
    feedback: str
    sent: str

def write(state: Reply):
    draft = llm.invoke(
        "Write a short internal Veenhaven Bus repair proposal. Do not invent a diagnosis. "
        f"Work order: {state['complaint']}. Available part: {part}. "
        f"Reviewer feedback: {state['feedback']}"
    ).content
    return {"draft": draft}

def review(state: Reply) -> Command[Literal["send", "write"]]:
    decision = interrupt({"draft": state["draft"], "options": ["approve", "edit", "reject"]})
    if decision["action"] == "approve":
        return Command(goto="send")
    if decision["action"] == "edit":
        return Command(update={"draft": decision["text"]}, goto="send")
    if decision["action"] == "reject":
        return Command(update={"feedback": decision["text"]}, goto="write")
    raise ValueError("Unknown review action")

def send(state: Reply):
    return {"sent": state["draft"]}

builder = StateGraph(Reply)
builder.add_node("write", write)
builder.add_node("review", review)
builder.add_node("send", send)
builder.add_edge(START, "write")
builder.add_edge("write", "review")
builder.add_edge("send", END)
graph = builder.compile(checkpointer=InMemorySaver())
inputs = {"complaint": json.dumps(work_order), "draft": "", "feedback": "", "sent": ""}
'''

demo(1, "interrupts", "Interrupts", [
    section("a · interrupt", "We port the write, review and send workflow from ARI510 demo22 to a Veenhaven Bus work order. Sending records a proposal in state and makes no external change."),
    code(COMMON), code(REVIEW),
    code('''
    cfg = config("review")
    paused = graph.invoke(inputs, cfg, version="v2")
    print("payload:", paused.interrupts[0].value)
    print("next:", graph.get_state(cfg).next)
    print("sent:", paused.value["sent"])
    assert paused.interrupts and not paused.value["sent"]
    approved = graph.invoke(Command(resume={"action": "approve"}), cfg, version="v2")
    print("approved:", approved.value["sent"])
    assert not approved.interrupts and approved.value["sent"]
    '''),
    section("b · approve-edit-reject", "We supply an edited proposal, then reject another draft with feedback. Rejection returns to writing and asks for approval again. The model may change the wording or retain parts of its earlier proposal."),
    md("We reuse the saved draft in fresh threads with `update_state(..., as_node=\"write\")`, from module 03. The pause before writing avoids another model call before each review."),
    code('''
    edit_cfg = config("edit")
    graph.invoke(inputs, edit_cfg, version="v2", interrupt_before=["write"])
    graph.update_state(edit_cfg, {"draft": approved.value["draft"]}, as_node="write")
    graph.invoke(None, edit_cfg, version="v2")
    edited_text = "Inspect BW-7001 before reserving CE-CF-02. No part order is authorised."
    edited = graph.invoke(Command(resume={"action": "edit", "text": edited_text}), edit_cfg, version="v2")
    print("edited:", edited.value["sent"])
    assert edited.value["sent"] == edited_text

    reject_cfg = config("reject")
    graph.invoke(inputs, reject_cfg, version="v2", interrupt_before=["write"])
    graph.update_state(reject_cfg, {"draft": approved.value["draft"]}, as_node="write")
    graph.invoke(None, reject_cfg, version="v2")
    rewritten = graph.invoke(Command(resume={"action": "reject", "text": "Require an inspection before selecting a replacement part."}), reject_cfg, version="v2")
    print("revised:", rewritten.interrupts[0].value)
    assert rewritten.interrupts and not rewritten.value["sent"]
    final = graph.invoke(Command(resume={"action": "approve"}), reject_cfg, version="v2")
    print("sent:", final.value["sent"])
    assert final.value["sent"]
    '''),
    section("c · several-interrupts", "We keep sequential interrupt calls in a stable order inside one node. We then pause parallel nodes in the same step and match each reply to its interrupt id."),
    code('''
    class Checks(TypedDict):
        answers: Annotated[list[str], operator.add]

    def sequential(state):
        print("review entered")
        safety = interrupt({"check": "safety", "work_order": work_order["wo_id"]})
        budget = interrupt({"check": "budget", "part": part["part_no"]})
        return {"answers": [f"safety={safety}", f"budget={budget}"]}

    seq = StateGraph(Checks).add_node("review", sequential).add_edge(START, "review").add_edge("review", END).compile(checkpointer=InMemorySaver())
    seq_cfg = config("sequential")
    out = seq.invoke({"answers": []}, seq_cfg, version="v2")
    print("first:", out.interrupts[0].value)
    out = seq.invoke(Command(resume="inspection required"), seq_cfg, version="v2")
    print("second:", out.interrupts[0].value)
    out = seq.invoke(Command(resume="approved budget"), seq_cfg, version="v2")
    print("answers:", out.value["answers"])
    assert len(out.value["answers"]) == 2

    def safety(state):
        answer = interrupt({"check": "safety", "work_order": work_order["wo_id"]})
        return {"answers": [f"safety={answer}"]}

    def budget(state):
        answer = interrupt({"check": "budget", "part": part["part_no"]})
        return {"answers": [f"budget={answer}"]}

    parallel = StateGraph(Checks)
    parallel.add_node("safety", safety)
    parallel.add_node("budget", budget)
    for name in ("safety", "budget"):
        parallel.add_edge(START, name)
        parallel.add_edge(name, END)
    checks = parallel.compile(checkpointer=InMemorySaver())
    check_cfg = config("parallel")
    out = checks.invoke({"answers": []}, check_cfg, version="v2")
    print("pending:", [(item.id, item.value) for item in out.interrupts])
    replies = {item.id: f"approved {item.value['check']}" for item in out.interrupts}
    out = checks.invoke(Command(resume=replies), check_cfg, version="v2")
    print("answers:", sorted(out.value["answers"]))
    assert len(out.value["answers"]) == 2 and not out.interrupts
    '''),
], "we can reject again or change the parallel replies. We keep interrupt order stable during a paused run.")

demo(2, "interrupts-in-multi-agent", "Interrupts in multi-agent workflows", [
    section("a · in-a-subgraph", "We compile a child workflow without its own saver and give the parent a checkpointer. The child's approval appears in the parent's result. We resume the parent with the same thread id."),
    code(COMMON),
    code('''
    class Job(TypedDict):
        work_order: str
        draft: str
        approved: bool
        result: str

    def draft_job(state: Job):
        return {"draft": llm.invoke(f"Write a short inspection proposal for Veenhaven Bus. Use only these facts: {state['work_order']}").content}

    def approve_job(state: Job):
        answer = interrupt({"draft": state["draft"], "work_order": work_order["wo_id"]})
        return {"approved": answer["approved"]}

    child_builder = StateGraph(Job)
    child_builder.add_node("draft", draft_job)
    child_builder.add_node("approval", approve_job)
    child_builder.add_edge(START, "draft")
    child_builder.add_edge("draft", "approval")
    child_builder.add_edge("approval", END)
    child = child_builder.compile()
    parent_builder = StateGraph(Job)
    parent_builder.add_node("specialist", child)
    parent_builder.add_node("record", lambda s: {"result": s["draft"] if s["approved"] else "declined"})
    parent_builder.add_edge(START, "specialist")
    parent_builder.add_edge("specialist", "record")
    parent_builder.add_edge("record", END)
    parent = parent_builder.compile(checkpointer=InMemorySaver())
    cfg = config("subgraph")
    out = parent.invoke({"work_order": json.dumps(work_order), "draft": "", "approved": False, "result": ""}, cfg, version="v2")
    print("parent payload:", out.interrupts[0].value)
    print("parent next:", parent.get_state(cfg).next)
    for task in parent.get_state(cfg, subgraphs=True).tasks:
        print("child next:", task.state.next)
    assert out.interrupts and not out.value["result"]
    out = parent.invoke(Command(resume={"approved": True}), cfg, version="v2")
    print("parent result:", out.value["result"])
    assert out.value["approved"] and out.value["result"]
    '''),
    section("b · in-a-subagent", "We expose the child as a tool to a model supervisor. The nested interrupt passes through the tool node to the top-level caller. Resuming the supervisor re-enters the tool and delivers the reply to the child's interrupt."),
    code('''
    tool_entries = []

    @tool
    def inspection_specialist(work_order_id: str) -> str:
        """Ask the inspection specialist to propose and approve work for a work order."""
        if work_order_id != work_order["wo_id"]:
            raise ValueError("Unknown work order")
        tool_entries.append(work_order_id)
        print("tool entered:", work_order_id)
        result = child.invoke({"work_order": json.dumps(work_order), "draft": "", "approved": False, "result": ""})
        return json.dumps({"approved": result["approved"], "draft": result["draft"]})

    supervisor = create_agent(llm, tools=[inspection_specialist],
        system_prompt="Call inspection_specialist once for the requested work order. Report the returned approval and proposal. Do not call it again after a result.",
        checkpointer=InMemorySaver())
    supervisor_cfg = config("subagent")
    out = supervisor.invoke({"messages": [("human", "Request the inspection specialist's proposal for BW-7001.")]}, supervisor_cfg, version="v2")
    print("top-level payload:", [item.value for item in out.interrupts])
    assert len(out.interrupts) == 1
    print("top-level next:", supervisor.get_state(supervisor_cfg).next)
    print("tool entries before resume:", len(tool_entries))
    out = supervisor.invoke(Command(resume={"approved": True}), supervisor_cfg, version="v2")
    print("tool entries after resume:", len(tool_entries))
    for message in out.value["messages"]:
        if isinstance(message, ToolMessage):
            print("specialist result:", message.content)
            assert json.loads(message.content)["approved"] is True
    print("supervisor:", out.value["messages"][-1].content)
    assert not out.interrupts and len(tool_entries) == 2
    '''),
    md("We leave nested invocation configuration to LangGraph's propagation. We do not create a separate child thread or turn its interrupt into a normal tool result. Tool code before the nested call runs again, so we put external actions after approval and use idempotency keys."),
], "we can resume the top-level supervisor with approval set to false and inspect the tool result.")

demo(3, "human-in-the-loop-middleware", "Human-in-the-loop middleware", [
    section("a · approval-policy", "We gate a simulated part reservation with `HumanInTheLoopMiddleware`. We use fresh threads for approval, editing and rejection. The model chooses the proposed arguments, so we inspect the pending action before supplying a decision."),
    code(COMMON),
    code('''
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    reservations = []

    @tool
    def reserve_part(part_no: str, quantity: int) -> str:
        """Record a simulated reservation of a Veenhaven Bus part, without updating the database."""
        if part_no != part["part_no"] or not 0 < quantity <= part["stock"]:
            raise ValueError("Invalid reservation")
        reservations.append({"part_no": part_no, "quantity": quantity})
        return json.dumps(reservations[-1])

    policy = HumanInTheLoopMiddleware(interrupt_on={
        "reserve_part": {"allowed_decisions": ["approve", "edit", "reject"]}
    })
    agent = create_agent(llm, tools=[reserve_part], middleware=[policy],
        system_prompt="Call reserve_part once with the requested arguments. After a tool result, report it and stop. After rejection, stop without retrying. An edited result is authoritative.",
        checkpointer=InMemorySaver())

    for choice in ("approve", "edit", "reject"):
        cfg = config(choice)
        before = len(reservations)
        out = agent.invoke({"messages": [("human", f"Reserve 2 of {part['part_no']} for BW-7001.")]}, cfg, version="v2")
        assert len(out.interrupts) == 1 and len(reservations) == before
        pending = out.interrupts[0].value
        print("actions:", pending["action_requests"])
        print("allowed:", pending["review_configs"])
        assert len(pending["action_requests"]) == 1
        decision = {"type": choice}
        if choice == "edit":
            decision["edited_action"] = {"name": "reserve_part", "args": {"part_no": part["part_no"], "quantity": 1}}
        if choice == "reject":
            decision["message"] = "Reservation denied. Abandon the reservation and do not retry."
        out = agent.invoke(Command(resume={"decisions": [decision]}), cfg, version="v2")
        assert not out.interrupts
        print("decision:", choice)
        print("new reservations:", reservations[before:])
        for message in out.value["messages"]:
            if isinstance(message, AIMessage) and message.tool_calls:
                print("model call:", message.tool_calls)
            if isinstance(message, ToolMessage):
                print("tool:", message.status, message.content)
        print("answer:", out.value["messages"][-1].content)
        assert len(reservations) - before == (0 if choice == "reject" else 1)
        if choice == "edit":
            assert reservations[-1]["quantity"] == 1
    '''),
    md("We return one decision per pending action, in the action list's order. Editing uses `edited_action.args`, although the request uses `arguments`. On the installed stack the AI message keeps its original call; the tool result includes a reviewer-edit notice. Rejection creates an error tool message without executing the tool."),
], "we can restrict the policy to approve and reject, or request several reservations and supply one decision per action.")

demo(4, "loop-detection", "Loop detection", [
    section("a · watchdog-node", "We let a model propose another inspection while a watchdog measures progress in state. A scripted lack of progress makes the stopping condition repeatable. The recursion limit remains an outer bound on graph steps."),
    code(COMMON),
    code('''
    from langgraph.errors import GraphRecursionError

    class Investigation(TypedDict):
        attempts: int
        evidence: str
        previous: str
        stalled: int
        proposal: str
        status: str

    def investigate(state):
        proposal = llm.invoke(f"Suggest a short inspection action for {work_order}. Evidence remains unchanged: {state['evidence']}. Do not claim an inspection was performed.").content
        return {"attempts": state["attempts"] + 1, "proposal": proposal}

    def watchdog(state):
        stalled = state["stalled"] + 1 if state["evidence"] == state["previous"] else 0
        stop = stalled >= 2 or state["attempts"] >= 4
        print("watchdog:", state["attempts"], stalled, "stop" if stop else "continue")
        return {"previous": state["evidence"], "stalled": stalled,
                "status": "manual review" if stop else "continue"}

    def route(state) -> Literal["investigate", "manual"]:
        return "manual" if state["status"] == "manual review" else "investigate"

    watch = StateGraph(Investigation)
    watch.add_node("investigate", investigate)
    watch.add_node("watchdog", watchdog)
    watch.add_node("manual", lambda s: {"status": "manual review queued"})
    watch.add_edge(START, "investigate")
    watch.add_edge("investigate", "watchdog")
    watch.add_conditional_edges("watchdog", route)
    watch.add_edge("manual", END)
    initial = {"attempts": 0, "evidence": work_order["summary"], "previous": work_order["summary"], "stalled": 0, "proposal": "", "status": ""}
    out = watch.compile().invoke(initial, {"recursion_limit": 12})
    print("status:", out["status"])
    print("proposal:", out["proposal"])
    assert out["attempts"] == 2 and out["status"] == "manual review queued"

    bound = StateGraph(Investigation)
    bound.add_node("spin", lambda s: {"attempts": s["attempts"] + 1})
    bound.add_edge(START, "spin")
    bound.add_edge("spin", "spin")
    try:
        bound.compile().invoke(initial, {"recursion_limit": 4})
    except GraphRecursionError as exc:
        print("outer bound:", type(exc).__name__)
    '''),
    section("b · repeated-tool-calls", "We obtain a stock tool call from the course model, then replay the same name and arguments with a new call id. We compare canonical arguments before execution. Identical read requests without new evidence stop the run; call limits from module 04 provide a separate bound."),
    code('''
    @tool
    def read_stock(part_no: str) -> str:
        """Read stock for the supported Veenhaven Bus part."""
        return json.dumps(part) if part_no == part["part_no"] else "Unknown part"

    proposed = llm.bind_tools([read_stock], tool_choice="read_stock", parallel_tool_calls=False).invoke(
        f"Read stock for {part['part_no']}."
    )
    assert len(proposed.tool_calls) == 1
    first = proposed.tool_calls[0]
    repeated = AIMessage("", tool_calls=[{**first, "id": "repeat-2"}])

    class Calls(MessagesState):
        seen: list[str]
        executed: int
        blocked: bool

    def signature(call):
        return json.dumps({"name": call["name"], "args": call["args"]}, sort_keys=True)

    def guard(state):
        calls = state["messages"][-1].tool_calls
        duplicate = any(signature(call) in state["seen"] for call in calls)
        return {"blocked": duplicate}

    def execute(state):
        call = state["messages"][-1].tool_calls[0]
        return {"messages": [ToolMessage(read_stock.invoke(call["args"]), tool_call_id=call["id"])],
                "seen": [*state["seen"], signature(call)], "executed": state["executed"] + 1}

    def replay(state):
        return {"messages": [repeated]}

    def stop(state):
        call = state["messages"][-1].tool_calls[0]
        return {"messages": [ToolMessage("Repeated unchanged read blocked; manual review required.", tool_call_id=call["id"], status="error")]}

    calls = StateGraph(Calls)
    calls.add_node("guard", guard)
    calls.add_node("execute", execute)
    calls.add_node("replay", replay)
    calls.add_node("stop", stop)
    calls.add_edge(START, "guard")
    calls.add_conditional_edges("guard", lambda s: "stop" if s["blocked"] else "execute", {"stop": "stop", "execute": "execute"})
    calls.add_edge("execute", "replay")
    calls.add_edge("replay", "guard")
    calls.add_edge("stop", END)
    out = calls.compile().invoke({"messages": [HumanMessage("Check stock"), proposed], "seen": [], "executed": 0, "blocked": False})
    print("signature:", out["seen"])
    print("executed:", out["executed"], "blocked:", out["blocked"])
    print("result:", out["messages"][-1].content)
    assert out["executed"] == 1 and out["blocked"]
    '''),
    md("We scope duplicate detection to a run with unchanged evidence. Polling live data can legitimately repeat a read; a policy can include an evidence version or a freshness window. A successful tool call and its retry are separate from an agent asking again."),
], "we can change the replayed arguments or reset stalled progress when new inspection evidence arrives.")

demo(5, "retries-and-fallbacks", "Retries and fallbacks", [
    section("a · backoff", "We build on module 04's retry policy and record increasing delays around an injected transient stock-service failure. We disable jitter only to make the demonstration visible. Retrying a read does not authorise repeating a purchase."),
    code(COMMON),
    code('''
    from langgraph.types import RetryPolicy

    class Stock(TypedDict):
        part_no: str
        stock: int
        source: str
        answer: str

    attempts = []
    def remote_stock(state):
        attempts.append(time.perf_counter())
        print("attempt:", len(attempts))
        if len(attempts) < 3:
            raise ConnectionError("injected transient stock-service outage")
        return {"stock": part["stock"], "source": "simulated live service"}

    def explain(state):
        return {"answer": llm.invoke(f"Write a short Veenhaven Bus stock report using only: {state}. Do not reserve stock.").content}

    retry = StateGraph(Stock)
    retry.add_node("lookup", remote_stock, retry_policy=RetryPolicy(
        max_attempts=3, initial_interval=0.1, backoff_factor=2, max_interval=0.3,
        jitter=False, retry_on=ConnectionError))
    retry.add_node("explain", explain)
    retry.add_edge(START, "lookup")
    retry.add_edge("lookup", "explain")
    retry.add_edge("explain", END)
    initial = {"part_no": part["part_no"], "stock": 0, "source": "", "answer": ""}
    out = retry.compile().invoke(initial)
    print("gaps:", [round(b - a, 3) for a, b in zip(attempts, attempts[1:])])
    print("answer:", out["answer"])
    assert len(attempts) == 3 and out["stock"] == part["stock"]
    '''),
    section("b · fallback-chain", "We try a live lookup, a dated local snapshot and a manual-review result in that order. We disclose the source and never let a snapshot authorise a reservation. Module 04's model fallback handles a model outage; this chain handles missing business data."),
    code('''
    from langchain_core.runnables import RunnableLambda

    def live(request):
        print("source: live unavailable")
        raise ConnectionError("injected live outage")

    def snapshot(request):
        if request["part_no"] != part["part_no"]:
            print("source: snapshot missing")
            raise LookupError("part absent from snapshot")
        print("source: snapshot")
        return {"part_no": part["part_no"], "stock": part["stock"],
                "source": "course snapshot, freshness unverified", "may_reserve": False}

    def manual(request):
        print("source: manual review")
        return {"part_no": request["part_no"], "stock": None,
                "source": "manual stock check required", "may_reserve": False}

    chain = RunnableLambda(live).with_fallbacks(
        [RunnableLambda(snapshot), RunnableLambda(manual)],
        exceptions_to_handle=(ConnectionError, LookupError))
    known = chain.invoke({"part_no": part["part_no"]})
    unknown = chain.invoke({"part_no": "UNKNOWN"})
    print("known:", known)
    print("unknown:", unknown)
    report = llm.invoke(f"Explain these Veenhaven Bus stock results concisely. Preserve uncertainty and do not authorise a reservation: {known}; {unknown}").content
    print("report:", report)
    assert known["stock"] == part["stock"] and unknown["stock"] is None
    assert not known["may_reserve"] and not unknown["may_reserve"]
    '''),
], "we can change the transient-failure count or remove the local snapshot and observe the manual-review fallback.")

demo(6, "composition-and-durability", "Composition and durability", [
    section("a · composing-workflows", "We port the compiled-subgraph shape from ARI510 and compose lookup and report workflows. Shared state keys pass through directly. A wrapper maps state when a child has a different schema."),
    code(COMMON),
    code('''
    class Work(TypedDict):
        wo_id: str
        facts: str
        report: str
        queue: str
        status: str

    def lookup(state):
        with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM work_orders WHERE wo_id = ?", (state["wo_id"],)).fetchone()
        if row is None:
            raise ValueError("Unknown work order")
        return {"facts": json.dumps(dict(row))}

    lookup_builder = StateGraph(Work)
    lookup_builder.add_node("lookup", lookup)
    lookup_builder.add_edge(START, "lookup")
    lookup_builder.add_edge("lookup", END)
    lookup_workflow = lookup_builder.compile()

    class ReportInput(TypedDict):
        source: str
        text: str

    def report(state):
        return {"text": llm.invoke(f"Summarise this Veenhaven Bus work order in one short sentence. Do not add facts: {state['source']}").content}

    report_builder = StateGraph(ReportInput)
    report_builder.add_node("report", report)
    report_builder.add_edge(START, "report")
    report_builder.add_edge("report", END)
    report_workflow = report_builder.compile()

    def mapped_report(state):
        child = report_workflow.invoke({"source": state["facts"], "text": ""})
        return {"report": child["text"]}

    composed = StateGraph(Work)
    composed.add_node("lookup_workflow", lookup_workflow)
    composed.add_node("report_workflow", mapped_report)
    composed.add_edge(START, "lookup_workflow")
    composed.add_edge("lookup_workflow", "report_workflow")
    composed.add_edge("report_workflow", END)
    initial = {"wo_id": work_order["wo_id"], "facts": "", "report": "", "queue": "", "status": ""}
    out = composed.compile().invoke(initial)
    print("facts:", out["facts"])
    print("report:", out["report"])
    assert out["facts"] and out["report"]
    '''),
    section("b · branching-at-scale", "We keep a routing registry separate from node implementations. Business rules route validated fault codes to a specialist queue or manual review. Unknown codes use an explicit default path."),
    code('''
    from functools import partial

    routes = {"F-CE": "electric", "F-MM": "diesel", "F-CD": "doors"}
    def classify(state):
        code = json.loads(state["facts"])["error_code"]
        return {"queue": routes.get(code[:4], "manual")}

    def queue_work(state, queue):
        return {"status": f"queued for {queue}"}

    branching = StateGraph(Work)
    branching.add_node("lookup", lookup_workflow)
    branching.add_node("classify", classify)
    for name in sorted(set(routes.values()) | {"manual"}):
        branching.add_node(name, partial(queue_work, queue=name))
        branching.add_edge(name, END)
    branching.add_edge(START, "lookup")
    branching.add_edge("lookup", "classify")
    path_map = {name: name for name in set(routes.values()) | {"manual"}}
    branching.add_conditional_edges("classify", lambda s: s["queue"], path_map)
    routed = branching.compile().invoke(initial)
    print("route:", routed["queue"], routed["status"])
    assert routed["queue"] == "electric"
    fallback_input = {**initial, "facts": json.dumps({"error_code": "UNKNOWN"})}
    print("unknown route:", classify(fallback_input))
    assert classify(fallback_input)[\"queue\"] == \"manual\"
    '''),
    section("c · resuming-after-a-crash", "We save lookup and model output before a node raises an injected crash. We close the SQLite connection and rebuild the graph, then resume the same thread with `None`. An approval interrupt instead requires `Command(resume=...)`."),
    code('''
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.errors import GraphDrained
    from langgraph.runtime import RunControl, Runtime

    crash = {"enabled": True}
    drain_request = {"enabled": False}
    executions = {"prepare": 0, "finish": 0}

    def prepare(state, runtime: Runtime):
        executions["prepare"] += 1
        update = lookup(state)
        update["report"] = llm.invoke(f"Draft a short Veenhaven Bus inspection note. Use only: {update['facts']}").content
        if drain_request["enabled"] and runtime.control is not None:
            runtime.control.request_drain("trainer shutdown")
        return update

    def finish(state):
        executions["finish"] += 1
        if crash["enabled"]:
            raise RuntimeError("injected worker crash before recording")
        return {"status": "inspection note recorded"}

    def durable_builder():
        graph = StateGraph(Work)
        graph.add_node("prepare", prepare)
        graph.add_node("finish", finish)
        graph.add_edge(START, "prepare")
        graph.add_edge("prepare", "finish")
        graph.add_edge("finish", END)
        return graph

    checkpoint_file = Path("workflow-checkpoints.sqlite")
    if checkpoint_file.exists():
        checkpoint_file.unlink()
    crash_cfg = config("crash")
    calls_before = usage.calls
    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        running = durable_builder().compile(checkpointer=saver)
        try:
            running.invoke(initial, crash_cfg, durability="sync")
        except RuntimeError as exc:
            print("crash:", str(exc))
        saved = running.get_state(crash_cfg)
        print("saved next:", saved.next)
        print("saved report:", saved.values["report"])
        assert saved.next == ("finish",) and saved.values["report"]
        assert executions == {"prepare": 1, "finish": 1}

    crash["enabled"] = False
    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        restarted = durable_builder().compile(checkpointer=saver)
        print("reopened next:", restarted.get_state(crash_cfg).next)
        recovered = restarted.invoke(None, crash_cfg, durability="sync")
        print("recovered:", recovered["status"])
        print("executions:", executions)
        print("model calls:", usage.calls - calls_before)
        assert recovered["status"] == "inspection note recorded"
        assert executions == {"prepare": 1, "finish": 2}
        assert usage.calls - calls_before == 1
    '''),
    md("We also request a graceful drain inside the running preparation node. The node completes and its update is saved before the next node starts. A production signal handler can request the same drain from another thread."),
    code('''
    drain_request["enabled"] = True
    drain_cfg = config("drain")
    control = RunControl()
    before = dict(executions)
    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        running = durable_builder().compile(checkpointer=saver)
        try:
            running.invoke(initial, drain_cfg, control=control, durability="sync")
        except GraphDrained as exc:
            print("drained:", exc.reason)
        print("drained next:", running.get_state(drain_cfg).next)
        assert running.get_state(drain_cfg).next == ("finish",)
        assert executions["finish"] == before["finish"]
    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        restarted = durable_builder().compile(checkpointer=saver)
        resumed = restarted.invoke(None, drain_cfg, control=RunControl(), durability="sync")
        print("resumed:", resumed["status"])
        assert resumed["status"] == "inspection note recorded"
    '''),
    md("We use a new control object for the resumed run. Drain is cooperative and does not cancel in-flight work. A checkpoint cannot undo external writes; recording a real reservation still requires a stable idempotency key and a persistent backend."),
], "we can crash before preparation completes and compare the repeated model calls with the crash after its checkpoint.")
