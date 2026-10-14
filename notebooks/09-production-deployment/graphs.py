
"""Original Veenhaven Bus graph exports for module 09."""
import asyncio
from typing_extensions import NotRequired

from course_runtime import data, data_folder, llm

import json
import re
import sqlite3
from pathlib import Path

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import tool

DB = Path(data("demo-world/service.db")).resolve()
MANUALS = Path(data_folder("demo-world/manuals"))


@tool
def part_stock(part_no: str) -> str:
    """Look up a Veenhaven Bus part's stock and depot by its part number."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no = ?",
                          (part_no.upper(),)).fetchall()
    return json.dumps(rows)


@tool
def fault_guidance(error_code: str) -> str:
    """Read the meaning, first action and replacement condition for a bus error code."""
    return "\n".join(f"[{p.name}] {line}" for p in sorted(MANUALS.glob("*.md"))
                     for line in p.read_text(encoding="utf-8").splitlines()
                     if line.startswith("| " + error_code.upper() + " |")) or "No matching code."


QUESTION = "How many CE-CF-02 cooling fans are in stock and at which depot?"
SYSTEM = "Support Veenhaven Bus mechanics. Use the tools for facts. Preserve stock and depot names. Be brief."
LIMIT = {"recursion_limit": 20}


def ask(text):
    return {"messages": [{"role": "user", "content": text}]}


def show(result):
    for message in result["messages"]:
        if isinstance(message, dict):
            kind, content = message["type"], message.get("content", "")
            calls = message.get("tool_calls", [])
        else:
            kind, content, calls = message.type, message.content, getattr(message, "tool_calls", [])
        if kind in ("ai", "tool"):
            print(kind, ":", str(content)[:700], calls or "")

from deepagents import AsyncSubAgent, create_deep_agent
from langgraph.graph import END, START, MessagesState, StateGraph

parts = create_agent(llm, tools=[part_stock], system_prompt=SYSTEM, name="parts")


class WorkState(MessagesState):
    delay_seconds: NotRequired[float]


async def answer(state):
    await asyncio.sleep(state.get("delay_seconds", 0))
    result = await parts.ainvoke({"messages": state["messages"]})
    return {"messages": result["messages"]}


builder = StateGraph(WorkState)
builder.add_node("answer", answer)
builder.add_edge(START, "answer")
builder.add_edge("answer", END)
service = builder.compile()


async def research(state):
    text = str(state["messages"][-1].content)
    if "DELAY" in text and "NO DELAY" not in text:
        await asyncio.sleep(120)
    result = await parts.ainvoke({"messages": state["messages"]})
    return {"messages": result["messages"]}


worker_builder = StateGraph(MessagesState)
worker_builder.add_node("research", research)
worker_builder.add_edge(START, "research")
worker_builder.add_edge("research", END)
researcher = worker_builder.compile()

supervisor = create_deep_agent(
    model=llm,
    subagents=[AsyncSubAgent(name="parts-researcher", graph_id="researcher",
                           description="Research Veenhaven Bus parts stock in the background.")],
    system_prompt="Coordinate Veenhaven Bus research. Use only the requested async task tool, "
                  "then respond briefly. After launch return to the user without checking. "
                  "Copy full task IDs from async_tasks. Always fetch status before reporting it.",
    name="supervisor")
