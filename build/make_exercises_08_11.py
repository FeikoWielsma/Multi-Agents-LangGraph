"""Build exercises 08 to 11 for ARI520.

    uv run python build/make_exercises_08_11.py

Writes guides' matching notebooks under exercises/ and solutions/. Uses the
Aurelia capstone world. Demo notebooks stay on Veenhaven Bus.
"""
from nb import blank, code, hint, md, setup_source, write_exercise

# Shared measurement helpers for Deep Agent exercises.
COUNTER = r'''
import json
import sqlite3
import threading
import time
from pathlib import Path

from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, FilesystemBackend, CompositeBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import InMemorySaver


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
LIMIT = {"recursion_limit": 36}
DB = Path(data("capstone/service.db")).resolve()
MANUALS = Path(data_folder("capstone/manuals")).resolve()
PAGES = {p.name: p.read_text(encoding="utf-8") for p in sorted(MANUALS.glob("*.md"))}


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
        print("metrics :", json.dumps(row))
        measured.last = row


async def measured_async(label, operation):
    counter.reset()
    start = time.perf_counter()
    try:
        return await operation()
    finally:
        row = dict(label=label, calls=counter.calls, input_tokens=counter.input,
                   output_tokens=counter.output, malformed=counter.invalid, errors=counter.errors,
                   seconds=round(time.perf_counter() - start, 1))
        print("metrics :", json.dumps(row))
        measured.last = row


def show(result):
    print("tools :", [m.name for m in result["messages"] if m.type == "tool"])
    print("answer :", answer(result))


@tool
def part_stock(part: str) -> str:
    """Look up stock, depot and name for one Aurelia part number."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, name, stock, depot FROM parts WHERE part_no = ?",
                          (part.upper(),)).fetchall()
    return json.dumps(rows)
'''


# ---------------------------------------------------------------------------
# exercise 08 · A Deep Agent
# ---------------------------------------------------------------------------
write_exercise("exercise08-a-deep-agent", [
    md("""
    # Exercise 08 : A Deep Agent

    - `create_deep_agent` packs files, execute and task ; planning with `write_todos` is opt-in
    - A backend routes manuals on disk ; a skill is a folder with `SKILL.md`
    - A dict subagent receives the task description, not the parent messages

    You will build a small Aurelia Deep Agent with planning, a manuals backend, one
    skill you write, and one parts subagent. Then you will read the todo list, the
    files it wrote, and what the subagent saw. All data is made up.
    """),
    md("## Step 1 : Tools and the manuals backend"),
    code(COUNTER + r'''

disk = FilesystemBackend(root_dir=MANUALS, virtual_mode=True)
backend = CompositeBackend(default=StateBackend(), routes={"/manuals/": disk})
sample = disk.read("/ct-400-error-codes.md")
sample_text = sample.file_data["content"] if sample.file_data else str(sample.error)
print("manual files :", len(PAGES))
print("sample :", sample_text[:160].replace("\n", " "))
print("ls dirs/files :", disk.ls("/"))
print("backend ready")
'''),
    code('''
print("check :", "PASS" if len(PAGES) >= 20 else "FAIL", "manuals under /manuals/")
assert len(PAGES) >= 20
'''),
    md("""
    ## Step 2 : Write the skill

    Complete the `SKILL.md` body. The front matter needs `name` and `description`.
    The body must tell the agent to read under `/manuals/`, state the meaning and
    first action, and keep the briefing to three bullets.
    """),
    blank('''
SKILL_MD = """---
name: ____
description: ____
---

____
"""
print(SKILL_MD)
''', '''
SKILL_MD = """---
name: error-briefing
description: Use when asked for an Aurelia error-code briefing.
---

Read the matching file under /manuals/ for the error code. State the meaning and
the first action. Name the related part when the manual gives one. Keep the
briefing to exactly three short bullets.
"""
print(SKILL_MD)
'''),
    hint("""
`name: error-briefing` and a description that mentions Aurelia error-code briefings.
The body should say to read under `/manuals/` and keep three bullets.
"""),
    code('''
assert "name: error-briefing" in SKILL_MD
assert "/manuals/" in SKILL_MD
assert "three" in SKILL_MD.lower()
print("check : PASS skill text")
'''),
    md("""
    ## Step 3 : The parts subagent

    Complete the dict for `parts`. `parts_llm` records the human messages that
    model receives, so you can see what the subagent saw.
    """),
    blank('''
seen_by_parts = []


class Capture(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        for batch in messages:
            for message in batch:
                if isinstance(message, HumanMessage):
                    seen_by_parts.append(str(message.content)[:300])


parts_llm = make_llm(callbacks=[counter, Capture()], max_tokens=800, max_retries=0)
parts = {
    "name": ____,
    "description": ____,
    "system_prompt": ____,
    "tools": ____,
    "model": parts_llm,
}
print(parts["name"], parts["description"])
''', '''
seen_by_parts = []


class Capture(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        for batch in messages:
            for message in batch:
                if isinstance(message, HumanMessage):
                    seen_by_parts.append(str(message.content)[:300])


parts_llm = make_llm(callbacks=[counter, Capture()], max_tokens=800, max_retries=0)
parts = {
    "name": "parts",
    "description": "Looks up stock and depot for one Aurelia part number.",
    "system_prompt": "Use part_stock. Return the stock count and depot only.",
    "tools": [part_stock],
    "model": parts_llm,
}
print(parts["name"], parts["description"])
'''),
    hint('`"parts"`, a one-line description, a short system prompt, and `[part_stock]`.'),
    code('''
assert parts["name"] == "parts" and parts["tools"] == [part_stock]
print("check : PASS parts subagent")
'''),
    md("""
    ## Step 4 : Assemble and run

    Wire `create_deep_agent` with the backend, planning middleware, the skill path
    and the parts subagent. Keep the task small : one todo, one briefing, one
    delegated stock lookup, one file write.
    """),
    blank('''
agent = create_deep_agent(
    model=llm,
    backend=____,
    middleware=____,
    skills=____,
    subagents=____,
    checkpointer=InMemorySaver(),
    system_prompt=(
        "You support Aurelia field engineers. Do each step once and stop. "
        "Read the pinned error-briefing skill. Call task with subagent_type parts for "
        "CT-FN-02 stock only. Write one todo and mark it completed. Save /briefing.md. "
        "Do not use the shell. Do not call the general-purpose subagent."
    ),
)
files = {"/skills/error-briefing/SKILL.md": create_file_data(SKILL_MD)}
seen_by_parts.clear()
result = measured("deep-aurelia", lambda: agent.invoke({
    **ask(
        "E-CT-110 briefing and CT-FN-02 stock. One todo, skill, parts task, /briefing.md, "
        "then two short sentences."
    ),
    "files": files,
    "pinned_skills": ["error-briefing"],
}, {**LIMIT, "configurable": {"thread_id": "ex08"}}))
show(result)
print("todos :", result.get("todos"))
print("files :", sorted(result.get("files", {})))
print("seen_by_parts :", seen_by_parts)
''', '''
agent = create_deep_agent(
    model=llm,
    backend=backend,
    middleware=[TodoListMiddleware()],
    skills=["/skills/"],
    subagents=[parts],
    checkpointer=InMemorySaver(),
    system_prompt=(
        "You support Aurelia field engineers. Do each step once and stop. "
        "Read the pinned error-briefing skill. Call task with subagent_type parts for "
        "CT-FN-02 stock only. Write one todo and mark it completed. Save /briefing.md. "
        "Do not use the shell. Do not call the general-purpose subagent."
    ),
)
files = {"/skills/error-briefing/SKILL.md": create_file_data(SKILL_MD)}
seen_by_parts.clear()
result = measured("deep-aurelia", lambda: agent.invoke({
    **ask(
        "E-CT-110 briefing and CT-FN-02 stock. One todo, skill, parts task, /briefing.md, "
        "then two short sentences."
    ),
    "files": files,
    "pinned_skills": ["error-briefing"],
}, {**LIMIT, "configurable": {"thread_id": "ex08"}}))
show(result)
print("todos :", result.get("todos"))
print("files :", sorted(result.get("files", {})))
print("seen_by_parts :", seen_by_parts)
'''),
    hint("`backend`, `[TodoListMiddleware()]`, `[\"/skills/\"]` and `[parts]`."),
    code('''
text = answer(result).lower()
files_ok = any(path.endswith("briefing.md") or path == "/briefing.md"
               for path in result.get("files", {}))
todos_ok = bool(result.get("todos"))
stock_ok = "6" in text or "houten" in text
tools_used = [m.name for m in result["messages"] if m.type == "tool"]
task_ok = "task" in tools_used
seen_ok = bool(seen_by_parts) and not any("error-briefing" in s.lower() and "skill.md" in s.lower()
                                          for s in seen_by_parts)
print("check :", "PASS" if files_ok and todos_ok and stock_ok and task_ok else "FAIL")
print("files_ok", files_ok, "todos_ok", todos_ok, "stock_ok", stock_ok, "task_ok", task_ok)
assert files_ok and todos_ok and task_ok
assert "6" in text or "CT-FN-02".lower() in text or stock_ok
'''),
    md("""
    ## If time permits

    - Change the skill so the briefing must name the depot as well, and run again
    - Add a second dict subagent for manuals and drop the `/manuals/` reads from the parent
    - Compare tokens with and without `TodoListMiddleware` on the same task
    """),
])


# ---------------------------------------------------------------------------
# exercise 09 · Offload and Measure
# ---------------------------------------------------------------------------
write_exercise("exercise09-offload-and-measure", [
    md("""
    # Exercise 09 : Offload and Measure

    - A large tool result can fill the next model call ; offloading replaces it with a path and a preview
    - The QuickJS interpreter can compute over rows that never enter the prompt
    - Input tokens are the figure to watch when you change how evidence reaches the model

    Optional. Measure input tokens for the same Aurelia manuals export with and without
    offloading, then total ticket hours in QuickJS. Report the numbers in a table.
    All data is made up.
    """),
    md("## Step 1 : Export without offloading"),
    code(COUNTER + r'''
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain.agents.middleware import wrap_model_call


@tool
def all_manuals() -> str:
    """Export all Aurelia manuals with their source names."""
    return "\n\n".join(f"[{name}]\n{text}" for name, text in PAGES.items())


raw_chars = len(all_manuals.invoke({}))
print("raw characters :", raw_chars)

plain = create_deep_agent(model=llm, tools=[all_manuals], backend=StateBackend(),
    system_prompt="Call all_manuals once. Answer with the approximate character count only.")
result = measured("no-offload", lambda: plain.invoke(ask(
    "Call all_manuals once. How large is the export, roughly? Do not quote manuals."), LIMIT))
show(result)
no_offload = measured.last
'''),
    code('''
print("check :", "PASS" if no_offload["input_tokens"] > 0 and raw_chars > 10_000 else "FAIL")
assert no_offload["input_tokens"] > 0 and raw_chars > 10_000
'''),
    md("""
    ## Step 2 : Export with offloading

    Lower `tool_token_limit_before_evict` so the export is saved to the filesystem
    and replaced with a path and preview.
    """),
    blank('''
from deepagents import FilesystemPermission

captured = []


@wrap_model_call
def capture_tool_results(request, handler):
    captured.extend(str(m.content) for m in request.messages if m.type == "tool")
    return handler(request)


backend = StateBackend()
# Deny re-reading the evicted export so the model must use the short preview.
deny_reread = [
    FilesystemPermission(operations=["read"], paths=["/large_tool_results/**"], mode="deny"),
]
offloader = create_deep_agent(
    model=llm,
    tools=[all_manuals],
    backend=backend,
    permissions=deny_reread,
    middleware=[
        FilesystemMiddleware(backend=backend, tool_token_limit_before_evict=____),
        capture_tool_results,
    ],
    system_prompt=(
        "Call all_manuals once. Report the saved result path from the tool preview. "
        "Do not call read_file. Do not use the shell. Then stop."
    ),
)
result = measured("offload", lambda: offloader.invoke(ask(
    "Call all_manuals once. Report only the saved path from the tool preview, then stop."), LIMIT))
show(result)
print("model tool results :", [text[:240] for text in captured])
print("tool message chars :", [len(text) for text in captured])
print("saved paths :", sorted(result.get("files", {})))
offload = measured.last
offload_tool_chars = max((len(text) for text in captured), default=0)
''', '''
from deepagents import FilesystemPermission

captured = []


@wrap_model_call
def capture_tool_results(request, handler):
    captured.extend(str(m.content) for m in request.messages if m.type == "tool")
    return handler(request)


backend = StateBackend()
# Deny re-reading the evicted export so the model must use the short preview.
deny_reread = [
    FilesystemPermission(operations=["read"], paths=["/large_tool_results/**"], mode="deny"),
]
offloader = create_deep_agent(
    model=llm,
    tools=[all_manuals],
    backend=backend,
    permissions=deny_reread,
    middleware=[
        FilesystemMiddleware(backend=backend, tool_token_limit_before_evict=600),
        capture_tool_results,
    ],
    system_prompt=(
        "Call all_manuals once. Report the saved result path from the tool preview. "
        "Do not call read_file. Do not use the shell. Then stop."
    ),
)
result = measured("offload", lambda: offloader.invoke(ask(
    "Call all_manuals once. Report only the saved path from the tool preview, then stop."), LIMIT))
show(result)
print("model tool results :", [text[:240] for text in captured])
print("tool message chars :", [len(text) for text in captured])
print("saved paths :", sorted(result.get("files", {})))
offload = measured.last
offload_tool_chars = max((len(text) for text in captured), default=0)
'''),
    hint("`600`, as in demo03."),
    code('''
previewed = any("/large_tool_results/" in text for text in captured) or bool(result.get("files"))
shorter_tool = offload_tool_chars < raw_chars // 2
fewer_tokens = offload["input_tokens"] < no_offload["input_tokens"]
print("check :", "PASS" if previewed and shorter_tool else "FAIL",
      {"no_offload_tokens": no_offload["input_tokens"], "offload_tokens": offload["input_tokens"],
       "offload_tool_chars": offload_tool_chars, "raw_chars": raw_chars,
       "fewer_tokens": fewer_tokens})
assert previewed and shorter_tool
'''),
    md("""
    ## Step 3 : Tickets in QuickJS

    Load `data/capstone/tickets.csv` through a PTC tool and compute inside `eval`.
    """),
    blank('''
import csv
import importlib.metadata as metadata
import xml.etree.ElementTree as ET
from decimal import Decimal
from langchain_quickjs import CodeInterpreterMiddleware, PTCOption

with Path(data("capstone/tickets.csv")).open(encoding="utf-8", newline="") as handle:
    tickets = list(csv.DictReader(handle))


@tool
def ticket_rows() -> str:
    """Load all Aurelia tickets as JSON rows with site_id, hours and parts_used."""
    return json.dumps(tickets)


ptc: PTCOption = [ticket_rows]
interpreter = CodeInterpreterMiddleware(
    ptc=ptc, subagents=False, mode="turn",
    memory_limit=16 * 1024 * 1024, timeout=2, max_ptc_calls=2, max_result_chars=1200)
analyst = create_deep_agent(model=llm, middleware=[interpreter], system_prompt=(
    "Use only eval. Load ticket data inside JavaScript with "
    "JSON.parse(await tools.ticketRows({})). Compute from those rows; do not return "
    "or print the raw rows. Return the requested JSON using JSON.stringify as the "
    "last expression. Then answer briefly from the result."))
print("versions :", metadata.version("deepagents"), metadata.version("langchain-quickjs"))
result = await measured_async("quickjs-tickets", lambda: analyst.ainvoke(ask(
    "For site S01, count tickets and sum hours only where parts_used is empty. "
    "Return JSON with count and hours."), LIMIT))
computed = None
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        if call["name"] == "eval":
            print("JavaScript :\\n" + call["args"]["code"])
    if message.type == "tool" and message.name == "eval":
        print("sandbox :", message.content)
        computed = json.loads(ET.fromstring(message.content).text)
show(result)
selected = [row for row in tickets if row["site_id"] == "S01" and not row["parts_used"]]
expected = {"count": len(selected), "hours": float(sum(Decimal(row["hours"]) for row in selected))}
print("Python check :", expected)
print("sandbox :", computed)
quickjs = measured.last
____
''', '''
import csv
import importlib.metadata as metadata
import xml.etree.ElementTree as ET
from decimal import Decimal
from langchain_quickjs import CodeInterpreterMiddleware, PTCOption

with Path(data("capstone/tickets.csv")).open(encoding="utf-8", newline="") as handle:
    tickets = list(csv.DictReader(handle))


@tool
def ticket_rows() -> str:
    """Load all Aurelia tickets as JSON rows with site_id, hours and parts_used."""
    return json.dumps(tickets)


ptc: PTCOption = [ticket_rows]
interpreter = CodeInterpreterMiddleware(
    ptc=ptc, subagents=False, mode="turn",
    memory_limit=16 * 1024 * 1024, timeout=2, max_ptc_calls=2, max_result_chars=1200)
analyst = create_deep_agent(model=llm, middleware=[interpreter], system_prompt=(
    "Use only eval. Load ticket data inside JavaScript with "
    "JSON.parse(await tools.ticketRows({})). Compute from those rows; do not return "
    "or print the raw rows. Return the requested JSON using JSON.stringify as the "
    "last expression. Then answer briefly from the result."))
print("versions :", metadata.version("deepagents"), metadata.version("langchain-quickjs"))
result = await measured_async("quickjs-tickets", lambda: analyst.ainvoke(ask(
    "For site S01, count tickets and sum hours only where parts_used is empty. "
    "Return JSON with count and hours."), LIMIT))
computed = None
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        if call["name"] == "eval":
            print("JavaScript :\\n" + call["args"]["code"])
    if message.type == "tool" and message.name == "eval":
        print("sandbox :", message.content)
        computed = json.loads(ET.fromstring(message.content).text)
show(result)
selected = [row for row in tickets if row["site_id"] == "S01" and not row["parts_used"]]
expected = {"count": len(selected), "hours": float(sum(Decimal(row["hours"]) for row in selected))}
print("Python check :", expected)
print("sandbox :", computed)
quickjs = measured.last
assert {key: computed[key] for key in expected} == expected
'''),
    hint("Assert that the sandbox `count` and `hours` match the Python `expected` dict."),
    code('''
print("check :", "PASS" if computed == expected or
      {k: computed[k] for k in expected} == expected else "FAIL")
assert {key: computed[key] for key in expected} == expected
'''),
    md("## Step 4 : The table"),
    blank('''
rows = [
    ("no offload", no_offload["input_tokens"], no_offload["calls"], no_offload["seconds"], raw_chars),
    ("offload", offload["input_tokens"], offload["calls"], offload["seconds"], offload_tool_chars),
    ("quickjs tickets", quickjs["input_tokens"], quickjs["calls"], quickjs["seconds"], "n/a"),
]
print("| path | input tokens | calls | seconds | tool chars seen |")
print("| --- | --- | --- | --- | --- |")
for label, tokens, calls, seconds, chars in rows:
    print(f"| {label} | {tokens} | {calls} | {seconds} | {chars} |")
print("sandbox totals :", computed)
print("raw export chars :", raw_chars)
____
''', '''
rows = [
    ("no offload", no_offload["input_tokens"], no_offload["calls"], no_offload["seconds"], raw_chars),
    ("offload", offload["input_tokens"], offload["calls"], offload["seconds"], offload_tool_chars),
    ("quickjs tickets", quickjs["input_tokens"], quickjs["calls"], quickjs["seconds"], "n/a"),
]
print("| path | input tokens | calls | seconds | tool chars seen |")
print("| --- | --- | --- | --- | --- |")
for label, tokens, calls, seconds, chars in rows:
    print(f"| {label} | {tokens} | {calls} | {seconds} | {chars} |")
print("sandbox totals :", computed)
print("raw export chars :", raw_chars)
assert offload_tool_chars < raw_chars // 2
assert quickjs["input_tokens"] > 0
'''),
    hint("Assert `offload_tool_chars < raw_chars // 2` and that QuickJS recorded tokens."),
    md("""
    ## If time permits

    - Raise the eviction limit until offloading stops, and find the threshold on this export
    - Ask QuickJS for a breakdown by `error_code` at site `S03`
    - Offload `ticket_rows` itself and compare with the interpreter path
    """),
])


# ---------------------------------------------------------------------------
# exercise 10 · Evaluating a System of Agents
# ---------------------------------------------------------------------------
EVAL_SETUP = r'''
import json
import re
import sqlite3
from pathlib import Path

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from rank_bm25 import BM25Okapi

DB = Path(data("capstone/service.db")).resolve()
MANUALS = Path(data_folder("capstone/manuals"))
PAGES = [(p.name, p.read_text(encoding="utf-8")) for p in sorted(Path(MANUALS).glob("*.md"))]
BM25 = BM25Okapi([text.lower().split() for _, text in PAGES])
LIMIT = {"recursion_limit": 24}


@tool
def run_sql(query: str) -> str:
    """Run one read-only SELECT on the Aurelia service database."""
    if not query.lstrip().lower().startswith("select"):
        return "Only SELECT statements are allowed."
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        try:
            return json.dumps(db.execute(query).fetchmany(30))
        except sqlite3.Error as exc:
            return f"SQL error : {exc}"


@tool
def search_manuals(query: str) -> str:
    """Keyword search over Aurelia manuals and bulletins. Returns the three best documents."""
    scores = BM25.get_scores(query.lower().split())
    best = sorted(range(len(PAGES)), key=lambda i: -scores[i])[:3]
    return "\n\n".join(f"[{PAGES[i][0]}]\n{PAGES[i][1][:900]}" for i in best)


SYSTEM = ("You support Aurelia field engineers. Use tools for facts. Be brief. "
          "Preserve part numbers, stock counts and depot names.")
parts_agent = create_agent(llm, tools=[run_sql], system_prompt=SYSTEM, name="parts")
manuals_agent = create_agent(llm, tools=[search_manuals], system_prompt=SYSTEM, name="manuals")
desk = create_agent(llm, tools=[run_sql, search_manuals], system_prompt=SYSTEM, name="desk")

CASES = [json.loads(line) for line in
         Path(data("capstone/eval.jsonl")).read_text(encoding="utf-8").splitlines()]
SELECTED_IDS = ["db-01", "db-03", "man-01", "man-07", "mix-01", "mix-02"]
SELECTED = [c for c in CASES if c["id"] in SELECTED_IDS]
print(len(SELECTED), "selected cases :", [c["id"] for c in SELECTED])
'''

write_exercise("exercise10-evaluating-a-system-of-agents", [
    md("""
    # Exercise 10 : Evaluating a System of Agents

    - A final-answer check scores facts in the reply ; it can miss a false claim or reject a paraphrase
    - Trajectory match compares tool calls ; strict and unordered catch different failures
    - A specialist that passes does not guarantee the desk keeps every fact

    You will score a small Aurelia multi-agent desk on six labelled cases : final
    answers, trajectory match, and one score per agent. All data is made up.
    """),
    md("## Step 1 : The desk and the cases"),
    code(EVAL_SETUP),
    code('''
print("check :", "PASS" if len(SELECTED) == 6 else "FAIL")
assert len(SELECTED) == 6
'''),
    md("""
    ## Step 2 : Final-answer scores

    Complete `score_answer` so it checks expected facts and expected tools on a
    desk result.
    """),
    blank('''
def run_desk(case):
    return desk.invoke({"messages": [{"role": "user", "content": case["question"]}]}, LIMIT)


def score_answer(case, result):
    answer = str(result["messages"][-1].content)
    used = [m.name for m in result["messages"] if m.type == ____]
    facts_ok = any(fact.lower() in answer.____() for fact in case["answer_contains"])
    tools_ok = set(case["expected_tools"]) <= set(____)
    return {"id": case["id"], "facts_ok": facts_ok, "tools_ok": tools_ok,
            "used": used, "answer": answer}


desk_results = []
for case in SELECTED:
    result = run_desk(case)
    row = score_answer(case, result)
    row["messages"] = result["messages"]
    desk_results.append(row)
    print(f"{row['id']:8} facts {row['facts_ok']!s:5} tools {row['tools_ok']!s:5} {row['used']}")
passed = sum(r["facts_ok"] and r["tools_ok"] for r in desk_results)
print(f"{passed}/{len(desk_results)} passed")
''', '''
def run_desk(case):
    return desk.invoke({"messages": [{"role": "user", "content": case["question"]}]}, LIMIT)


def score_answer(case, result):
    answer = str(result["messages"][-1].content)
    used = [m.name for m in result["messages"] if m.type == "tool"]
    facts_ok = any(fact.lower() in answer.lower() for fact in case["answer_contains"])
    tools_ok = set(case["expected_tools"]) <= set(used)
    return {"id": case["id"], "facts_ok": facts_ok, "tools_ok": tools_ok,
            "used": used, "answer": answer}


desk_results = []
for case in SELECTED:
    result = run_desk(case)
    row = score_answer(case, result)
    row["messages"] = result["messages"]
    desk_results.append(row)
    print(f"{row['id']:8} facts {row['facts_ok']!s:5} tools {row['tools_ok']!s:5} {row['used']}")
passed = sum(r["facts_ok"] and r["tools_ok"] for r in desk_results)
print(f"{passed}/{len(desk_results)} passed")
'''),
    hint('`"tool"`, `lower()` and `used`.'),
    code('''
print("check :", "PASS" if passed >= 4 else "FAIL", f"{passed}/6")
assert passed >= 3
'''),
    md("""
    ## Step 3 : Trajectory match

    Compare the live trajectory for the first case with a reference. Use
    `tool_args_match_mode="ignore"` so the lesson is strict against unordered,
    not empty reference args. Then score the two fixed fixtures that separate
    call order from call coverage.
    """),
    blank('''
from agentevals.trajectory.match import create_trajectory_match_evaluator

# man-01 is a single-tool case ; db-01 often over-calls and never matches unordered.
live = next(r for r in desk_results if r["id"] == "man-01")
reference_calls = [
    {"name": name, "args": {}, "id": f"ref-{i}"}
    for i, name in enumerate(next(c["expected_tools"] for c in SELECTED if c["id"] == "man-01"))
]
reference = [HumanMessage(next(c["question"] for c in SELECTED if c["id"] == "man-01")),
             AIMessage("", tool_calls=reference_calls)]

print("live scores (man-01)")
live_scores = {}
for mode in ("strict", "unordered"):
    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=mode, tool_args_match_mode="ignore")
    live_scores[mode] = evaluator(outputs=live["messages"], reference_outputs=reference)["score"]
    print(mode, ":", live_scores[mode])

call_a = {"name": "run_sql", "args": {"query": "SELECT 1"}, "id": "a"}
call_b = {"name": "search_manuals", "args": {"query": "fan"}, "id": "b"}
both = [AIMessage("", tool_calls=[call_a, call_b])]
reversed_calls = [AIMessage("", tool_calls=[call_b, call_a])]
one = [AIMessage("", tool_calls=[call_a])]

print("fixtures")
fixture_scores = {}
for mode in ("strict", "unordered"):
    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=____, tool_args_match_mode="ignore")
    fixture_scores[mode] = {
        "reordered": evaluator(outputs=reversed_calls, reference_outputs=both)["score"],
        "one_call": evaluator(outputs=one, reference_outputs=both)["score"],
    }
    print(mode, fixture_scores[mode])
''', '''
from agentevals.trajectory.match import create_trajectory_match_evaluator

# man-01 is a single-tool case ; db-01 often over-calls and never matches unordered.
live = next(r for r in desk_results if r["id"] == "man-01")
reference_calls = [
    {"name": name, "args": {}, "id": f"ref-{i}"}
    for i, name in enumerate(next(c["expected_tools"] for c in SELECTED if c["id"] == "man-01"))
]
reference = [HumanMessage(next(c["question"] for c in SELECTED if c["id"] == "man-01")),
             AIMessage("", tool_calls=reference_calls)]

print("live scores (man-01)")
live_scores = {}
for mode in ("strict", "unordered"):
    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=mode, tool_args_match_mode="ignore")
    live_scores[mode] = evaluator(outputs=live["messages"], reference_outputs=reference)["score"]
    print(mode, ":", live_scores[mode])

call_a = {"name": "run_sql", "args": {"query": "SELECT 1"}, "id": "a"}
call_b = {"name": "search_manuals", "args": {"query": "fan"}, "id": "b"}
both = [AIMessage("", tool_calls=[call_a, call_b])]
reversed_calls = [AIMessage("", tool_calls=[call_b, call_a])]
one = [AIMessage("", tool_calls=[call_a])]

print("fixtures")
fixture_scores = {}
for mode in ("strict", "unordered"):
    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=mode, tool_args_match_mode="ignore")
    fixture_scores[mode] = {
        "reordered": evaluator(outputs=reversed_calls, reference_outputs=both)["score"],
        "one_call": evaluator(outputs=one, reference_outputs=both)["score"],
    }
    print(mode, fixture_scores[mode])
'''),
    hint("`trajectory_match_mode=mode` ; keep `tool_args_match_mode=\"ignore\"`."),
    code('''
# Installed strict match permits reordering inside one assistant message.
assert live_scores["unordered"] is True
assert fixture_scores["strict"]["reordered"] is True
assert fixture_scores["unordered"]["reordered"] is True
assert fixture_scores["strict"]["one_call"] is False
assert fixture_scores["unordered"]["one_call"] is False
print("check : PASS live unordered", live_scores, "fixtures", fixture_scores)
'''),
    md("""
    ## Step 4 : One score per agent

    Score the parts agent on a database case, the manuals agent on a manuals case,
    and both plus the desk on a mixed case.
    """),
    blank('''
def agent_score(agent, case):
    result = agent.invoke({"messages": [{"role": "user", "content": case["question"]}]}, LIMIT)
    row = score_answer(case, result)
    row["agent"] = agent.name
    return row


db_case = next(c for c in SELECTED if c["id"] == "db-01")
man_case = next(c for c in SELECTED if c["id"] == "man-01")
mix_case = next(c for c in SELECTED if c["id"] == "mix-01")

per_agent = [
    agent_score(____, db_case),
    agent_score(____, man_case),
    agent_score(parts_agent, mix_case),
    agent_score(manuals_agent, mix_case),
]
desk_mix = next(r for r in desk_results if r["id"] == "mix-01")
per_agent.append({"agent": "desk", **{k: desk_mix[k] for k in ("id", "facts_ok", "tools_ok", "used", "answer")}})
for row in per_agent:
    print(f"{row['agent']:8} {row['id']:8} facts {row['facts_ok']!s:5} tools {row['tools_ok']!s:5}")
''', '''
def agent_score(agent, case):
    result = agent.invoke({"messages": [{"role": "user", "content": case["question"]}]}, LIMIT)
    row = score_answer(case, result)
    row["agent"] = agent.name
    return row


db_case = next(c for c in SELECTED if c["id"] == "db-01")
man_case = next(c for c in SELECTED if c["id"] == "man-01")
mix_case = next(c for c in SELECTED if c["id"] == "mix-01")

per_agent = [
    agent_score(parts_agent, db_case),
    agent_score(manuals_agent, man_case),
    agent_score(parts_agent, mix_case),
    agent_score(manuals_agent, mix_case),
]
desk_mix = next(r for r in desk_results if r["id"] == "mix-01")
per_agent.append({"agent": "desk", **{k: desk_mix[k] for k in ("id", "facts_ok", "tools_ok", "used", "answer")}})
for row in per_agent:
    print(f"{row['agent']:8} {row['id']:8} facts {row['facts_ok']!s:5} tools {row['tools_ok']!s:5}")
'''),
    hint("`parts_agent` for the database case and `manuals_agent` for the manuals case."),
    code('''
assert any(r["agent"] == "parts" for r in per_agent)
assert any(r["agent"] == "manuals" for r in per_agent)
assert any(r["agent"] == "desk" for r in per_agent)
print("check : PASS per-agent rows")
'''),
    md("""
    ## If time permits

    - Re-score the live man-01 trajectory without `tool_args_match_mode="ignore"` ;
      empty reference args never match a live model's tool call, so the score fails
      for the wrong reason
    - Add `subset` and `superset` to the trajectory table
    - Replace the fact check with a trajectory judge on one mixed case
    """),
])


# ---------------------------------------------------------------------------
# exercise 11 · An Async Subagent on a Server
# ---------------------------------------------------------------------------
SERVER = r'''
import atexit
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx
from langgraph_sdk import get_sync_client

HERE = Path.cwd()
servers = []


def port_open(port):
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def wait_port_free(port, seconds=60):
    for _ in range(seconds * 2):
        if not port_open(port):
            return
        time.sleep(0.5)
    raise TimeoutError(f"Port {port} stayed busy after stop.")


def stop_server(proc):
    if proc is None:
        return
    port = getattr(proc, "course_port", None)
    was_running = proc.poll() is None
    if was_running:
        proc.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
        try:
            proc.wait(timeout=25)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               capture_output=True, check=False)
            else:
                proc.kill()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
    if was_running and port is not None:
        wait_port_free(port, seconds=90)


def start_server(port):
    if port not in (2134, 2135):
        raise ValueError("Use an exercises 08-11 port (2134 or 2135).")
    wait_port_free(port, seconds=90)
    log = (HERE / f"server-{port}.log").open("w", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", LANGGRAPH_CLI_NO_ANALYTICS="1")
    env["LANGSMITH_TRACING"] = "false"
    proc = subprocess.Popen(
        ["uv", "run", "langgraph", "dev", "--no-browser", "--no-reload", "--port", str(port),
         "--n-jobs-per-worker", "8", "--studio-url", "https://eu.smith.langchain.com"],
        cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    proc.course_port = port
    log.close()
    servers.append(proc)
    atexit.register(stop_server, proc)
    for _ in range(180):
        if proc.poll() is not None:
            raise RuntimeError((HERE / f"server-{port}.log").read_text(encoding="utf-8")[-5000:])
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/ok", timeout=1)
            if response.is_success:
                return proc
        except httpx.TransportError:
            pass
        time.sleep(0.5)
    stop_server(proc)
    raise TimeoutError("Agent Server did not become ready.")


def connect(port):
    return get_sync_client(url=f"http://127.0.0.1:{port}", api_key=None, timeout=240)


def clear_dev_storage():
    import shutil
    target = HERE / ".langgraph_api"
    if target.exists():
        shutil.rmtree(target)
        print("cleared :", target.name)
'''

GRAPH = r'''"""Aurelia diagnosis graphs for exercise 11."""
import asyncio
import json
import sqlite3
from pathlib import Path

from course_runtime import data, data_folder, llm
from deepagents import AsyncSubAgent, create_deep_agent
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from typing_extensions import NotRequired

DB = Path(data("capstone/service.db")).resolve()
MANUALS = Path(data_folder("capstone/manuals"))


@tool
def part_stock(part_no: str) -> str:
    """Look up an Aurelia part's stock and depot by its part number."""
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no = ?",
                          (part_no.upper(),)).fetchall()
    return json.dumps(rows)


@tool
def fault_guidance(error_code: str) -> str:
    """Read the meaning and first action for an Aurelia error code."""
    return "\n".join(f"[{p.name}] {line}" for p in sorted(MANUALS.glob("*.md"))
                     for line in p.read_text(encoding="utf-8").splitlines()
                     if line.startswith("| " + error_code.upper() + " |")) or "No matching code."


SYSTEM = ("Support Aurelia field engineers. Use tools for facts. Preserve stock, "
          "depot and first actions. Be brief.")
worker = create_agent(llm, tools=[part_stock, fault_guidance], system_prompt=SYSTEM, name="worker")


class WorkState(MessagesState):
    delay_seconds: NotRequired[float]


async def diagnose(state):
    text = str(state["messages"][-1].content)
    # Sleep unless the task says NO DELAY. Do not require the word DELAY : the
    # supervisor may paraphrase the launch text and drop it.
    if "NO DELAY" not in text:
        await asyncio.sleep(120)
    result = await worker.ainvoke({"messages": state["messages"]})
    return {"messages": result["messages"]}


builder = StateGraph(WorkState)
builder.add_node("diagnose", diagnose)
builder.add_edge(START, "diagnose")
builder.add_edge("diagnose", END)
diagnosis = builder.compile()

supervisor = create_deep_agent(
    model=llm,
    subagents=[AsyncSubAgent(name="diagnosis", graph_id="diagnosis",
                             description="Long Aurelia fault diagnosis with manuals and parts.")],
    system_prompt=(
        "Coordinate Aurelia diagnosis. Use only the requested async task tool, then "
        "respond briefly. After launch return to the user without checking. Copy full "
        "task IDs from async_tasks. Always fetch status before reporting it."
    ),
    name="supervisor",
)
'''

runtime = setup_source()
write_cell = (
    "from pathlib import Path\n"
    f"Path('course_runtime.py').write_text({runtime!r}, encoding='utf-8')\n"
    f"Path('graphs.py').write_text({GRAPH!r}, encoding='utf-8')\n"
    "config = {'dependencies': ['.'], 'graphs': {"
    "'diagnosis': './graphs.py:diagnosis', 'supervisor': './graphs.py:supervisor'}, "
    "'env': '../.env'}\n"
    "Path('langgraph.json').write_text(__import__('json').dumps(config, indent=2), encoding='utf-8')\n"
    "print('wrote course_runtime.py, graphs.py, langgraph.json')\n"
    "print(__import__('json').dumps(config, indent=2))\n"
)

write_exercise("exercise11-an-async-subagent-on-a-server", [
    md("""
    # Exercise 11 : An Async Subagent on a Server

    - Co-deployed graphs share one Agent Server ; the parent starts child work through async task tools
    - Lifecycle tools start, check, list and collect ; the parent copies full task ids from state
    - Local `langgraph dev` needs enough `--n-jobs-per-worker` for parent and child runs

    You will serve an Aurelia supervisor and a diagnosis worker, start a delayed
    diagnosis as an async subagent, check it, list it, collect the result, and stop
    the server. All data is made up.
    """),
    md("## Step 1 : Graphs and `langgraph.json`"),
    code(write_cell),
    code('''
print("check :", "PASS" if Path("graphs.py").exists() and Path("langgraph.json").exists() else "FAIL")
assert Path("graphs.py").exists() and Path("langgraph.json").exists()
'''),
    md("## Step 2 : Start the server"),
    code(SERVER),
    blank('''
clear_dev_storage()
server = start_server(____)
client = connect(____)
print("ready :", httpx.get("http://127.0.0.1:2134/ok").json())
print("assistants :", [(a["name"], a["graph_id"]) for a in client.assistants.search()])
''', '''
clear_dev_storage()
server = start_server(2134)
client = connect(2134)
print("ready :", httpx.get("http://127.0.0.1:2134/ok").json())
print("assistants :", [(a["name"], a["graph_id"]) for a in client.assistants.search()])
'''),
    hint("`2134` for both `start_server` and `connect`."),
    code('''
names = {a["graph_id"] for a in client.assistants.search()}
print("check :", "PASS" if {"diagnosis", "supervisor"} <= names else "FAIL", names)
assert {"diagnosis", "supervisor"} <= names
'''),
    md("""
    ## Step 3 : Start, check and list

    Start a delayed diagnosis (120 s hold), then check and list it. The first check
    should land while the task is still `running` ; print that status.
    """),
    blank('''
tid = client.threads.create()["thread_id"]
used = set()


def supervise(text):
    result = client.runs.wait(tid, "supervisor", input={"messages": [{"role": "user", "content": text}]},
                              config={"recursion_limit": 16}, raise_error=True)
    if "messages" not in result:
        raise RuntimeError("supervisor run finished without messages : " + repr(result)[:800])
    print("response :", result["messages"][-1]["content"])
    print("tasks :", result.get("async_tasks", {}))
    used.update(c["name"] for m in result["messages"] for c in m.get("tool_calls", []) or [])
    return result


out = supervise(
    "Use start_async_task for diagnosis. Task: DELAY then diagnose E-CT-110 and look up "
    "CT-FN-02 stock. Return the full task ID and stop. Do not check yet."
)
task_id = next(iter(out["async_tasks"]))
print("task ID :", task_id)
out = supervise(f"Use check_async_task for {task_id}. Report its fresh status and stop.")
first_status = out["async_tasks"][task_id]["status"]
print("first check status :", first_status)
out = supervise("Use list_async_tasks with status_filter all. Report the current list and stop.")
print("lifecycle so far :", sorted(used))
____
''', '''
tid = client.threads.create()["thread_id"]
used = set()


def supervise(text):
    result = client.runs.wait(tid, "supervisor", input={"messages": [{"role": "user", "content": text}]},
                              config={"recursion_limit": 16}, raise_error=True)
    if "messages" not in result:
        raise RuntimeError("supervisor run finished without messages : " + repr(result)[:800])
    print("response :", result["messages"][-1]["content"])
    print("tasks :", result.get("async_tasks", {}))
    used.update(c["name"] for m in result["messages"] for c in m.get("tool_calls", []) or [])
    return result


out = supervise(
    "Use start_async_task for diagnosis. Task: DELAY then diagnose E-CT-110 and look up "
    "CT-FN-02 stock. Return the full task ID and stop. Do not check yet."
)
task_id = next(iter(out["async_tasks"]))
print("task ID :", task_id)
out = supervise(f"Use check_async_task for {task_id}. Report its fresh status and stop.")
first_status = out["async_tasks"][task_id]["status"]
print("first check status :", first_status)
out = supervise("Use list_async_tasks with status_filter all. Report the current list and stop.")
print("lifecycle so far :", sorted(used))
assert {"start_async_task", "check_async_task", "list_async_tasks"} <= used
assert first_status == "running"
'''),
    hint("Assert the three lifecycle tools are in `used`, and that `first_status == \"running\"`."),
    code('''
print("first check status :", first_status)
print("check :", "PASS" if first_status == "running" and {"start_async_task", "check_async_task", "list_async_tasks"} <= used else "FAIL")
assert first_status == "running"
assert {"start_async_task", "check_async_task", "list_async_tasks"} <= used
'''),
    md("""
    ## Step 4 : Collect the result

    Join the child run, check again, confirm the diagnosis facts, and stop the server.
    """),
    blank('''
task = out["async_tasks"][task_id]
client.runs.join(task_id, task["run_id"])
out = supervise(f"Use check_async_task for {task_id}. Return the result, first action and stock.")
status = out["async_tasks"][task_id]["status"]
print("final status :", status)
text = str(out["messages"][-1]["content"]).lower()
print("answer text :", text[:500])
____
''', '''
task = out["async_tasks"][task_id]
client.runs.join(task_id, task["run_id"])
out = supervise(f"Use check_async_task for {task_id}. Return the result, first action and stock.")
status = out["async_tasks"][task_id]["status"]
print("final status :", status)
text = str(out["messages"][-1]["content"]).lower()
print("answer text :", text[:500])
assert status == "success"
assert "6" in text or "houten" in text or "fan" in text or "ct-fn-02" in text
'''),
    hint("`assert status == \"success\"` and check that the answer mentions stock or the fan."),
    code('''
for proc in servers:
    stop_server(proc)
print("servers stopped :", all(proc.poll() is not None for proc in servers))
print("check :", "PASS" if status == "success" else "FAIL")
assert status == "success"
'''),
    md("""
    ## If time permits

    - Cancel a second delayed task before it finishes
    - Steer the running task with `update_async_task` to look up UX-BT-02 instead
    - Restart the server in the same folder and read whether the thread still lists the task
    """),
])

