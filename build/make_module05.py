"""Generate the nine module 05 notebooks. Run with uv run python build/make_module05.py."""
from nb import code, md, section, write_demo

MODULE = "05-multi-agent-patterns"

COMMON = r'''
import json
import operator
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Annotated, Literal
from typing_extensions import NotRequired, TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import wrap_model_call
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, Send
from pydantic import BaseModel, Field


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
llm = make_llm(callbacks=[counter], max_tokens=1200, max_retries=0)
metrics = []


def measured(label, operation):
    counter.reset()
    start = time.perf_counter()
    try:
        return operation()
    finally:
        row = dict(pattern=label, calls=counter.calls, input_tokens=counter.input,
                   output_tokens=counter.output, seconds=round(time.perf_counter() - start, 1),
                   malformed=counter.invalid, errors=counter.errors)
        metrics.append(row)
        print("metrics :", json.dumps(row))


DB = Path(data("demo-world/service.db")).resolve()
MANUALS = Path(data_folder("demo-world/manuals"))
PAGES = {p.name: p.read_text(encoding="utf-8") for p in sorted(MANUALS.glob("*.md"))}


@tool
def part_stock(part: str) -> str:
    """Look up the stock, location and name of a Veenhaven Bus part number."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, name, stock, depot FROM parts WHERE part_no = ?",
                          (part.upper(),)).fetchall()
    return json.dumps(rows)


@tool
def fault_guidance(error_code: str) -> str:
    """Read the manual's meaning and first action for a Veenhaven Bus error code."""
    matches = [f"[{name}]\n{line}" for name, text in PAGES.items()
               for line in text.splitlines() if line.startswith("| " + error_code.upper() + " |")]
    return "\n".join(matches) or "No matching error code."


@tool
def run_sql(query: str) -> str:
    """Run a read-only SELECT. Tables: buses(fleet_no, model, depot_id, commissioned, firmware),
    depots(depot_id, name, city, contract), parts(part_no, model, name, stock, price_eur, depot),
    work_orders(wo_id, fleet_no, opened, status, error_code, summary, mechanic_id)."""
    if not query.lstrip().lower().startswith("select"):
        return "Only SELECT statements are allowed."
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        return json.dumps(db.execute(query).fetchmany(30))


@tool
def search_manuals(query: str) -> str:
    """Find relevant Veenhaven Bus manuals and bulletins with their file names."""
    words = set(query.lower().split())
    ranked = sorted(PAGES, key=lambda name: -sum(PAGES[name].lower().count(w) for w in words))[:3]
    return "\n\n".join(f"[{name}]\n{PAGES[name]}" for name in ranked)


QUESTION = ("Bus CE12-2021-0117 shows F-CE-110. How many CE-CF-02 cooling fans are in stock, "
            "at which location, and what are the manual's first action and replacement condition for this error? Be brief.")
STOCK_TASK = "How many CE-CF-02 cooling fans are in stock and at which location?"
MANUAL_TASK = "What are the meaning, first action and replacement condition for F-CE-110? Cite the manual."
LIMIT = {"recursion_limit": 24}


def ask(question):
    return {"messages": [HumanMessage(question)]}


def last_text(result):
    return str(next(m.content for m in reversed(result["messages"])
                    if isinstance(m, AIMessage) and m.content and not m.tool_calls))


def agent_by_hand(model, tools, prompt, state_schema=MessagesState):
    bound = model.bind_tools(tools)

    def model_node(state):
        return {"messages": [bound.invoke([SystemMessage(prompt), *state["messages"]])]}

    graph = StateGraph(state_schema)
    graph.add_node("model", model_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile()


def specialists(model):
    return {
        "parts": agent_by_hand(model, [part_stock], "Answer stock questions from the tool. Return every fact briefly."),
        "manuals": agent_by_hand(model, [fault_guidance], "Answer error-code questions from the manual tool. Cite its file."),
    }


def compose(model, question, findings):
    return model.invoke("Answer from these findings only. Preserve counts, locations and conditions.\n"
                        + question + "\n" + "\n".join(findings)).content


def completeness(answer):
    text = answer.lower()
    return {"stock": bool(re.search(r"\b(6|six)\b", text)) and "rietpoort" in text,
            "action": "fan" in text and "airflow" in text and bool(re.search(r"\b(80|eighty)\b", text))}
'''

SUBAGENTS = r'''
workers = specialists(llm)
inner = {}


@tool
def call_parts(question: str) -> str:
    """Ask the parts specialist about stock and location."""
    result = workers["parts"].invoke(ask(question), LIMIT)
    inner.setdefault("parts", []).append(result["messages"])
    return last_text(result)


@tool
def call_manuals(question: str) -> str:
    """Ask the manuals specialist about error meanings and first actions."""
    result = workers["manuals"].invoke(ask(question), LIMIT)
    inner.setdefault("manuals", []).append(result["messages"])
    return last_text(result)


coordinator = agent_by_hand(llm, [call_parts, call_manuals],
                           "Coordinate Veenhaven Bus maintenance. Delegate both data questions, then answer briefly.")
result = measured("subagents", lambda: coordinator.invoke(ask(QUESTION), LIMIT))
print("outer :", [m.type for m in result["messages"]])
print("inner :", {name: [len(messages) for messages in runs] for name, runs in inner.items()})
print("answer :", last_text(result))
print("checks :", completeness(last_text(result)))
'''

SUPERVISOR = r'''
class TeamState(TypedDict):
    question: str
    findings: dict[str, str]
    next: str
    task: str
    rounds: int
    answer: str


class Decision(BaseModel):
    next: Literal["parts", "manuals", "finish"]
    task: str


def supervisor_graph(model):
    workers = specialists(model)

    def supervise(state):
        if len(state["findings"]) == 2 or state["rounds"] >= 2:
            return {"next": "finish"}
        decision = model.with_structured_output(Decision).invoke(
            "Select an unfinished worker: parts for stock, manuals for error guidance. "
            "Do not repeat a worker.\nQuestion: " + state["question"]
            + "\nCompleted: " + json.dumps(state["findings"]))
        print("supervisor :", decision.next, decision.task)
        return {"next": decision.next, "task": decision.task}

    def worker(name):
        def node(state):
            task = state["task"]
            answer = last_text(workers[name].invoke(ask(task), LIMIT))
            return {"findings": {**state["findings"], name: answer}, "rounds": state["rounds"] + 1}
        return node

    graph = StateGraph(TeamState)
    graph.add_node("supervisor", supervise)
    for name in workers:
        graph.add_node(name, worker(name))
        graph.add_edge(name, "supervisor")
    graph.add_node("finish", lambda s: {"answer": compose(model, s["question"], list(s["findings"].values()))})
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", lambda s: s["next"], ["parts", "manuals", "finish"])
    graph.add_edge("finish", END)
    return graph.compile()


def team_input(question):
    return {"question": question, "findings": {}, "rounds": 0, "next": "", "task": "", "answer": ""}


team = supervisor_graph(llm)
result = measured("supervisor", lambda: team.invoke(team_input(QUESTION), LIMIT))
print("workers :", list(result["findings"]))
print("answer :", result["answer"])
print("checks :", completeness(result["answer"]))
'''

ROUTER = r'''
class Route(BaseModel):
    agent: Literal["parts", "manuals"]
    query: str


class Routes(BaseModel):
    routes: list[Route] = Field(min_length=1, max_length=2)


class RouterState(TypedDict):
    question: str
    routes: list[dict]
    answers: Annotated[list[str], operator.add]
    final: str


def router_graph(model, parallel):
    workers = specialists(model)

    def classify(state):
        routes = model.with_structured_output(Routes).invoke(
            "Choose the required specialists. parts handles stock, manuals handles error codes. "
            "At most one question per specialist.\n" + state["question"]).routes
        print("routes :", [(r.agent, r.query) for r in routes])
        return {"routes": [r.model_dump() for r in routes]}

    def dispatch(state):
        return [Send(r["agent"], {"question": r["query"]}) for r in state["routes"]]

    def specialist(name):
        return lambda s: {"answers": [name + " : " + last_text(workers[name].invoke(ask(s["question"]), LIMIT))]}

    def sequential_dispatch(state):
        return {"answers": [r["agent"] + " : " + last_text(workers[r["agent"]].invoke(ask(r["query"]), LIMIT))
                            for r in state["routes"]]}

    graph = StateGraph(RouterState)
    graph.add_node("classify", classify)
    graph.add_node("synthesise", lambda s: {"final": compose(model, s["question"], s["answers"])})
    graph.add_edge(START, "classify")
    if parallel:
        for name in workers:
            graph.add_node(name, specialist(name))
            graph.add_edge(name, "synthesise")
        graph.add_conditional_edges("classify", dispatch, ["parts", "manuals"])
    else:
        graph.add_node("dispatch", sequential_dispatch)
        graph.add_edge("classify", "dispatch")
        graph.add_edge("dispatch", "synthesise")
    graph.add_edge("synthesise", END)
    return graph.compile()


result = measured("router sequential", lambda: router_graph(llm, False).invoke(
    {"question": STOCK_TASK, "answers": []}, LIMIT))
print("answer :", result["final"])
'''

HANDOFF = r'''
class HandoffState(AgentState):
    active_agent: NotRequired[str]


def transfer(target, full_history):
    @tool("transfer_to_" + target)
    def move(runtime: ToolRuntime) -> Command:
        """Transfer the conversation to the other specialist."""
        note = ToolMessage(content="Transferred to " + target, tool_call_id=runtime.tool_call_id)
        messages = runtime.state["messages"]
        forwarded = messages if full_history else [next(m for m in reversed(messages) if isinstance(m, AIMessage))]
        return Command(goto=target, graph=Command.PARENT,
                       update={"active_agent": target, "messages": [*forwarded, note]})
    return move


def handoff_graph(model, fixed=True):
    handoff_model = model.model_copy(update={"model_kwargs": {**model.model_kwargs, "parallel_tool_calls": False}}) if fixed else model
    parts = agent_by_hand(handoff_model, [part_stock, transfer("manuals_agent", fixed)],
                          "Look up the stock first. Then transfer to manuals_agent if the error guidance is unanswered.", HandoffState)
    manuals = agent_by_hand(handoff_model, [fault_guidance, transfer("parts_agent", fixed)],
                            "Look up error guidance. Transfer only if stock is still unanswered. "
                            "When both facts are present, give one complete brief answer.", HandoffState)

    def route(state):
        last = state["messages"][-1]
        return END if isinstance(last, AIMessage) and not last.tool_calls else state["active_agent"]

    graph = StateGraph(HandoffState)
    graph.add_node("parts_agent", lambda s: parts.invoke(s, LIMIT))
    graph.add_node("manuals_agent", lambda s: manuals.invoke(s, LIMIT))
    graph.add_conditional_edges(START, lambda s: s.get("active_agent", "parts_agent"), ["parts_agent", "manuals_agent"])
    for name in ["parts_agent", "manuals_agent"]:
        graph.add_conditional_edges(name, route, ["parts_agent", "manuals_agent", END])
    return graph.compile()


def seeded_failure(parallel):
    stock_call = AIMessage(content="", tool_calls=[{"name": "part_stock", "args": {"part": "CE-CF-02"}, "id": "stock-1", "type": "tool_call"}])
    move_call = {"name": "transfer_to_manuals_agent", "args": {}, "id": "move-1", "type": "tool_call"}
    trigger = AIMessage(content="", tool_calls=[*stock_call.tool_calls, move_call] if parallel else [move_call])
    stock_result = ToolMessage(content=part_stock.invoke({"part": "CE-CF-02"}), tool_call_id="stock-1")

    def seed(state):
        return {"messages": [trigger] if parallel else [stock_call, stock_result, trigger]}

    child = StateGraph(HandoffState)
    child.add_node("seed", seed)
    child.add_node("tools", ToolNode([part_stock, transfer("manuals_agent", False)]))
    child.add_edge(START, "seed")
    child.add_edge("seed", "tools")
    child.add_edge("tools", END)

    def receive(state):
        print("received :", [(m.type, str(m.content)[:140]) for m in state["messages"]])
        response = llm.invoke([SystemMessage("Answer using only the visible facts and the manual excerpt. "
                                            "If the stock count is missing, say it is unavailable.\n"
                                            + fault_guidance.invoke({"error_code": "F-CE-110"})), *state["messages"]])
        return {"messages": [response]}

    parent = StateGraph(HandoffState)
    parent.add_node("parts_agent", child.compile())
    parent.add_node("manuals_agent", receive)
    parent.add_edge(START, "parts_agent")
    parent.add_edge("manuals_agent", END)
    return parent.compile().invoke(ask(QUESTION), LIMIT)
'''

SKILLS = r'''
SKILLS = {
    "parts": "Use part_stock to report the part number, count and location. Do not promise a reservation.",
    "manuals": "Use fault_guidance. Cite the file, preserve conditions, and distinguish inspection from replacement.",
}


@tool
def load_skill(name: str) -> str:
    """Load task instructions. Names: parts for stock; manuals for error-code guidance."""
    return SKILLS.get(name, "Unknown skill.")


skilled = agent_by_hand(llm, [load_skill, part_stock, fault_guidance],
                       "You support Veenhaven Bus. Load each matching skill before using its tools. Be brief.")
result = measured("skills", lambda: skilled.invoke(ask(QUESTION), LIMIT))
print("tools :", [m.name for m in result["messages"] if isinstance(m, ToolMessage)])
print("answer :", last_text(result))
print("checks :", completeness(last_text(result)))
'''

WORKFLOW = r'''
class WorkflowState(TypedDict):
    question: str
    stock: str
    guidance: str
    answer: str


def workflow_graph(model, parallel):
    workers = specialists(model)
    graph = StateGraph(WorkflowState)
    graph.add_node("parts", lambda s: {"stock": last_text(workers["parts"].invoke(ask(STOCK_TASK), LIMIT))})
    graph.add_node("manuals", lambda s: {"guidance": last_text(workers["manuals"].invoke(ask(MANUAL_TASK), LIMIT))})
    graph.add_node("compose", lambda s: {"answer": compose(model, s["question"], [s["stock"], s["guidance"]])})
    graph.add_edge(START, "parts")
    if parallel:
        graph.add_edge(START, "manuals")
        graph.add_edge(["parts", "manuals"], "compose")
    else:
        graph.add_edge("parts", "manuals")
        graph.add_edge("manuals", "compose")
    graph.add_edge("compose", END)
    return graph.compile()
'''

CHECKER = r'''
class Review(BaseModel):
    approved: bool
    feedback: str


class DraftState(TypedDict):
    task: str
    draft: str
    feedback: str
    approved: bool
    rounds: int


EVIDENCE = part_stock.invoke({"part": "CE-CF-02"}) + "\n" + part_stock.invoke({"part": "CE-DA-03"})
TASK = "Write a parts note naming CE-CF-02 and CE-DA-03, their stock counts and locations. Mark zero stock as 'out of stock'."


def check_note(draft):
    problems = []
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        expected = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no IN (?, ?)",
                              ("CE-CF-02", "CE-DA-03")).fetchall()
    for part, count, location in expected:
        lines = [line.lower() for line in draft.splitlines() if part.lower() in line.lower()]
        if not lines:
            problems.append("Include " + part)
        elif not any(re.search(r"\b" + str(count) + r"\b", line) and location.lower() in line
                     and (count != 0 or "out of stock" in line) for line in lines):
            problems.append(f"Put {part}, stock {count}, {location}" + (", and 'out of stock'" if count == 0 else "") + " on one line.")
    return problems


def maker_checker(model, code_check=False):
    def make(state):
        draft = model.invoke(state["task"] + "\nEvidence:\n" + EVIDENCE
                             + "\nFeedback:\n" + state["feedback"] + "\nPrevious draft:\n" + state["draft"]).content
        return {"draft": draft, "rounds": state["rounds"] + 1}

    def check(state):
        if code_check:
            problems = check_note(state["draft"])
            approved, feedback = not problems, "\n".join(problems)
        else:
            review = model.with_structured_output(Review).invoke(
                "Check that both named parts, their counts and locations match the evidence. "
                "Zero stock needs 'out of stock'.\nEvidence:\n" + EVIDENCE + "\nDraft:\n" + state["draft"])
            approved, feedback = review.approved, review.feedback
        print("review :", state["rounds"], approved, feedback)
        return {"approved": approved, "feedback": feedback}

    graph = StateGraph(DraftState)
    graph.add_node("make", make)
    graph.add_node("check", check)
    graph.add_edge(START, "make")
    graph.add_edge("make", "check")
    graph.add_conditional_edges("check", lambda s: END if s["approved"] or s["rounds"] >= 2 else "make", ["make", END])
    return graph.compile()


def draft_input():
    return {"task": TASK, "draft": "", "feedback": "", "approved": False, "rounds": 0}
'''

SELECTION = r'''
class SelectionState(TypedDict):
    task: str
    candidates: Annotated[list[dict], operator.add]
    answer: str


class Judgement(BaseModel):
    selected: Literal["inspect", "replace"]
    reason: str


def debate_graph(model):
    evidence = fault_guidance.invoke({"error_code": "F-CE-110"}) + "\n" + part_stock.invoke({"part": "CE-CF-02"})

    def propose(role):
        return lambda s: {"candidates": [{"role": role, "text": model.invoke(
            f"Assess the case for {role} first. Use the evidence, retain its conditions, do not invent tests.\n"
            + s["task"] + "\n" + evidence).content}]}

    def judge(state):
        candidates = sorted(state["candidates"], key=lambda c: c["role"])
        verdict = model.with_structured_output(Judgement).invoke(
            "Choose the supported first action. Availability alone does not justify replacement.\nEvidence:\n"
            + evidence + "\nCandidates:\n" + json.dumps(candidates))
        return {"answer": verdict.selected + " : " + verdict.reason}

    graph = StateGraph(SelectionState)
    for role in ["inspect", "replace"]:
        graph.add_node(role, propose(role))
        graph.add_edge(START, role)
    graph.add_node("judge", judge)
    graph.add_edge(["inspect", "replace"], "judge")
    graph.add_edge("judge", END)
    return graph.compile()


def generate_filter_graph(model):
    def generate(state):
        text = model.invoke(TASK + " Use one line per part and digits for counts.\n"
                            + state["task"] + "\nEvidence:\n" + EVIDENCE).content
        return {"candidates": [{"role": state["task"], "text": text}]}

    def select(state):
        checked = [(c, check_note(c["text"])) for c in state["candidates"]]
        for candidate, problems in checked:
            print("filter :", candidate["role"], problems)
        valid = [c for c, problems in checked if not problems]
        chosen = min(valid, key=lambda c: (len(c["text"]), c["role"])) if valid else None
        return {"answer": chosen["text"] if chosen else "No candidate passed the factual checks."}

    graph = StateGraph(SelectionState)
    graph.add_node("generate", generate)
    graph.add_node("select", select)
    graph.add_conditional_edges(START, lambda s: [Send("generate", {"task": style}) for style in ["Compact bullets.", "A compact table."]], ["generate"])
    graph.add_edge("generate", "select")
    graph.add_edge("select", END)
    return graph.compile()
'''


def demo(number, slug, title, cells):
    return write_demo(MODULE, f"demo{number:02}-{slug}", [
        md(f"# Demo {number:02} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        md("We use the made-up Veenhaven Bus records. We count every attempted model call, input and output tokens, and elapsed seconds, including the shared rate limiter."),
        code(COMMON), *cells,
        md("## Things to try\n\nOptional : we can change the question, inspect each context, and compare the answer checks with the call and token counts."),
    ])


demo(1, "subagents", "Subagents", [
    section("a · subagents", "We wrap specialist graphs as tools of a coordinator. Each specialist runs a model and tool loop built from LangGraph nodes."),
    code(SUBAGENTS),
    section("b · subagent-context", "We inspect the histories from the same run. The worker sees the delegated question and its own tool exchanges. The coordinator receives the worker's final answer."),
    code(r'''
for name, runs in inner.items():
    for messages in runs:
        print("worker :", name)
        print("input :", messages[0].content)
        print("history :", [(m.type, getattr(m, "name", None)) for m in messages])
print("outer tools :", [(m.name, m.content) for m in result["messages"] if isinstance(m, ToolMessage)])
print("metrics retained :", metrics[-1])
'''),
    md("We can lose a fact when the coordinator omits it from the task or the worker omits it from the return. A complete answer needs both boundaries to preserve the relevant facts."),
])

demo(2, "supervisors", "Supervisors", [
    section("a · supervisors", "We put the dispatch decision in a supervisor node. Each completed worker returns to that node. Code caps the worker rounds, and we inspect any missing findings."),
    code(SUPERVISOR),
    md("We compare each delegated task with the original request. A supervisor can omit the replacement condition even after selecting the right worker. When the action check fails, we inspect whether the condition disappeared from the task, the worker's report, or the final synthesis."),
    section("b · hierarchical-teams", "We put the supervisor graph behind a manager node. The manager receives a team report, while the team manages its own workers. This adds a context boundary and another synthesis call."),
    code(r'''
class ManagerState(TypedDict):
    question: str
    report: str
    answer: str


def manage(state):
    report = team.invoke(team_input(state["question"]), LIMIT)
    print("team workers :", list(report["findings"]))
    return {"report": report["answer"]}


manager = StateGraph(ManagerState)
manager.add_node("maintenance_team", manage)
manager.add_node("manager", lambda s: {"answer": compose(llm, s["question"], [s["report"]])})
manager.add_edge(START, "maintenance_team")
manager.add_edge("maintenance_team", "manager")
manager.add_edge("manager", END)
result = measured("hierarchical", lambda: manager.compile().invoke({"question": QUESTION}, LIMIT))
print("answer :", result["answer"])
print("checks :", completeness(result["answer"]))
'''),
    md("We keep an incomplete result visible. Another manager cannot recover a condition that never reached the team report. We can require a task schema with separate first-action and replacement-condition fields, then measure whether that boundary improves coverage."),
])

demo(3, "router", "Router", [
    section("a · router", "We classify a stock request and dispatch it to the selected specialist. We keep the routing decision visible instead of asking the coordinator to route on every turn."),
    code(ROUTER),
    section("b · router-parallel", "We route a request with independent stock and manual questions to both workers using Send. Each branch adds an answer through a reducer, and the synthesis sees the combined results."),
    code(r'''
result = measured("router parallel", lambda: router_graph(llm, True).invoke({"question": QUESTION, "answers": []}, LIMIT))
print("branches :", len(result["answers"]))
print("answer :", result["final"])
print("checks :", completeness(result["final"]))
'''),
    md("We gain independent execution, but the shared limiter still spaces the requests. Parallel dispatch alone does not establish a latency improvement."),
])

demo(4, "handoffs", "Handoffs", [
    section("a · handoffs", "We adapt the documented subgraph transfer, which forwards the last AI message and its transfer receipt. We seed the triggering tool calls so the two faults remain reproducible. The receiver still calls the live course model. Source : [LangChain handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)."),
    code(HANDOFF),
    md("We first put a stock lookup and a transfer in the same AI message. The jump forwards both tool requests but only the transfer receipt. We catch the provider's rejection so Run All continues."),
    code(r'''
def missing_sibling():
    try:
        result = seeded_failure(parallel=True)
        print("provider accepted :", last_text(result))
    except Exception as exc:
        if "No tool output found" not in str(exc) and "tool_call_ids" not in str(exc):
            raise
        print("provider error :", type(exc).__name__, str(exc)[:900])


measured("handoff missing sibling", missing_sibling)
'''),
    md("We then separate the lookup from the transfer. The history is valid, but the last-message transfer loses the earlier stock result. We read the half answer and check the missing fact."),
    code(r'''
result = measured("handoff lost work", lambda: seeded_failure(parallel=False))
print("half answer :", last_text(result))
print("checks :", completeness(last_text(result)))
'''),
    section("b · handoffs-fixed", "We disable parallel tool calls for the handoff agents and forward the full worker history with the transfer receipt. We now let both agents choose their tools live. A valid history still does not guarantee that the parts agent transfers."),
    code(r'''
result = measured("handoffs fixed", lambda: handoff_graph(llm).invoke(ask(QUESTION), LIMIT))
print("tools :", [m.name for m in result["messages"] if isinstance(m, ToolMessage)])
print("answer :", last_text(result))
print("checks :", completeness(last_text(result)))
'''),
    section("c · handoffs-one-agent", "We keep one conversation and change its prompt and tools from the active step in state. We preserve history naturally inside the agent, while middleware controls which tools each step sees."),
    code(r'''
class SupportState(AgentState):
    current_step: str
    bus: str


@tool
def record_bus(fleet_no: str, runtime: ToolRuntime[None, SupportState]) -> Command:
    """Record the fleet number supplied by the caller and move to the specialist step."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        exists = db.execute("SELECT 1 FROM buses WHERE fleet_no = ?", (fleet_no,)).fetchone()
    if not exists:
        return Command(update={"messages": [ToolMessage(content="Unknown fleet number. Ask for a valid number.", tool_call_id=runtime.tool_call_id)]})
    return Command(update={"bus": fleet_no, "current_step": "specialist",
                           "messages": [ToolMessage(content="Recorded " + fleet_no, tool_call_id=runtime.tool_call_id)]})


@wrap_model_call
def apply_step(request, handler):
    step = request.state.get("current_step", "triage")
    print("step :", step)
    if step == "triage":
        return handler(request.override(system_prompt="Collect the fleet number, then call record_bus. Do not give technical advice.", tools=[record_bus]))
    return handler(request.override(system_prompt="Answer briefly for bus " + request.state["bus"] + " using the tools.", tools=[part_stock, fault_guidance]))


from langgraph.checkpoint.memory import InMemorySaver

support_model = llm.model_copy(update={"model_kwargs": {**llm.model_kwargs, "parallel_tool_calls": False}})
support = create_agent(support_model, tools=[record_bus, part_stock, fault_guidance],
                       state_schema=SupportState, middleware=[apply_step], checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "bus-support"}, "recursion_limit": 24}
result = measured("triage", lambda: support.invoke({**ask("My bus shows F-CE-110."), "current_step": "triage", "bus": ""}, config))
print("answer :", last_text(result))
result = measured("specialist step", lambda: support.invoke(ask(QUESTION), config))
print("active :", result["current_step"], result["bus"])
print("answer :", last_text(result))
print("checks :", completeness(last_text(result)))
'''),
    md("We inspect triage failures as well. A model may mistake an error code for a fleet number ; the database check prevents that value from advancing the step. We keep current_step unchanged until a valid fleet number is recorded."),
])

demo(5, "skills", "Skills", [
    section("a · skills", "We load instructions into the current agent's history with load_skill. The tool loop is still the graph we built by hand. A skill adds context without creating another worker."),
    code(SKILLS),
    section("b · subagent-or-skill", "We inspect what remains in the skilled agent's context and compare it with an isolated worker. We choose isolation when intermediate work would clutter the caller's history."),
    code(r'''
print("skill history :", [(m.name, str(m.content)[:120]) for m in result["messages"] if isinstance(m, ToolMessage)])
worker = specialists(llm)["parts"]
isolated = measured("isolated specialist", lambda: worker.invoke(ask(STOCK_TASK), LIMIT))
print("worker input :", isolated["messages"][0].content)
print("returned :", last_text(isolated))
'''),
    md("We retain intermediate results in one conversation when we need them for follow-ups. We delegate when we want a bounded result and a separate working context. Neither choice guarantees lower cost on every task."),
])

demo(6, "workflows", "Workflows", [
    section("a · workflows", "We port the ticket pipeline as a fixed sequence. A model classifies and writes, while a lookup table sets priority. We read a made-up ticket from the bus dataset."),
    code(r'''
import csv

ticket = next(csv.DictReader(Path(data("demo-world/tickets.csv")).open(encoding="utf-8")))


class TicketState(TypedDict):
    message: str
    category: str
    priority: str
    reply: str


class Category(BaseModel):
    category: Literal["complaint", "question", "praise"]


def categorise(state):
    category = llm.with_structured_output(Category).invoke("Classify this workshop message.\n" + state["message"])
    return {"category": category.category}


def prioritise(state):
    return {"priority": {"complaint": "high", "question": "normal", "praise": "low"}[state["category"]]}


def respond(state):
    return {"reply": llm.invoke("Write a short Veenhaven Bus acknowledgement. Do not invent a repair date.\n"
                                + json.dumps(state)).content}


graph = StateGraph(TicketState)
for name, node in [("categorise", categorise), ("prioritise", prioritise), ("respond", respond)]:
    graph.add_node(name, node)
graph.add_edge(START, "categorise")
graph.add_edge("categorise", "prioritise")
graph.add_edge("prioritise", "respond")
graph.add_edge("respond", END)
result = measured("sequential ticket", lambda: graph.compile().invoke({"message": ticket["symptom"]}, LIMIT))
print("ticket :", ticket["ticket_id"])
print("category :", result["category"])
print("priority :", result["priority"])
print("reply :", result["reply"])
'''),
    section("b · workflows-parallel", "We build fixed sequential and parallel lookup workflows. The same specialist tasks feed the same compose node. A join edge waits for both independent branches."),
    code(WORKFLOW),
    code(r'''
for parallel in [False, True]:
    result = measured("parallel lookup" if parallel else "sequential lookup", lambda: workflow_graph(llm, parallel).invoke({"question": QUESTION}, LIMIT))
    print("answer :", result["answer"])
    print("checks :", completeness(result["answer"]))
'''),
    section("c · orchestration-in-code", "We remove agent loops from known lookups. Code fetches the facts and the model writes the answer. We compare the number of model calls with the worker-based workflows."),
    code(r'''
def fetch(state):
    return {"stock": part_stock.invoke({"part": "CE-CF-02"}),
            "guidance": fault_guidance.invoke({"error_code": "F-CE-110"})}


graph = StateGraph(WorkflowState)
graph.add_node("fetch", fetch)
graph.add_node("compose", lambda s: {"answer": compose(llm, s["question"], [s["stock"], s["guidance"]])})
graph.add_edge(START, "fetch")
graph.add_edge("fetch", "compose")
graph.add_edge("compose", END)
result = measured("orchestration in code", lambda: graph.compile().invoke({"question": QUESTION}, LIMIT))
print("answer :", result["answer"])
print("checks :", completeness(result["answer"]))
'''),
])

demo(7, "maker-checker", "Maker-checker", [
    section("a · maker-checker", "We give a writer and a model checker the same database evidence and an explicit rubric. We cap the repair loop and report its last verdict, including a rejection that remains at the cap."),
    code(CHECKER),
    code(r'''
result = measured("model checker", lambda: maker_checker(llm).invoke(draft_input(), LIMIT))
print("approved :", result["approved"])
print("draft :", result["draft"])
print("code findings :", check_note(result["draft"]))
'''),
    section("b · checker-in-code", "We check required part numbers, counts, locations and a zero-stock warning directly. We start with a deliberately incomplete note so the repair path remains visible. Passing establishes only these checks."),
    code(r'''
bad = "CE-CF-02 : 6 at Rietpoort\nCE-DA-03 : available at Rietpoort"
print("seeded draft :", bad)
print("findings :", check_note(bad))
initial = {**draft_input(), "draft": bad, "feedback": "\n".join(check_note(bad))}
result = measured("code checker", lambda: maker_checker(llm, code_check=True).invoke(initial, LIMIT))
print("approved :", result["approved"])
print("draft :", result["draft"])
print("findings :", check_note(result["draft"]))
'''),
    md("We do not infer safety or suitability from a stock check. A model checker can overlook a fact, while a code checker can reject a semantically correct phrase that misses its required format."),
])

demo(8, "debate-and-selection", "Debate and selection", [
    section("a · debate-and-selection", "We ask separate agents to examine inspection and replacement first, using the same evidence. A judge sees both proposals and the source. We inspect whether it retains the manual's replacement condition."),
    code(CHECKER),
    code(SELECTION),
    code(r'''
result = measured("debate with judge", lambda: debate_graph(llm).invoke({"task": QUESTION, "candidates": []}, LIMIT))
for candidate in sorted(result["candidates"], key=lambda c: c["role"]):
    print("proposal :", candidate["role"], candidate["text"])
print("judge :", result["answer"])
'''),
    section("b · generate-and-filter", "We generate alternative notes independently, reject those that fail factual checks, and choose the shortest surviving note in code. We report an empty selection when no candidate passes."),
    code(r'''
result = measured("generate and filter", lambda: generate_filter_graph(llm).invoke({"task": TASK, "candidates": []}, LIMIT))
for candidate in result["candidates"]:
    print("candidate :", candidate["role"], candidate["text"])
print("selected :", result["answer"])
'''),
    md("We can combine these shapes with a bounded tournament or a repair loop. More proposals spend more tokens, and agreement between models does not replace evidence. The examples and code are ours ; the orchestration names are discussed in the [Academy delegation material](https://github.com/langchain-ai/lca-deepagents)."),
])

demo(9, "what-each-pattern-costs", "What each pattern costs", [
    section("a · what-each-pattern-costs", "We run one question three times per pattern on the real demo records. We include one agent first, the five documented patterns, and a code-driven lookup variant. We compare component-wise medians, and inspect every answer. Seconds include the shared rate limiter at the configured COURSE_RPS."),
    code(SUBAGENTS.split('result = measured("subagents"')[0]),
    code(ROUTER.split('result = measured("router sequential"')[0]),
    code(HANDOFF.split('def seeded_failure')[0]),
    code(SKILLS.split('result = measured("skills"')[0]),
    code(WORKFLOW),
    code(r'''
single = agent_by_hand(llm, [part_stock, fault_guidance], "Answer briefly using the data tools.")
patterns = {
    "single agent": lambda: last_text(single.invoke(ask(QUESTION), LIMIT)),
    "subagents": lambda: last_text(coordinator.invoke(ask(QUESTION), LIMIT)),
    "handoffs fixed": lambda: last_text(handoff_graph(llm).invoke(ask(QUESTION), LIMIT)),
    "skills": lambda: last_text(skilled.invoke(ask(QUESTION), LIMIT)),
    "router": lambda: router_graph(llm, True).invoke({"question": QUESTION, "answers": []}, LIMIT)["final"],
    "custom workflow": lambda: workflow_graph(llm, False).invoke({"question": QUESTION}, LIMIT)["answer"],
    "code lookups": lambda: compose(llm, QUESTION, [part_stock.invoke({"part": "CE-CF-02"}), fault_guidance.invoke({"error_code": "F-CE-110"})]),
}
rows = []
for name, operation in patterns.items():
    for run in range(1, 4):
        answer = measured(name, operation)
        checks = completeness(answer)
        row = {**metrics[-1], "run": run, "model": MODEL, "rps": float(os.environ["COURSE_RPS"]),
               "checks": checks, "correct": all(checks.values()), "answer": answer}
        rows.append(row)
        print("run :", name, run, "checks :", checks)
        print("answer :", answer)

from statistics import median

print("pattern              correct  calls  input  output  seconds")
for name in patterns:
    runs = [r for r in rows if r["pattern"] == name]
    values = [median(r[key] for r in runs) for key in ["calls", "input_tokens", "output_tokens", "seconds"]]
    print(f"{name:20} {sum(r['correct'] for r in runs)}/3      {values[0]:4.0f} {values[1]:6.0f} {values[2]:6.0f} {values[3]:7.1f}")
Path("demo09-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
'''),
    md("We score count and location plus the manual's airflow condition. We also read the answers because the checks can accept a wrong sentence containing the expected words. We compare calls and tokens first ; elapsed time includes deliberate request spacing and cannot be presented as model latency."),
    md("We keep the earlier probe separate. It used a smaller in-memory stock and workshop fixture at a different rate budget. Its handoff rows include the fixed history transfer, yet one run stopped with a half answer. We do not rerun Deep Agents here ; module 08 compares the harness after the manual patterns."),
])

print("module 05 notebooks written")
