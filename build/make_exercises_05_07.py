"""Build exercises 05 to 07. Run from the repository root with uv run python."""
import argparse

from nb import ROOT, blank, code, hint, md, write_exercise

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--only", nargs="+", type=int, choices=[5, 6, 7], default=[5, 6, 7])
selected = parser.parse_args().only


COMMON = r'''
import json
import operator
import sqlite3
import threading
import time
from pathlib import Path
from typing import Annotated, TypedDict
from uuid import UUID, uuid4

from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command, interrupt

class Counter(BaseCallbackHandler):
    def __init__(self):
        self.lock = threading.Lock()
        self.calls = self.input_tokens = self.output_tokens = 0

    def on_chat_model_start(self, serialized, messages, **kwargs):
        with self.lock:
            self.calls += 1

    def on_llm_end(self, response, **kwargs):
        with self.lock:
            for batch in response.generations:
                for generation in batch:
                    usage = generation.message.usage_metadata or {}
                    self.input_tokens += usage.get("input_tokens", 0)
                    self.output_tokens += usage.get("output_tokens", 0)

counter = Counter()
llm = make_llm(callbacks=[counter], max_tokens=650, max_retries=0)
started = time.perf_counter()
DB = Path(data("capstone/service.db")).resolve()
LIMIT = {"recursion_limit": 24}

def part_facts(part_no):
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT part_no, name, stock, price_eur, depot FROM parts WHERE part_no = ?",
                         (part_no,)).fetchone()
    if row is None:
        raise ValueError("Unknown Aurelia part")
    return dict(row)

def check(label, condition):
    print("check :", label, "PASS" if condition else "FAIL")
    assert condition, label

def finish_metrics(slug, server_usage=None):
    rows = server_usage or []
    result = {"model": MODEL, "rps": float(os.environ.get("COURSE_RPS", "0.3")),
              "calls": counter.calls + len(rows),
              "input_tokens": counter.input_tokens + sum(r.get("input_tokens", 0) for r in rows),
              "output_tokens": counter.output_tokens + sum(r.get("output_tokens", 0) for r in rows),
              "seconds": round(time.perf_counter() - started, 1)}
    print("metrics :", json.dumps(result))
    Path(slug + "-metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
'''


def challenge(solution, replacements):
    skeleton = solution
    for answer, placeholder in replacements:
        assert answer in skeleton, answer
        skeleton = skeleton.replace(answer, placeholder, 1)
    return blank(skeleton, solution)


def build(number, slug, title, footer, references, steps, extensions, cells, final=None):
    if number not in selected:
        return
    filename = f"exercise{number:02d}-{slug}"
    task = {5: "Build a service desk that calls a separately served parts agent over A2A",
            6: "Build two agents that negotiate a fixed Aurelia filter order under private price policies",
            7: "Build a supervisor whose parts subagent pauses for approval before recording an order"}[number]
    opening = (f"# Exercise {number:02d} : {title}\n\n"
               f"Open `exercises/{filename}.ipynb` and run the setup cell. "
               f"{task} by replacing the `____` blanks. "
               f"The solution is `solutions/{filename}.ipynb`.\n\n"
               f"Worked examples to revisit : {references}\n\n"
               "Made up, not from work. Use the supplied Aurelia data and fictional policy values.")
    optional = "### If time permits\n\n" + "\n".join("- " + item for item in extensions)
    notebook_cells = [md(opening), code(COMMON), *cells, md(optional)]
    notebook_cells += [code(final or f'finish_metrics("{filename}")')]
    write_exercise(filename, notebook_cells)
    front = f"---\nmarp: true\ntheme: spiraltrain\nsize: 16:10\npaginate: true\nfooter: {footer}\n---\n\n"
    guide = front + opening + "\n\n---\n\n" + "\n\n---\n\n".join(
        f"### Step {i} : {name}\n\n{text}" for i, (name, text) in enumerate(steps, 1)
    ) + "\n\n---\n\n" + optional + "\n"
    target = ROOT / "src" / "exercises" / f"{number:02d}-{slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(guide, encoding="utf-8")


SERVER_MODEL = r'''
import json
import operator
import os
import runpy
import sqlite3
import time
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import httpx
from langchain.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
setup = runpy.run_path(str(ROOT / "build" / "setup_cell.py"))
llm = setup["make_llm"](max_tokens=500, max_retries=0)

class ServedState(MessagesState):
    usage_history: Annotated[list[dict], operator.add]
    exchange: dict
'''

SPECIALIST = r'''
def answer(state):
    database = ROOT / "data/capstone/service.db"
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no IN ('CT-FN-02', 'CT-SR-03')").fetchall()
    reply = llm.invoke([SystemMessage(
        "Report Aurelia stock from these facts only. Keep part numbers, counts and depots. "
        "Do not reserve anything.\n" + json.dumps(rows)), *state["messages"]])
    return {"messages": [reply], "usage_history": [reply.usage_metadata or {}]}

b = StateGraph(ServedState)
b.add_node("answer", answer)
b.add_edge(START, "answer")
b.add_edge("answer", END)
graph = b.compile()
'''

COORDINATOR = r'''
def coordinate(state, config):
    context = str(config["configurable"]["thread_id"])
    time.sleep(1 / float(os.environ["COURSE_RPS"]))
    with httpx.Client(timeout=240, trust_env=False) as client:
        search = client.post("http://127.0.0.1:2125/assistants/search", json={"limit": 20})
        search.raise_for_status()
        specialist_id = next(a["assistant_id"] for a in search.json() if a["graph_id"] == "aurelia_parts")
        request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "SendMessage", "params": {
            "message": {"role": "ROLE_USER", "messageId": str(uuid4()), "contextId": context,
                        "parts": [{"text": str(state["messages"][-1].content)}]},
            "configuration": {"historyScope": "task"}}}
        response = client.post("http://127.0.0.1:2125/a2a/" + specialist_id,
                               json=request, headers={"Accept": "application/json"})
        response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError("Specialist A2A request failed")
    task = body["result"]["task"]
    if task["status"]["state"] != "TASK_STATE_COMPLETED":
        raise RuntimeError("Specialist task did not complete")
    evidence = "\n".join(p["text"] for a in task.get("artifacts", []) for p in a["parts"] if "text" in p)
    time.sleep(1 / float(os.environ["COURSE_RPS"]))
    reply = llm.invoke([SystemMessage("Write an Aurelia service handover from the specialist evidence. "
                                     "Preserve counts and depots. No order was placed.\n" + evidence),
                        *state["messages"]])
    return {"messages": [reply], "usage_history": [reply.usage_metadata or {}],
            "exchange": {"request": request, "remote_task_id": task["id"],
                         "remote_context_id": task["contextId"], "evidence": evidence}}

b = StateGraph(ServedState)
b.add_node("coordinate", coordinate)
b.add_edge(START, "coordinate")
b.add_edge("coordinate", END)
graph = b.compile()
'''

SERVER_HELPERS = r'''
import atexit
import socket
import subprocess
import httpx

servers = []

def stop_servers():
    for process in reversed(servers):
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, check=True)
            else:
                os.killpg(process.pid, 15)
            process.wait(timeout=20)

atexit.register(stop_servers)

def start_server(port, graph_id, folder):
    if port not in {2124, 2125}:
        raise ValueError("Use only ports 2124 and 2125")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))
    config = folder / "langgraph.json"
    config.write_text(json.dumps({"dependencies": ["."], "graphs": {graph_id: "./graph.py:graph"}}), encoding="utf-8")
    env = os.environ.copy()
    env["COURSE_RPS"] = os.environ.get("COURSE_RPS", "0.06")
    env["PYTHONUTF8"] = "1"
    env["LANGSMITH_TRACING"] = "false"
    process = subprocess.Popen(["uv", "run", "langgraph", "dev", "--port", str(port),
                                "--config", str(config), "--no-browser", "--no-reload", "--allow-blocking"],
                               cwd=folder, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                               start_new_session=os.name != "nt")
    servers.append(process)
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Agent Server exited. Check the edited graph source.")
        try:
            if httpx.get(url + "/ok", timeout=3, trust_env=False).status_code == 200:
                return url
        except httpx.TransportError:
            pass
        time.sleep(0.5)
    raise TimeoutError("Agent Server readiness timed out")

def assistant_for(url, graph_id):
    response = httpx.post(url + "/assistants/search", json={"limit": 20}, trust_env=False, timeout=30)
    response.raise_for_status()
    return next(a["assistant_id"] for a in response.json() if a["graph_id"] == graph_id)

def rpc(url, assistant_id, method, params):
    response = httpx.post(url + "/a2a/" + assistant_id, trust_env=False, timeout=240,
                          headers={"Accept": "application/json"},
                          json={"jsonrpc": "2.0", "id": str(uuid4()), "method": method, "params": params})
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError("A2A request failed")
    return body["result"]

def send_params(text, context):
    return {"message": {"role": "ROLE_USER", "messageId": str(uuid4()), "contextId": context,
                        "parts": [{"text": text}]}, "configuration": {"historyScope": "task"}}

def task_text(task):
    return "\n".join(p["text"] for a in task.get("artifacts", []) for p in a["parts"] if "text" in p)

def thread_state(url, context):
    response = httpx.get(url + "/threads/" + context + "/state", trust_env=False, timeout=30)
    response.raise_for_status()
    return response.json()["values"]
'''

CARDS = r'''
try:
    parts_url = start_server(2125, "aurelia_parts", parts_folder)
    desk_url = start_server(2124, "aurelia_desk", desk_folder)
    parts_id = assistant_for(parts_url, "aurelia_parts")
    desk_id = assistant_for(desk_url, "aurelia_desk")
    cards = []
    for url, assistant_id in [(parts_url, parts_id), (desk_url, desk_id)]:
        response = httpx.get(url + "/.well-known/agent-card.json",
                             params={"assistant_id": assistant_id}, trust_env=False, timeout=30)
        response.raise_for_status()
        card = response.json()
        cards.append(card)
        print("card :", card["name"], card["supportedInterfaces"])
        UUID(assistant_id)
except Exception:
    stop_servers()
    raise
check("both cards advertise JSONRPC", all(c["supportedInterfaces"][0]["protocolBinding"] == "JSONRPC" for c in cards))
'''

FIRST_TASK = r'''
try:
    context = str(uuid4())
    first = rpc(desk_url, desk_id, "SendMessage", send_params(
        "Report CT-FN-02 and CT-SR-03 stock and depots for an Aurelia CT-400 visit.", context))["task"]
    first_state = thread_state(desk_url, context)
    first_exchange = first_state["exchange"]
    print("handover :", task_text(first))
    print("remote exchange :", first_exchange)
    print("task ids :", first["id"], first_exchange["remote_task_id"])
except Exception:
    stop_servers()
    raise
check("completed with text", first["status"]["state"] == "TASK_STATE_COMPLETED" and bool(task_text(first)))
check("two tasks share context", first["contextId"] == first_exchange["remote_context_id"] == context
      and first["id"] != first_exchange["remote_task_id"])
check("stock evidence", all(p in first_exchange["evidence"] for p in ["CT-FN-02", "CT-SR-03", "Houten"]))
'''

FOLLOW_UP = r'''
try:
    follow = rpc(desk_url, desk_id, "SendMessage", send_params("Which of those two parts is out of stock?", context))["task"]
    fetched = rpc(desk_url, desk_id, "GetTask", {"id": follow["id"], "historyScope": "task"})
    whole = rpc(desk_url, desk_id, "GetTask", {"id": follow["id"]})
    desk_state = thread_state(desk_url, context)
    parts_state = thread_state(parts_url, context)
    server_usage = desk_state["usage_history"] + parts_state["usage_history"]
    print("follow-up :", task_text(follow))
    print("GetTask keys :", sorted(fetched))
    print("history lengths :", len(fetched.get("history", [])), len(whole.get("history", [])))
    print("server usage :", server_usage)
except Exception:
    stop_servers()
    raise
check("new task in same context", follow["id"] != first["id"] and follow["contextId"] == context)
check("GetTask is unwrapped", fetched["id"] == follow["id"] and "artifacts" not in fetched)
check("task history selects follow-up", len(fetched.get("history", [])) < len(whole.get("history", [])))
check("follow-up identifies unavailable part", "CT-SR-03" in task_text(follow))
check("all served calls counted", len(server_usage) == 4 and all(r.get("total_tokens", 0) > 0 for r in server_usage))
'''

build(5, "two-agents-over-a2a", "Two Agents over A2A", "Agent Communication",
      "module 06 demo03 · served-agents, demo04 · two-agents-over-a2a.", [
    ("Graph sources", "Complete the coordinator's JSON-RPC method, assistant UUID field and context field. Run the cell to write both edited graph sources into separate runtime folders.\n\nWhich server can read the Aurelia parts database?"),
    ("Agent cards", "Start the parts agent on 2125 and the desk agent on 2124. Complete the card request with the discovered assistant UUID. Read both advertised interfaces.\n\nWhy does the graph name work for discovery but fail as the A2A assistant id?"),
    ("First task", "Create a UUID context and send the visit request to the desk. Extract the task from `SendMessage`, then inspect the desk's stored remote exchange.\n\nWhich code calls the parts server, and why do the two task ids differ?"),
    ("Same context", "Send a new message with the saved context and no completed task id. Fetch that task with `GetTask` and compare task-only history with full-context history.\n\nWhere is the answer text, and does `historyScope` limit model input?"),
    ("Shutdown", "Run the final cell to stop both process trees and print their measured calls and tokens. Use `stop_servers()` immediately if a cell fails while a server is running.\n\nAre both reserved ports released?"),
], [
    "Send a third question through the desk with the same context and inspect both histories",
    "Call the specialist with `message/send` and compare its response shape with `SendMessage`",
    "Send an invalid non-UUID context and inspect the JSON-RPC error without making a model call",
], [
    md("## Step 1 : Graph sources\n\nComplete the coordinator source below. Run each source-writing cell before starting the servers. Agent Server requires the local Windows course environment and the installed server group."),
    code(SERVER_HELPERS),
    code("server_prelude = r'''\n" + SERVER_MODEL.strip() + "\n'''"),
    code("specialist_source = server_prelude + r'''\n" + SPECIALIST.strip() + "\n'''"),
    challenge("coordinator_source = server_prelude + r'''\n" + COORDINATOR.strip() + "\n'''", [
        ('"method": "SendMessage"', '"method": ____'),
        ('a["assistant_id"]', 'a[____]'),
        ('"contextId": context', '"contextId": ____'),
    ]),
    hint("Use `SendMessage`, the `assistant_id` returned by search, and the parent's UUID `thread_id` as `contextId`. The edited source string is the file the server loads."),
    code(r'''
if ROOT is None:
    raise RuntimeError("Run this server exercise in the local course repository")
runtime = Path.cwd() / "exercise05-two-agents-over-a2a" / "workspace"
parts_folder, desk_folder = runtime / "parts", runtime / "desk"
for folder, source in [(parts_folder, specialist_source), (desk_folder, coordinator_source)]:
    compile(source, "graph.py", "exec")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "graph.py").write_text(source, encoding="utf-8")
check("edited sources written", all((p / "graph.py").exists() for p in [parts_folder, desk_folder]))
'''),
    md("## Step 2 : Agent cards\n\nComplete the card query. The UUID comes from `/assistants/search`. Inspect the printed interface before sending any task."),
    challenge(CARDS, [('params={"assistant_id": assistant_id}', 'params={"assistant_id": ____}')]),
    hint("Pass the discovered `assistant_id`, not `aurelia_parts` or `aurelia_desk`."),
    md("## Step 3 : First task\n\nFill the context constructor, method and result key. Read the stored exchange to confirm that the desk itself called the specialist."),
    challenge(FIRST_TASK, [('str(uuid4())', 'str(____())'), ('"SendMessage"', '____'), (')["task"]', ')[____]')]),
    hint("Use `uuid4`, `SendMessage` and `task`. Both servers store a thread with the same context UUID."),
    md("## Step 4 : Same context\n\nKeep `context` and request a new task. Compare the answer artifacts with the keys returned by `GetTask`. `historyScope=\"task\"` filters response history for the requested task. It does not trim model input."),
    challenge(FOLLOW_UP, [('"Which of those two parts is out of stock?", context', '"Which of those two parts is out of stock?", ____'),
                          ('"GetTask", {"id": follow["id"]', '____, {"id": follow["id"]')]),
    hint("Reuse `context`, omit `taskId`, and use `GetTask`. Its result is the task itself."),
    md("## Step 5 : Shutdown\n\nRun the final cell after the optional work. It stops only the servers this notebook started. Server calls are counted from the persisted usage lists on both servers."),
], final=r'''
stop_servers()
check("both servers stopped", len(servers) == 2 and all(p.poll() is not None for p in servers))
for port in [2124, 2125]:
    with socket.socket() as probe:
        check(f"port {port} released", probe.connect_ex(("127.0.0.1", port)) != 0)
finish_metrics("exercise05-two-agents-over-a2a", server_usage)
''')


POLICIES = r'''
from dataclasses import dataclass
from pydantic import BaseModel, Field

FACTS = part_facts("MR-HF-01")
ORDER = {"part_no": FACTS["part_no"], "quantity": 3, "list_price_eur": FACTS["price_eur"],
         "stock": FACTS["stock"], "depot": FACTS["depot"]}

@dataclass(frozen=True)
class Principal:
    role: str
    scope: str
    policy: dict

BUYER = Principal("buyer", "purchase-quote", {"opening_eur": 210, "ceiling_eur": 280})
SELLER = Principal("seller", "sales-quote", {"opening_eur": 300, "floor_eur": 240})

def read_policy(principal, owner):
    expected_scope = {"buyer": "purchase-quote", "seller": "sales-quote"}
    if principal.role != owner or principal.scope != expected_scope[owner]:
        raise PermissionError("Policy outside this principal's scope")
    return dict(principal.policy)

@tool
def buyer_policy(runtime: ToolRuntime[Principal]) -> str:
    """Read the buyer's own opening offer and price ceiling."""
    return json.dumps(read_policy(runtime.context, "buyer"))

@tool
def seller_policy(runtime: ToolRuntime[Principal]) -> str:
    """Read the seller's own opening ask and floor price."""
    return json.dumps(read_policy(runtime.context, "seller"))

class Quote(BaseModel):
    unit_eur: int = Field(ge=1)
    reason: str

print("order :", ORDER)
print("buyer tool schema :", buyer_policy.args)
print("seller tool schema :", seller_policy.args)
'''

AGENTS = r'''
buyer = create_agent(llm, tools=[buyer_policy], context_schema=Principal, response_format=Quote,
    system_prompt="You are Aurelia procurement. Minimise the unit price for the fixed order. "
                  "Read buyer_policy before quoting. Never exceed your own ceiling. "
                  "In round 1 use your opening offer. In round 2 concede up to your ceiling to reach agreement. "
                  "Return a Quote. Other agents' private policies are unavailable.")
seller = create_agent(llm, tools=[seller_policy], context_schema=Principal, response_format=Quote,
    system_prompt="You sell Aurelia spare parts. Maximise the unit price for the fixed order. "
                  "Read seller_policy before quoting. Never quote below your own floor. "
                  "In round 1 use your opening ask. In round 2 concede down to your floor to reach agreement. "
                  "Return a Quote. Keep the floor price out of your reason.")

def propose(agent, principal, round_no, previous):
    task = {"order": ORDER, "round": round_no, "public_previous_offers": previous}
    out = agent.invoke({"messages": [HumanMessage(json.dumps(task))]}, LIMIT, context=principal)
    quote = out["structured_response"]
    tool_names = [m.name for m in out["messages"] if isinstance(m, ToolMessage)]
    expected = principal.role + "_policy"
    check(principal.role + " read only its own tool", expected in tool_names and set(tool_names) == {expected})
    if principal.role == "buyer":
        check("buyer ceiling", quote.unit_eur <= principal.policy["ceiling_eur"])
    else:
        check("seller floor", quote.unit_eur >= principal.policy["floor_eur"])
    public = {"role": principal.role, "unit_eur": quote.unit_eur}
    print("public quote :", public)
    return public

check("private fields absent from public order", "floor_eur" not in ORDER and "ceiling_eur" not in ORDER)
'''

SETTLE = r'''
def settle(proposals, quantity, stock):
    offers = {p["role"]: p["unit_eur"] for p in proposals}
    if not 0 < quantity <= stock:
        return {"status": "review", "reason": "quantity exceeds available stock", "external_action": False}
    if offers["buyer"] < offers["seller"]:
        return {"status": "review", "reason": "price ranges do not overlap", "external_action": False}
    unit_eur = (offers["buyer"] + offers["seller"]) / 2
    return {"status": "draft", "unit_eur": unit_eur, "quantity": quantity,
            "total_eur": unit_eur * quantity, "external_action": False}

class Negotiation(TypedDict):
    round_no: int
    previous: list[dict]
    proposals: Annotated[list[dict], operator.add]
    settlement: dict

def buyer_node(state):
    return {"proposals": [propose(buyer, BUYER, state["round_no"], state["previous"])]}

def seller_node(state):
    return {"proposals": [propose(seller, SELLER, state["round_no"], state["previous"])]}

def settle_node(state):
    return {"settlement": settle(state["proposals"], ORDER["quantity"], ORDER["stock"])}

b = StateGraph(Negotiation)
b.add_node("buyer", buyer_node)
b.add_node("seller", seller_node)
b.add_node("settle", settle_node)
b.add_edge(START, "buyer")
b.add_edge(START, "seller")
b.add_edge(["buyer", "seller"], "settle")
b.add_edge("settle", END)
negotiation = b.compile()
fixed = [{"role": "buyer", "unit_eur": 280}, {"role": "seller", "unit_eur": 240}]
check("midpoint draft", settle(fixed, 3, 9)["total_eur"] == 780)
check("crossed prices need review", settle([fixed[0], {"role": "seller", "unit_eur": 300}], 3, 9)["status"] == "review")
check("stock violation needs review", settle(fixed, 10, 9)["status"] == "review")
'''

NEGOTIATE = r'''
previous = []
rounds = []
for round_no in [1, 2]:
    out = negotiation.invoke({"round_no": round_no, "previous": previous, "proposals": []}, LIMIT)
    previous = sorted(out["proposals"], key=lambda p: p["role"])
    rounds.append(out)
    print("round :", round_no, "settlement :", out["settlement"])
    check("both proposals retained", [p["role"] for p in previous] == ["buyer", "seller"])
    check("public offers contain no private policy", all(set(p) == {"role", "unit_eur"} for p in previous))
check("opening offers conflict", rounds[0]["settlement"]["status"] == "review")
final = rounds[-1]["settlement"]
check("bounded negotiation completed", len(rounds) == 2 and not final["external_action"])
if final["status"] == "draft":
    check("draft within both policies", SELLER.policy["floor_eur"] <= final["unit_eur"] <= BUYER.policy["ceiling_eur"])
else:
    check("unresolved conflict reaches review", final["status"] == "review")
check("database unchanged", part_facts(ORDER["part_no"]) == FACTS)
'''

DENIAL = r'''
try:
    read_policy(BUYER, "seller")
    denied = False
except PermissionError as exc:
    denied = True
    print("buyer denied :", str(exc))
check("buyer cannot read seller floor", denied)
forged = Principal("seller", "purchase-quote", BUYER.policy)
try:
    read_policy(forged, "seller")
    wrong_scope_denied = False
except PermissionError:
    wrong_scope_denied = True
check("role name alone grants no access", wrong_scope_denied)
check("identity absent from model arguments", buyer_policy.args == seller_policy.args == {})
'''

build(6, "buyer-and-seller", "Buyer and Seller", "Agent Communication",
      "module 06 demo06 · conflicts, demo07 · buyer-and-seller.", [
    ("Private policies", "Read the three-filter order from Aurelia stock. Complete `read_policy` so both the owner and credential scope must match before any policy is returned. Keep the fictional opening prices and limits in the supplied principals.\n\nWhich values belong to the order, and which belong to one role?"),
    ("Scoped agents", "Give each agent only its own policy tool. Keep identity in trusted runtime context. Inspect the tool schema and run the proposal helper.\n\nCan the model change the role through a tool argument?"),
    ("Settlement", "Collect both proposals with the reducer and join before settlement. Write the rule : invalid quantity or a buyer offer below the seller's ask goes to review ; overlapping prices produce a midpoint draft. Run the supplied boundary checks.\n\nWhy does retaining both proposals differ from choosing the last writer?"),
    ("Negotiation", "Run two rounds. Pass only public prices into the second round. Inspect the opposing opening offers and the concession result. Keep an unresolved conflict in review.\n\nDid the pair reach a draft, and which rule protects stock and price?"),
    ("Access denial", "Attempt to read the seller policy using the buyer principal. Also try a seller role with the buyer credential scope. Run the final metrics cell.\n\nDoes the denial come from a prompt or an access check?"),
], [
    "Raise the seller floor above the buyer ceiling and keep the result in review",
    "Replace the midpoint rule with a model judge, then check its output against both policies",
    "Add a delivery deadline to each private policy and share only the proposed delivery date",
], [
    md("## Step 1 : Private policies\n\nComplete the owner and scope checks before returning policy data. Opening prices, ceiling and floor are fictional lab inputs. The order facts come from the read-only Aurelia database."),
    challenge(POLICIES, [('principal.role != owner', 'principal.role != ____'),
                         ('principal.scope != expected_scope[owner]', 'principal.scope != ____')]),
    hint("Compare the principal's role with `owner` and its scope with `expected_scope[owner]`. Reject before reading its policy."),
    code('check("buyer policy available", read_policy(BUYER, "buyer")["ceiling_eur"] == 280)\ncheck("seller policy available", read_policy(SELLER, "seller")["floor_eur"] == 240)'),
    md("## Step 2 : Scoped agents\n\nFill the two tool lists. Each fresh proposal receives its own principal and the public order. Agent transcripts stay in the proposal helper ; only the selected price returns to the negotiation."),
    challenge(AGENTS, [('tools=[buyer_policy]', 'tools=[____]'), ('tools=[seller_policy]', 'tools=[____]')]),
    hint("Use `buyer_policy` for the buyer and `seller_policy` for the seller. `ToolRuntime` injects context without adding model arguments."),
    md("## Step 3 : Settlement\n\nFill the overlap comparison, midpoint and join. Run the fixtures before making model calls."),
    challenge(SETTLE, [('offers["buyer"] < offers["seller"]', '____'),
                       ('(offers["buyer"] + offers["seller"]) / 2', '____'),
                       ('b.add_edge(["buyer", "seller"], "settle")', 'b.add_edge(____, "settle")')]),
    hint("A buyer bid below the seller ask has no overlap. Average the two accepted prices. Join with `[\"buyer\", \"seller\"]`."),
    md("## Step 4 : Negotiation\n\nRun the two bounded rounds. The model may keep the prices apart ; the same rule sends that result to review. Inspect the printed offers before treating a draft as acceptable."),
    code(NEGOTIATE),
    md("## Step 5 : Access denial\n\nUse the buyer identity for the prohibited read. The lab enforces tool and data access inside one Python process. Production credentials and downstream permissions require separate service identities. The notebook author can inspect Python memory."),
    challenge(DENIAL, [('read_policy(BUYER, "seller")', 'read_policy(____, "seller")')]),
    hint("Use `BUYER`, preserving its purchase scope. Hiding a tool alone is insufficient ; the policy service must also deny the call."),
])


ORDER_DATA = r'''
ORDERS = {}
tool_entries = {}
review_entries = {}
REQUESTS = [
    {"order_id": "A-approve", "part_no": "MR-HF-01", "quantity": 5},
    {"order_id": "A-edit", "part_no": "CT-FN-02", "quantity": 3},
    {"order_id": "A-reject", "part_no": "CT-DM-04", "quantity": 1},
]

def reviewer(total_eur):
    return "manager" if total_eur > 10000 else "lead"

def validated_order(order):
    facts = part_facts(order["part_no"])
    quantity = order["quantity"]
    if type(quantity) is not int or not 0 < quantity <= facts["stock"]:
        raise ValueError("Quantity must be positive and within stock")
    return {**order, "total_eur": quantity * facts["price_eur"], "reviewer": reviewer(quantity * facts["price_eur"])}

for request in REQUESTS:
    print("order :", validated_order(request))
check("reviewer boundary", reviewer(10000) == "lead" and reviewer(10001) == "manager")
check("edit recomputes price", validated_order({**REQUESTS[1], "quantity": 1})["total_eur"] == 420)
'''

CHILD = r'''
class Purchase(TypedDict):
    order: dict
    note: str
    result: dict

def prepare(state):
    order = validated_order(state["order"])
    note = llm.invoke("Write one short Aurelia review note from these supplied order facts only. "
                      "No order has been recorded.\n" + json.dumps(order)).content
    return {"order": order, "note": note}

def review_order(state):
    order = state["order"]
    key = order["order_id"]
    review_entries[key] = review_entries.get(key, 0) + 1
    decision = interrupt({"order": order, "note": state["note"], "options": ["approve", "edit", "reject"]})
    action = decision["action"]
    if action == "reject":
        return {"result": {"order_id": key, "status": "rejected", "reason": decision["note"]}}
    if action == "edit":
        quantity = decision["quantity"]
        if quantity > order["quantity"]:
            raise ValueError("An increased quantity needs a fresh review")
        order = validated_order({**order, "quantity": quantity})
    elif action != "approve":
        raise ValueError("Unknown approval action")
    recorded = {**order, "status": "recorded", "decision": action, "external_action": False}
    if key in ORDERS and ORDERS[key] != recorded:
        raise ValueError("Order id already recorded with different values")
    ORDERS.setdefault(key, recorded)
    return {"result": recorded}

b = StateGraph(Purchase)
b.add_node("prepare", prepare)
b.add_node("review", review_order)
b.add_edge(START, "prepare")
b.add_edge("prepare", "review")
b.add_edge("review", END)
parts_subagent = b.compile()
check("child has no separate saver", parts_subagent.checkpointer is None)
'''

SUPERVISOR = r'''
@tool
def parts_specialist(order_id: str, part_no: str, quantity: int) -> str:
    """Ask the parts subagent to review and record one simulated Aurelia order."""
    tool_entries[order_id] = tool_entries.get(order_id, 0) + 1
    result = parts_subagent.invoke({"order": {"order_id": order_id, "part_no": part_no, "quantity": quantity}})
    return json.dumps(result["result"])

supervisor = create_agent(llm, tools=[parts_specialist], checkpointer=InMemorySaver(),
    system_prompt="Call parts_specialist exactly once with the requested order id, part and quantity. "
                  "After its result, report the recorded or rejected status and stop. "
                  "An edited result is authoritative. Never retry a rejected order.")
check("supervisor saver installed", supervisor.checkpointer is not None)
check("order ledger empty", ORDERS == {})
'''

PAUSE = r'''
configs = {}
paused = {}
for request in REQUESTS:
    key = request["order_id"]
    cfg = {"configurable": {"thread_id": str(uuid4())}, "recursion_limit": 24}
    configs[key] = cfg
    out = supervisor.invoke({"messages": [HumanMessage("Request this Aurelia order: " + json.dumps(request))]},
                            cfg, version="v2")
    paused[key] = out
    print("top-level interrupts :", [i.value for i in out.interrupts])
    print("top-level next :", supervisor.get_state(cfg).next)
    check("one nested approval", len(out.interrupts) == 1)
    check("requested order preserved", out.interrupts[0].value["order"]["order_id"] == key
          and out.interrupts[0].value["order"]["part_no"] == request["part_no"]
          and out.interrupts[0].value["order"]["quantity"] == request["quantity"])
    check("supervisor paused in tools", supervisor.get_state(cfg).next == ("tools",))
check("nothing recorded before approval", not ORDERS)
check("first entries counted", all(tool_entries[r["order_id"]] == review_entries[r["order_id"]] == 1 for r in REQUESTS))
'''

RESUME = r'''
decisions = {
    "A-approve": {"action": "approve"},
    "A-edit": {"action": "edit", "quantity": 1},
    "A-reject": {"action": "reject", "note": "Repair the detector first. Manager declines the purchase."},
}
completed = {}
for key, decision in decisions.items():
    out = supervisor.invoke(Command(resume=decision), configs[key], version="v2")
    completed[key] = out
    print("decision :", key, decision)
    for message in out.value["messages"]:
        if isinstance(message, ToolMessage):
            print("parts result :", message.content)
    print("supervisor :", out.value["messages"][-1].content)
    check("completed without another interrupt", not out.interrupts)
check("approved quantity retained", ORDERS["A-approve"]["quantity"] == 5 and ORDERS["A-approve"]["total_eur"] == 1550)
check("edited quantity and price", ORDERS["A-edit"]["quantity"] == 1 and ORDERS["A-edit"]["total_eur"] == 420)
rejected_results = [json.loads(m.content) for m in completed["A-reject"].value["messages"] if isinstance(m, ToolMessage)]
check("rejection recorded without order", "A-reject" not in ORDERS and rejected_results[-1]["status"] == "rejected")
print("entry counts :", {"tool": tool_entries, "review": review_entries})
print("simulated orders :", ORDERS)
check("code before interrupt replayed", all(tool_entries[r["order_id"]] == review_entries[r["order_id"]] == 2 for r in REQUESTS))
check("each approved action recorded once", len(ORDERS) == 2 and all(not o["external_action"] for o in ORDERS.values()))
'''

build(7, "approval-in-a-subagent", "Approval in a Subagent", "Advanced Workflows",
      "module 07 demo01 · interrupts, demo02b · in-a-subagent (demo02-interrupts-in-multi-agent). "
      "ARI510 exercise13 · human-approval supplies the order and reviewer case.", [
    ("Order policy", "Inspect the three Aurelia requests. Complete the reviewer threshold and stock validation. Keep every order behind approval ; use the lead up to 10,000 EUR and the manager above that value.\n\nHow does reducing the fan quantity change its total?"),
    ("Parts subagent", "Complete `interrupt` and the approve, edit and reject decisions in the child review node. Recompute an edited quantity before recording it. Keep the ledger write after approval.\n\nWhich statement before `interrupt` will run again?"),
    ("Supervisor tool", "Invoke the parts subagent inside the tool and return its result. Put the checkpointer on the supervisor. Let LangGraph propagate the child configuration.\n\nWhy would a separate child thread prevent this top-level resume?"),
    ("Top-level pause", "Start all three orders in separate supervisor threads. Find each interrupt through `out.interrupts` and inspect `get_state(cfg).next`.\n\nIs any order recorded while the supervisor waits in its tools node?"),
    ("Decisions", "Resume the supervisor threads : approve the filters, reduce the fan order to one, and reject the detector with a reason. Compare both entry counters before and after resume.\n\nWhy do the tool and review counters reach two while the accepted ledger has one entry per order?"),
], [
    "Try editing to quantity 0 or above stock and inspect the validation failure",
    "Print the supervisor state history and locate the pending approval checkpoint",
    "Add a second manager review after the lead approves an expensive order",
], [
    md("## Step 1 : Order policy\n\nFill the manager threshold and quantity bounds. All requests require a person. The supplied role policy adapts ARI510 exercise13's part-order case."),
    challenge(ORDER_DATA, [('total_eur > 10000', '____'), ('0 < quantity <= facts["stock"]', '____')]),
    hint("Use `total_eur > 10000` and `0 < quantity <= facts[\"stock\"]`. Edit recomputes the price from the database."),
    md("## Step 2 : Parts subagent\n\nFill the interrupt call and decision branches. The counter intentionally observes replay. The ledger represents a simulated action and writes only after approval. An edit may reduce quantity ; an increase needs a fresh review."),
    challenge(CHILD, [('decision = interrupt(', 'decision = ____('),
                      ('action == "reject"', 'action == ____'),
                      ('quantity = decision["quantity"]', 'quantity = ____'),
                      ('elif action != "approve"', 'elif action != ____')]),
    hint("Call `interrupt`, match `reject`, read the edited `decision[\"quantity\"]`, and accept `approve`. Compile the child without its own saver."),
    md("## Step 3 : Supervisor tool\n\nComplete the nested invocation and parent saver. Keep the tool result as JSON. Preserve the propagated interrupt instead of returning it as an ordinary tool result."),
    challenge(SUPERVISOR, [('parts_subagent.invoke(', '____.invoke('),
                           ('checkpointer=InMemorySaver()', 'checkpointer=____()')]),
    hint("Use `parts_subagent` and `InMemorySaver`. Leave the nested invocation config to LangGraph, as demo02b does."),
    md("## Step 4 : Top-level pause\n\nRun the requests and read the top-level payloads. Record the two entry counters before supplying a decision."),
    code(PAUSE),
    md("## Step 5 : Decisions\n\nFill the decisions and resume the saved supervisor configs. Compare the simulated ledger with both counters. The completed preparation node, including its model call, stays checkpointed ; the paused tool wrapper and review node execute again."),
    challenge(RESUME, [('"A-approve": {"action": "approve"}', '"A-approve": {"action": ____}'),
                       ('"A-edit": {"action": "edit", "quantity": 1}', '"A-edit": {"action": ____, "quantity": ____}'),
                       ('"A-reject": {"action": "reject"', '"A-reject": {"action": ____'),
                       ('Command(resume=decision)', 'Command(resume=____)')]),
    hint("Use `approve`, `edit` with quantity `1`, and `reject`. Resume each saved parent config with `decision`."),
])

print("exercises written :", selected)
