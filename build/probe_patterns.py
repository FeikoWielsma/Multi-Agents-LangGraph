"""The five multi-agent patterns and a Deep Agent, measured on one two-domain question.

    uv run python build/probe_patterns.py [model] [runs]

Each pattern answers the same question that needs a parts lookup and a workshop
lookup. Per run : model calls, input and output tokens, seconds, malformed tool
calls, and whether the answer has both facts. Results go to
build/probe-patterns-<model>.json.
"""
import json
import operator
import os
import sys
import threading
import time
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send
from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
MODEL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("COURSE_MODEL", "openai/gpt-6-luna")
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
QUESTION = ("Bus 4012 has a brake fault and is at depot Noord. Is brake pad BR-220 in stock "
            "at Noord, and when is the next free workshop slot there? Answer in two sentences.")


def answer_ok(text: str) -> bool:
    t = text.lower()
    return ("6" in t or "six" in t) and "thursday" in t


# ---- data and tools ---------------------------------------------------------
STOCK = {("BR-220", "Noord"): 6, ("BR-220", "Zuid"): 0, ("FL-110", "Noord"): 2}
SLOTS = {"Noord": "Thursday 15 October, 09:00", "Zuid": "Monday 19 October, 13:00"}


@tool
def part_stock(part: str, depot: str) -> str:
    """Units in stock for a part number at a depot."""
    return f"{STOCK.get((part.upper(), depot.title()), 0)} units of {part} at {depot}"


@tool
def next_workshop_slot(depot: str) -> str:
    """The next free workshop slot at a depot."""
    return SLOTS.get(depot.title(), "no free slot this month")


@tool
def fault_history(bus: str) -> str:
    """Past faults recorded for a bus."""
    return "Bus 4012 : brake pads replaced 2026-03-02 ; ABS warning 2026-08-19"


# ---- measuring --------------------------------------------------------------
class Counter(BaseCallbackHandler):
    def __init__(self):
        self.lock = threading.Lock()
        self.calls = self.input = self.output = self.invalid = 0

    def on_llm_end(self, response, **kwargs):
        with self.lock:
            self.calls += 1
            for gen in response.generations[0]:
                msg = getattr(gen, "message", None)
                usage = getattr(msg, "usage_metadata", None) or {}
                self.input += usage.get("input_tokens", 0)
                self.output += usage.get("output_tokens", 0)
                self.invalid += len(getattr(msg, "invalid_tool_calls", []) or [])


# New OpenRouter accounts get 20 requests a minute per model ; stay under it
LIMITER = InMemoryRateLimiter(requests_per_second=float(os.environ.get("COURSE_RPS", "0.3")),
                              check_every_n_seconds=0.1, max_bucket_size=1)


def make_llm(counter):
    return ChatOpenAI(model=MODEL, base_url=os.environ["COURSE_BASE_URL"],
                      api_key=os.environ["COURSE_API_KEY"], temperature=0, timeout=120,
                      extra_body={"reasoning": {"effort": "none"}}, callbacks=[counter], rate_limiter=LIMITER)


def last_text(messages) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content and not m.tool_calls:
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def ask(messages_text):
    return {"messages": [{"role": "user", "content": messages_text}]}


# ---- the patterns -----------------------------------------------------------
def single(llm):
    agent = create_agent(llm, tools=[part_stock, next_workshop_slot, fault_history],
                         system_prompt="You are the depot assistant. Be brief.")
    return last_text(agent.invoke(ask(QUESTION))["messages"])


def subagents(llm):
    parts = create_agent(llm, tools=[part_stock], system_prompt="You answer parts stock questions. Be brief.")
    workshop = create_agent(llm, tools=[next_workshop_slot], system_prompt="You answer workshop scheduling questions. Be brief.")

    @tool
    def ask_parts_agent(question: str) -> str:
        """Ask the parts agent a question about stock."""
        return last_text(parts.invoke(ask(question))["messages"])

    @tool
    def ask_workshop_agent(question: str) -> str:
        """Ask the workshop agent a question about workshop slots."""
        return last_text(workshop.invoke(ask(question))["messages"])

    main = create_agent(llm, tools=[ask_parts_agent, ask_workshop_agent],
                        system_prompt="You coordinate specialist agents. Delegate, then answer briefly.")
    return last_text(main.invoke(ask(QUESTION))["messages"])


def handoffs(llm, trace=False):
    # A handoff Command jumps away and drops the results of any sibling tool calls,
    # which the provider then rejects : one tool call per turn for handoff agents
    llm = llm.model_copy(update={"model_kwargs": {"parallel_tool_calls": False}})
    class S(AgentState):
        active_agent: NotRequired[str]

    def transfer(target):
        @tool(f"transfer_to_{target}")
        def _transfer(runtime: ToolRuntime) -> Command:
            """Transfer the conversation to the other agent."""
            # Forward the agent's whole history, not only its last message as the docs'
            # example does : otherwise the lookups it made before the handoff are lost
            note = ToolMessage(content=f"Transferred to {target}", tool_call_id=runtime.tool_call_id)
            return Command(goto=target, update={"active_agent": target,
                                                "messages": [*runtime.state["messages"], note]},
                           graph=Command.PARENT)
        _transfer.description = f"Transfer to the {target}."
        return _transfer

    parts = create_agent(llm, tools=[part_stock, transfer("workshop_agent")],
                         system_prompt="You are the parts agent. First answer the stock part of the request "
                                       "with your tool. If a workshop question remains unanswered, then "
                                       "transfer to the workshop agent. Be brief.")
    workshop = create_agent(llm, tools=[next_workshop_slot, transfer("parts_agent")],
                            system_prompt="You are the workshop agent. First answer the workshop part of the "
                                          "request with your tool. If a stock question remains unanswered, then "
                                          "transfer to the parts agent. When every part is answered, give the "
                                          "user one complete answer. Be brief.")

    def route(state) -> Literal["parts_agent", "workshop_agent", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and not last.tool_calls:
            return END
        return state.get("active_agent", "parts_agent")

    g = StateGraph(S)
    g.add_node("parts_agent", lambda s: parts.invoke(s))
    g.add_node("workshop_agent", lambda s: workshop.invoke(s))
    g.add_edge(START, "parts_agent")
    g.add_conditional_edges("parts_agent", route, ["parts_agent", "workshop_agent", END])
    g.add_conditional_edges("workshop_agent", route, ["parts_agent", "workshop_agent", END])
    out = g.compile().invoke(ask(QUESTION), {"recursion_limit": 25})
    if trace:
        for m in out["messages"]:
            print(f"  {m.type:<6} {[c['name'] for c in getattr(m, 'tool_calls', [])]} {str(m.content)[:90]!r}")
    return last_text(out["messages"])


SKILLS = {
    "parts": "Parts skill : look up stock with part_stock for the part and depot named. "
             "Report the number of units.",
    "workshop": "Workshop skill : look up the next slot with next_workshop_slot for the depot. "
                "Report day, date and time.",
}


def skills(llm):
    @tool
    def load_skill(name: str) -> str:
        """Load the instructions for a skill : parts or workshop."""
        return SKILLS.get(name, "unknown skill")

    agent = create_agent(llm, tools=[load_skill, part_stock, next_workshop_slot],
                         system_prompt="You are the depot assistant. Skills available : parts, workshop. "
                                       "Load a skill before using its tools. Be brief.")
    return last_text(agent.invoke(ask(QUESTION))["messages"])


def router(llm):
    parts = create_agent(llm, tools=[part_stock], system_prompt="You answer parts stock questions. Be brief.")
    workshop = create_agent(llm, tools=[next_workshop_slot], system_prompt="You answer workshop scheduling questions. Be brief.")

    class Route(BaseModel):
        parts_question: str | None
        workshop_question: str | None

    class S(TypedDict):
        question: str
        results: Annotated[list[str], operator.add]
        answer: str

    def classify(state):
        r = llm.with_structured_output(Route).invoke(
            "Split this request into a question for the parts agent and one for the workshop "
            f"agent ; null where not needed.\n\n{state['question']}")
        sends = []
        if r.parts_question:
            sends.append(Send("parts", {"question": r.parts_question}))
        if r.workshop_question:
            sends.append(Send("workshop", {"question": r.workshop_question}))
        return Command(goto=sends)

    g = StateGraph(S)
    g.add_node("classify", classify, destinations=("parts", "workshop"))
    g.add_node("parts", lambda s: {"results": [last_text(parts.invoke(ask(s["question"]))["messages"])]})
    g.add_node("workshop", lambda s: {"results": [last_text(workshop.invoke(ask(s["question"]))["messages"])]})
    g.add_node("synthesise", lambda s: {"answer": llm.invoke(
        f"Answer in two sentences : {s['question']}\n\nFindings :\n" + "\n".join(s["results"])).content})
    g.add_edge(START, "classify")
    g.add_edge("parts", "synthesise")
    g.add_edge("workshop", "synthesise")
    g.add_edge("synthesise", END)
    return g.compile().invoke({"question": QUESTION, "results": []})["answer"]


def workflow(llm):
    parts = create_agent(llm, tools=[part_stock], system_prompt="You answer parts stock questions. Be brief.")
    workshop = create_agent(llm, tools=[next_workshop_slot], system_prompt="You answer workshop scheduling questions. Be brief.")

    class S(TypedDict):
        question: str
        stock: str
        slot: str
        answer: str

    g = StateGraph(S)
    g.add_node("parts", lambda s: {"stock": last_text(parts.invoke(ask(
        "Is brake pad BR-220 in stock at depot Noord?"))["messages"])})
    g.add_node("workshop", lambda s: {"slot": last_text(workshop.invoke(ask(
        "When is the next free workshop slot at depot Noord?"))["messages"])})
    g.add_node("compose", lambda s: {"answer": llm.invoke(
        f"Answer in two sentences : {s['question']}\n\nStock : {s['stock']}\nSlot : {s['slot']}").content})
    g.add_edge(START, "parts")
    g.add_edge("parts", "workshop")
    g.add_edge("workshop", "compose")
    g.add_edge("compose", END)
    return g.compile().invoke({"question": QUESTION})["answer"]


def deep_agent(llm):
    from deepagents import create_deep_agent
    agent = create_deep_agent(
        model=llm, tools=[],
        system_prompt="You coordinate the depot. Delegate lookups to your subagents, then answer briefly.",
        subagents=[
            {"name": "parts-agent", "description": "Looks up parts stock at a depot.",
             "system_prompt": "You answer parts stock questions. Be brief.", "tools": [part_stock]},
            {"name": "workshop-agent", "description": "Looks up the next free workshop slot at a depot.",
             "system_prompt": "You answer workshop scheduling questions. Be brief.", "tools": [next_workshop_slot]},
        ])
    return last_text(agent.invoke(ask(QUESTION))["messages"])


PATTERNS = {"single agent": single, "subagents": subagents, "handoffs": handoffs,
            "skills": skills, "router": router, "custom workflow": workflow, "deep agent": deep_agent}

if __name__ == "__main__":
    rows = []
    for name, fn in PATTERNS.items():
        for run in range(RUNS):
            counter = Counter()
            start = time.time()
            try:
                text = fn(make_llm(counter))
                error = None
            except Exception as exc:
                text, error = "", f"{type(exc).__name__}: {str(exc)[:600]}"
            row = dict(model=MODEL, pattern=name, run=run + 1, seconds=round(time.time() - start, 1),
                       calls=counter.calls, input_tokens=counter.input, output_tokens=counter.output,
                       malformed=counter.invalid, correct=answer_ok(text), error=error, answer=text[:300])
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("pattern", "run", "seconds", "calls", "input_tokens",
                                                    "output_tokens", "malformed", "correct", "error")}))

    out = Path(__file__).with_name(f"probe-patterns-{MODEL.split('/')[-1]}.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {out.name}")
