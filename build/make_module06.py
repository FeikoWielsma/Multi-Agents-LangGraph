"""Generate module 06. Run with uv run python build/make_module06.py."""
from nb import code, md, section, write_demo

MODULE = "06-agent-communication"

COMMON = r'''
import json
import operator
import sqlite3
import threading
import time
from pathlib import Path
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command


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
llm = make_llm(callbacks=[counter], max_tokens=500, max_retries=0)
started = time.perf_counter()
DB = Path(data("demo-world/service.db")).resolve()
MANUALS = Path(data_folder("demo-world/manuals"))
NOTEBOOK_DIR = ROOT / "notebooks" / "06-agent-communication" if ROOT else Path.cwd()


def stock(part="CE-CF-02"):
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT part_no, name, stock, price_eur, depot FROM parts WHERE part_no = ?", (part,)).fetchone()
    return dict(row) if row else {"part_no": part, "error": "unknown part"}


def guidance(error="F-CE-110"):
    return "\n".join(f"[{p.name}] {line}" for p in sorted(MANUALS.glob("*.md"))
                     for line in p.read_text(encoding="utf-8").splitlines()
                     if line.startswith("| " + error + " |"))


FACTS = stock()
QUESTION = "Report CE-CF-02 stock and location, then the first action and replacement condition for F-CE-110."
LIMIT = {"recursion_limit": 16}


def finish_metrics(name):
    row = {"model": MODEL, "rps": float(os.environ.get("COURSE_RPS", "0.3")),
           "calls": counter.calls, "input_tokens": counter.input_tokens,
           "output_tokens": counter.output_tokens, "seconds": round(time.perf_counter() - started, 1)}
    print("metrics :", row)
    (NOTEBOOK_DIR / (name + "-metrics.json")).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
'''


def demo(number, slug, title, cells, final=None):
    tail = [md("## Things to try\n\nOptional : we can change the part, the context boundary or the policy and inspect the result.")]
    tail += [code(final or f'finish_metrics("demo{number:02d}")')]
    write_demo(MODULE, f"demo{number:02d}-{slug}", [
        md(f"# Demo {number:02d} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        code(COMMON), *cells, *tail,
    ])


demo(1, "what-agents-share", "What agents share", [
    section("a · shared-state-or-messages", "We give a parts worker and a manuals worker the same maintenance request. A shared-state graph stores their findings in separate keys."),
    code(r'''
class Shared(TypedDict):
    question: str
    stock: dict
    guidance: str
    answer: str


def combine(state):
    return {"answer": llm.invoke(state["question"] + "\nEvidence only:\n"
                                + json.dumps(state["stock"]) + "\n" + state["guidance"]).content}


builder = StateGraph(Shared)
builder.add_node("parts", lambda s: {"stock": stock()})
builder.add_node("manuals", lambda s: {"guidance": guidance()})
builder.add_node("combine", combine)
builder.add_edge(START, "parts")
builder.add_edge(START, "manuals")
builder.add_edge(["parts", "manuals"], "combine")
builder.add_edge("combine", END)
shared = builder.compile().invoke({"question": QUESTION})
print("shared keys :", sorted(shared))
print("answer :", shared["answer"])
'''),
    md("We then pass an explicit message envelope. The receiver gets the payload we put in it. Shared state would also expose the caller's other fields. This local Python example has no network transport."),
    code(r'''
class Envelope(TypedDict):
    sender: str
    recipient: str
    correlation_id: str
    payload: dict


def receive(envelope: Envelope):
    print("received :", envelope)
    return llm.invoke("Write a stock note from this payload only.\n" + json.dumps(envelope["payload"])).content


envelope = Envelope(sender="parts", recipient="coordinator", correlation_id="BW-7001", payload=FACTS)
print("message answer :", receive(envelope))
'''),
    section("b · full-history-task-or-summary", "We compare full history, task-only input, a copied history with a new task, and a selected factual summary. The missing first-action request is deliberate in the task-only case."),
    code(r'''
history = [
    HumanMessage("Bus CE12-2021-0117 has F-CE-110. Include the first action and replacement condition."),
    AIMessage("Stock lookup complete. " + json.dumps(FACTS)),
    HumanMessage("Write the final maintenance note."),
]
task_only = [HumanMessage("Write a CE-CF-02 stock note. " + json.dumps(FACTS))]
fork = [*history, HumanMessage("Assess the inspection-first option. Preserve conditions.")]
summary = [HumanMessage("Maintenance case BW-7001. " + QUESTION + "\n" + json.dumps(FACTS))]
contexts = {"full history": history, "task only": task_only, "fork": fork, "summary": summary}
prompt = SystemMessage("Use visible facts only. Do not infer repair completion. Manual excerpt:\n" + guidance())
for name, messages in contexts.items():
    reply = llm.invoke([prompt, *messages])
    print("context :", name, [(m.type, m.content) for m in messages])
    print("answer :", reply.content)
    print("input tokens :", (reply.usage_metadata or {}).get("input_tokens"))
print("parent history :", len(history), "fork history :", len(fork))
'''),
    md("We copy the history in ordinary Python to expose the fork contract. No checkpoint fork or Deep Agents harness runs here. A summary can lose a condition at either boundary, so we inspect the worker's return before using it."),
    code(r'''
worker_answer = llm.invoke([prompt, *summary]).content
returned = {"case": "BW-7001", "worker": "maintenance", "summary": worker_answer}
print("summary back :", returned)
print("caller sees :", [history[-1].content, returned])
'''),
])


demo(2, "subgraph-communication", "Subgraph communication", [
    section("a · handoff-to-parent", "We transfer from a parts subgraph to a manuals node in its parent. Code fixes the route so we can inspect the communication boundary without relying on a model's transfer choice."),
    code(r'''
def parts_reply(state):
    reply = llm.invoke([SystemMessage("Return the part count and depot briefly.\n" + json.dumps(FACTS)),
                        *state["messages"]])
    return {"messages": [reply]}


def handoff(state):
    return Command(goto="manuals", graph=Command.PARENT,
                   update={"messages": state["messages"]})


child = StateGraph(MessagesState)
child.add_node("parts_reply", parts_reply)
child.add_node("handoff", handoff)
child.add_edge(START, "parts_reply")
child.add_edge("parts_reply", "handoff")


def manuals_reply(state):
    print("receiver :", [(m.type, m.content) for m in state["messages"]])
    return {"messages": [llm.invoke([SystemMessage("Combine the visible stock and manual facts.\n" + guidance()),
                                    *state["messages"]])]}


parent = StateGraph(MessagesState)
parent.add_node("parts", child.compile())
parent.add_node("manuals", manuals_reply)
parent.add_edge(START, "parts")
parent.add_edge("manuals", END)
result = parent.compile().invoke({"messages": [HumanMessage(QUESTION, id="case-request")]}, LIMIT)
print("answer :", result["messages"][-1].content)
print("message ids :", [m.id for m in result["messages"]])
'''),
    md("We use the parent's add_messages reducer to reconcile the forwarded history by message id. The receiver print lists the stock note. The written answer can still omit that stock. A return annotation of Command with a literal destination would register that name as an edge inside the child, which has no such node. A tool-triggered handoff also needs a matching ToolMessage receipt and one tool call at a time, as module 05 showed. This node-triggered transfer has no pending tool call."),
    section("b · shared-keys", "We port ARI510 demo23's compiled subgraph shape. The parts graph shares part_no and stock with its parent. Its working note remains inside the child schema."),
    code(r'''
class PartsState(TypedDict):
    part_no: str
    stock: dict
    working_note: str


class CaseState(TypedDict):
    case_id: str
    part_no: str
    stock: dict
    answer: str


parts = StateGraph(PartsState)
parts.add_node("lookup", lambda s: {"stock": stock(s["part_no"]), "working_note": "read-only inventory"})
parts.add_edge(START, "lookup")
parts.add_edge("lookup", END)
parts_graph = parts.compile()
case = StateGraph(CaseState)
case.add_node("parts", parts_graph)
case.add_node("report", lambda s: {"answer": llm.invoke("Report these facts briefly.\n" + json.dumps(s["stock"])).content})
case.add_edge(START, "parts")
case.add_edge("parts", "report")
case.add_edge("report", END)
result = case.compile().invoke({"case_id": "BW-7001", "part_no": "CE-CF-02"})
print("parent output :", result)
print("private key returned :", "working_note" in result)
'''),
    section("c · transformed-input-and-output", "We map a parent item field into the child's part_no field and return a selected stock finding. The child receives no parent-only requester field."),
    code(r'''
class RequestState(TypedDict):
    item: str
    requester: str
    finding: dict
    answer: str


def mapped_parts(state):
    child_input = {"part_no": state["item"]}
    print("child input :", child_input)
    child_output = parts_graph.invoke(child_input)
    print("child output :", child_output)
    return {"finding": child_output["stock"]}


mapped = StateGraph(RequestState)
mapped.add_node("parts", mapped_parts)
mapped.add_node("report", lambda s: {"answer": llm.invoke("Write a stock note from these facts.\n" + json.dumps(s["finding"])).content})
mapped.add_edge(START, "parts")
mapped.add_edge("parts", "report")
mapped.add_edge("report", END)
print("mapped parent :", mapped.compile().invoke({"item": "CE-CF-02", "requester": "workshop planner"}))
'''),
    md("We treat the wrapper as a data interface. Excluding a field from model input does not isolate credentials, Python memory, checkpoints or logs."),
])


SERVER = r'''
import atexit
import re
import subprocess
from uuid import UUID, uuid4, uuid5
import httpx

servers = []


def stop_servers():
    for process, log, handle in reversed(servers):
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=True)
            else:
                os.killpg(process.pid, 15)
            process.wait(timeout=20)
        handle.close()
    servers.clear()


atexit.register(stop_servers)


NAMESPACE_GRAPH = UUID("6ba7b821-9dad-11d1-80b4-00c04fd430c8")


def start_server(port, graphs, folder, keyless=False):
    if port not in {2124, 2125}:
        raise ValueError("Use the module's reserved ports.")
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / "langgraph.json"
    config.write_text(json.dumps({"dependencies": ["."], "graphs": graphs}), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if keyless:
        for key in list(env):
            if key.startswith(("LANGSMITH_", "LANGCHAIN_")):
                env.pop(key, None)
        env["LANGSMITH_TRACING"] = "false"
    log = folder / "server.tmp"
    handle = log.open("w", encoding="utf-8")
    process = subprocess.Popen(["uv", "run", "langgraph", "dev", "--port", str(port),
                                "--config", str(config), "--no-browser", "--no-reload",
                                "--allow-blocking"],
                               cwd=folder, env=env, stdout=handle, stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                               start_new_session=os.name != "nt")
    servers.append((process, log, handle))
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Agent Server exited. See " + str(log))
        try:
            response = httpx.get(url + "/ok", timeout=3, trust_env=False)
            if response.status_code == 200:
                print("server :", url, "ready")
                return url
        except httpx.TransportError:
            pass
        time.sleep(0.5)
    stop_servers()
    raise TimeoutError("Agent Server readiness timed out.")


def server_facts(index=0):
    text = servers[index][1].read_text(encoding="utf-8", errors="replace")
    studio = ""
    for line in text.splitlines():
        if "api_key" in line.lower() or "secret" in line.lower():
            continue
        match = re.search(r"https://[a-z.]*smith\.langchain\.com/studio/", line)
        if match:
            studio = match.group(0)
            break
    print("studio url :", studio)
    print("metadata loop skipped :", "skipping metadata loop" in text)
    print("EU metadata endpoint :", "eu.api.smith.langchain.com" in text)


def assistant_for(url, graph_id):
    response = httpx.post(url + "/assistants/search", json={"limit": 50}, timeout=30, trust_env=False)
    response.raise_for_status()
    matches = [row["assistant_id"] for row in response.json() if row.get("graph_id") == graph_id]
    if len(matches) != 1:
        raise RuntimeError("Expected one assistant for " + graph_id)
    derived = str(uuid5(NAMESPACE_GRAPH, graph_id))
    print("graph id :", graph_id)
    print("assistant id :", matches[0])
    print("uuid5 match :", matches[0] == derived)
    return matches[0]


def rpc(url, assistant, method, params):
    request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": method, "params": params}
    response = httpx.post(url + "/a2a/" + assistant, json=request, timeout=180, trust_env=False,
                          headers={"Accept": "application/json"})
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError(json.dumps(body["error"]))
    return body["result"]


def send_params(text, context_id=None):
    message = {"role": "ROLE_USER", "messageId": str(uuid4()), "parts": [{"text": text}]}
    if context_id:
        message["contextId"] = context_id
    return {"message": message, "configuration": {"historyScope": "task"}}


def task_text(task):
    return "\n".join(part["text"] for artifact in task.get("artifacts", [])
                     for part in artifact.get("parts", []) if "text" in part)
'''

SERVER_MODEL = r'''
import runpy
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
setup = runpy.run_path(str(ROOT / "build" / "setup_cell.py"))
llm = setup["make_llm"](max_tokens=500, max_retries=0)
'''

SERVED = r'''
import json
import sqlite3
from langchain.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from server_model import ROOT, llm


class ServedState(MessagesState):
    usage: dict


def answer(state):
    with sqlite3.connect(f"file:{(ROOT / 'data/demo-world/service.db').as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no IN ('CE-CF-02', 'CE-DA-03')").fetchall()
    reply = llm.invoke([SystemMessage("Answer using this inventory only. Retain every count and depot.\n" + json.dumps(rows)),
                        *state["messages"]])
    return {"messages": [reply], "usage": reply.usage_metadata or {}}


builder = StateGraph(ServedState)
builder.add_node("answer", answer)
builder.add_edge(START, "answer")
builder.add_edge("answer", END)
graph = builder.compile()
'''

demo(3, "served-agents", "Served agents", [
    section("a · calling-a-served-agent", "We run a local Agent Server from the installed server group. We first check a graph that has no model or .env loader with both LangSmith key names removed from the subprocess environment."),
    code(SERVER),
    code(r'''
health_file = NOTEBOOK_DIR / "health_graph.py"
health_file.write_text('from langgraph.graph import StateGraph, MessagesState, START, END\n'
                       'from langchain.messages import AIMessage\n'
                       'b = StateGraph(MessagesState)\n'
                       'b.add_node("reply", lambda s: {"messages": [AIMessage("local echo")]})\n'
                       'b.add_edge(START, "reply")\nb.add_edge("reply", END)\ngraph = b.compile()\n', encoding="utf-8")
try:
    url = start_server(2124, {"echo": "./health_graph.py:graph"}, NOTEBOOK_DIR, keyless=True)
    native = httpx.post(url + "/runs/wait", json={"assistant_id": "echo", "input": {"messages": [
        {"role": "user", "content": "ping"}]}}, timeout=60, trust_env=False)
    native.raise_for_status()
    print("native graph name :", native.json()["messages"][-1]["content"])
    named = httpx.get(url + "/.well-known/agent-card.json", params={"assistant_id": "echo"}, trust_env=False)
    print("graph name card :", named.status_code, named.json()["error"]["message"])
    echo_id = assistant_for(url, "echo")
    rejected = httpx.post(url + "/a2a/echo", json={"jsonrpc": "2.0", "id": "graph-name", "method": "SendMessage",
                          "params": send_params("ping")}, timeout=30, trust_env=False,
                          headers={"Accept": "application/json"})
    print("graph name rpc :", rejected.json()["error"]["message"])
    echo = rpc(url, echo_id, "SendMessage", send_params("Check local execution."))["task"]
    print("without LangSmith key :", echo["status"]["state"], task_text(echo))
    server_facts()
finally:
    stop_servers()
'''),
    md("We load the course model from the shared setup source in the served graph. The subprocess inherits the repository environment, including the course request budget. We call the native runs/wait endpoint before using A2A."),
    code(f'''
(NOTEBOOK_DIR / "server_model.py").write_text({SERVER_MODEL!r}, encoding="utf-8")
(NOTEBOOK_DIR / "parts_graph.py").write_text({SERVED!r}, encoding="utf-8")
url = start_server(2124, {{"parts": "./parts_graph.py:graph"}}, NOTEBOOK_DIR)
try:
    response = httpx.post(url + "/runs/wait", json={{"assistant_id": "parts", "input": {{"messages": [
        {{"role": "user", "content": "Report CE-CF-02 stock and its depot."}}]}}}}, timeout=180, trust_env=False)
    response.raise_for_status()
    served = response.json()
    print("native answer :", served["messages"][-1]["content"])
    print("usage :", served["usage"])
except Exception:
    stop_servers()
    raise
'''),
    section("b · agent-card", "We fetch the generated agent card and use its advertised JSON-RPC interface. The card describes the assistant and its transport; it grants no credentials or permissions."),
    code(r'''
try:
    parts_id = assistant_for(url, "parts")
    card_response = httpx.get(url + "/.well-known/agent-card.json", params={"assistant_id": parts_id}, trust_env=False)
    card_response.raise_for_status()
    card = card_response.json()
    print("agent card :", json.dumps(card, indent=2))
    task = rpc(url, parts_id, "SendMessage", send_params("Report CE-DA-03 stock and its depot."))["task"]
    print("a2a state :", task["status"]["state"])
    print("a2a answer :", task_text(task))
    print("task keys :", sorted(task))
    context = task["contextId"]
    same = rpc(url, parts_id, "GetTask", {"id": task["id"], "historyScope": "task"})
    listed = rpc(url, parts_id, "ListTasks", {"contextId": context, "historyScope": "task"})
    print("get keys :", sorted(same))
    print("get status :", same["status"]["state"])
    print("get status text :", same["status"]["message"]["parts"][0]["text"])
    print("list count :", len(listed["tasks"]))
    native_state = httpx.get(url + "/threads/" + context + "/state", trust_env=False)
    native_state.raise_for_status()
    print("context is thread :", native_state.json()["values"]["messages"][-1]["content"])
    invalid = {"jsonrpc": "2.0", "id": "invalid-context", "method": "SendMessage",
               "params": send_params("Check inventory.", "BW-7001")}
    print("invalid context :", httpx.post(url + "/a2a/" + parts_id, json=invalid, trust_env=False,
                                           headers={"Accept": "application/json"}).json()["error"]["message"])
    server_facts()
except Exception:
    stop_servers()
    raise
'''),
    md("SendMessage returns result.task, including artifacts with the assistant text. GetTask returns the task directly and, on this server, a generic completion line with no artifacts. contextId is the server thread id and must be a UUID. The graph name works on runs/wait and is rejected on the A2A path."),
], final='stop_servers()\nprint("servers stopped :", not servers)\nfinish_metrics("demo03")')

COORDINATOR = r'''
import json
import os
import time
from uuid import uuid4
import httpx
from langchain.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from server_model import llm


class CoordinatorState(MessagesState):
    exchange: dict
    usage: dict


def coordinate(state, config):
    context_id = str(config["configurable"]["thread_id"])
    headers = {"Accept": "application/json"}
    with httpx.Client(timeout=180, trust_env=False) as client:
        listed = client.post("http://127.0.0.1:2125/assistants/search", json={"limit": 20})
        listed.raise_for_status()
        assistant_id = next(row["assistant_id"] for row in listed.json() if row.get("graph_id") == "parts")
        payload = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "SendMessage", "params": {
            "message": {"role": "ROLE_USER", "messageId": str(uuid4()), "contextId": context_id,
                        "parts": [{"text": str(state["messages"][-1].content)}]},
            "configuration": {"historyScope": "task"}}}
        response = client.post("http://127.0.0.1:2125/a2a/" + assistant_id, json=payload, headers=headers)
        response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError(json.dumps(body["error"]))
    task = body["result"]["task"]
    if task["status"]["state"] != "TASK_STATE_COMPLETED":
        raise RuntimeError(json.dumps(task["status"]))
    text = "\n".join(part["text"] for artifact in task.get("artifacts", []) for part in artifact["parts"] if "text" in part)
    time.sleep(1 / float(os.environ.get("COURSE_RPS", "0.3")))
    reply = llm.invoke([SystemMessage("Write a brief handover from the returned evidence only. Preserve counts and depots.\n" + text),
                        *state["messages"]])
    return {"messages": [reply], "exchange": {"request": payload, "response": body, "assistant_id": assistant_id},
            "usage": reply.usage_metadata or {}}


builder = StateGraph(CoordinatorState)
builder.add_node("coordinate", coordinate)
builder.add_edge(START, "coordinate")
builder.add_edge("coordinate", END)
graph = builder.compile()
'''

demo(4, "two-agents-over-a2a", "Two agents over A2A", [
    section("a · two-agents-over-a2a", "We start a coordinator and a parts specialist on separate ports with separate local storage. The coordinator node sends plain httpx JSON-RPC to the specialist; the notebook does not relay the specialist's answer."),
    code(SERVER),
    code(f'''
server_a = NOTEBOOK_DIR / "server-a"
server_b = NOTEBOOK_DIR / "server-b"
for folder in (server_a, server_b):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "server_model.py").write_text({SERVER_MODEL!r}, encoding="utf-8")
(server_b / "parts_graph.py").write_text({SERVED!r}, encoding="utf-8")
(server_a / "coordinator_graph.py").write_text({COORDINATOR!r}, encoding="utf-8")
try:
    parts_url = start_server(2125, {{"parts": "./parts_graph.py:graph"}}, server_b)
    coordinator_url = start_server(2124, {{"coordinator": "./coordinator_graph.py:graph"}}, server_a)
    parts_id = assistant_for(parts_url, "parts")
    coordinator_id = assistant_for(coordinator_url, "coordinator")
    for base, assistant in [(parts_url, parts_id), (coordinator_url, coordinator_id)]:
        response = httpx.get(base + "/.well-known/agent-card.json", params={{"assistant_id": assistant}}, trust_env=False)
        response.raise_for_status()
        print("agent card :", json.dumps(response.json(), indent=2))
    outer = rpc(coordinator_url, coordinator_id, "SendMessage", send_params("Report CE-CF-02 and CE-DA-03 stock and their depots."))["task"]
    print("coordinator state :", outer["status"]["state"])
    print("coordinator answer :", task_text(outer))
    context = outer["contextId"]
    state_response = httpx.get(coordinator_url + "/threads/" + context + "/state", trust_env=False)
    state_response.raise_for_status()
    coordinator_state = state_response.json()["values"]
    print("exchange :", json.dumps(coordinator_state["exchange"], indent=2))
    remote_task = coordinator_state["exchange"]["response"]["result"]["task"]
    print("same context :", context == remote_task["contextId"])
    print("different task :", outer["id"] != remote_task["id"])
    print("coordinator usage :", coordinator_state["usage"])
    remote_state = httpx.get(parts_url + "/threads/" + context + "/state", trust_env=False).json()["values"]
    print("specialist usage :", remote_state["usage"])
    follow = rpc(parts_url, parts_id, "message/send", send_params("Which of those parts is out of stock?", context))
    print("legacy state :", follow["status"]["state"])
    print("legacy keys :", sorted(follow))
    print("follow-up :", task_text(follow))
    print("new task in context :", follow["id"] != remote_task["id"], follow["contextId"] == context)
    whole = rpc(parts_url, parts_id, "GetTask", {{"id": follow["id"]}})
    scoped = rpc(parts_url, parts_id, "GetTask", {{"id": follow["id"], "historyScope": "task"}})
    print("history entries :", {{"default context": len(whole.get("history", [])), "task": len(scoped.get("history", []))}})
except Exception:
    stop_servers()
    raise
'''),
    md("Each server allocates its own task. Reusing a contextId creates a thread with that id on the second server; the messages stay in that server's storage. A completed task id is not the input of the next turn. The legacy method message/send unwraps the task and writes the state in lowercase. GetTask with historyScope task keeps the requested task's history. We request the follow-up task here. This response filter does not limit the model's input history."),
    md("We add a request-spacing delay inside the coordinator because the servers have separate process-local model limiters. This keeps the combined model traffic within COURSE_RPS. Server failures raise instead of becoming a fabricated stock answer."),
], final='stop_servers()\nprint("servers stopped :", not servers)\nfinish_metrics("demo04")')


demo(5, "events-and-synchronisation", "Events and synchronisation", [
    section("a · streaming-subgraphs", "We stream a compiled parts subgraph and its parent. Namespaces identify the child, while updates contain only the values returned by each node."),
    code(r'''
class StreamState(TypedDict):
    part_no: str
    finding: dict
    answer: str


child = StateGraph(StreamState)
child.add_node("lookup", lambda s: {"finding": stock(s["part_no"])})
child.add_edge(START, "lookup")
child.add_edge("lookup", END)
parent = StateGraph(StreamState)
parent.add_node("parts", child.compile())
parent.add_node("report", lambda s: {"answer": llm.invoke("Write one stock sentence.\n" + json.dumps(s["finding"])).content})
parent.add_edge(START, "parts")
parent.add_edge("parts", "report")
parent.add_edge("report", END)
graph = parent.compile()
for part in graph.stream({"part_no": "CE-CF-02"}, stream_mode="updates", subgraphs=True, version="v2"):
    print("event :", part["type"], part["ns"], part["data"])
'''),
    md("We inspect experimental v3 subgraph projections on a deterministic parent to avoid repeating the model call. We consume each child handle inside the discovery loop before the parent advances."),
    code(r'''
projection_parent = StateGraph(StreamState)
projection_parent.add_node("parts", child.compile())
projection_parent.add_edge(START, "parts")
projection_parent.add_edge("parts", END)
run = projection_parent.compile().stream_events({"part_no": "CE-CF-02"}, version="v3")
for subrun in run.subgraphs:
    print("v3 path :", subrun.path)
    for value in subrun.values:
        print("v3 child value :", value)
    print("v3 child status :", subrun.status)
print("v3 output :", run.output)
'''),
    section("b · custom-events", "We publish lookup progress through get_stream_writer. A custom event is an observation for a consumer. Only the returned update changes graph state."),
    code(r'''
from langgraph.config import get_stream_writer


def lookup_with_events(state):
    writer = get_stream_writer()
    writer({"event": "lookup-started", "part_no": state["part_no"]})
    finding = stock(state["part_no"])
    writer({"event": "lookup-finished", "part_no": state["part_no"], "found": "error" not in finding})
    return {"finding": finding}


events = StateGraph(StreamState)
events.add_node("lookup", lookup_with_events)
events.add_edge(START, "lookup")
events.add_edge("lookup", END)
for part in events.compile().stream({"part_no": "CE-CF-02"}, stream_mode=["custom", "updates"], version="v2"):
    print("event :", part["type"], part["data"])
'''),
    section("c · broadcast-channel", "We publish an inventory snapshot once. Each parallel role reads the same broadcast field and returns its own observation through a reducer."),
    code(r'''
class Broadcast(TypedDict):
    broadcast: dict
    observations: Annotated[list[dict], operator.add]


def subscriber(role):
    def node(state):
        return {"observations": [{"role": role, "seen": state["broadcast"]}]}
    return node


broadcast = StateGraph(Broadcast)
broadcast.add_node("publish", lambda s: {"broadcast": {"version": "BW-7001-stock", "facts": stock()}})
for role in ["seller", "buyer"]:
    broadcast.add_node(role, subscriber(role))
    broadcast.add_edge("publish", role)
    broadcast.add_edge(role, END)
broadcast.add_edge(START, "publish")
result = broadcast.compile().invoke({"observations": []})
for observation in result["observations"]:
    print("broadcast read :", observation)
print("same snapshot :", result["observations"][0]["seen"] == result["observations"][1]["seen"])
'''),
    md("The channel lives in one graph run. A branch reads the snapshot published before it starts, and it does not see another branch's in-progress writes. A real stock action needs a current authorised check."),
    section("d · fan-in-and-barriers", "We compare an explicit join for fixed dependencies with a deferred collector for branches of unequal depth. The collector checks the required results before writing a final note."),
    code(r'''
class Joined(TypedDict):
    findings: Annotated[list[dict], operator.add]
    collected: list[str]


def collect(state):
    roles = sorted(item["role"] for item in state["findings"])
    if roles != ["manuals", "parts"]:
        raise ValueError("Required branches are incomplete.")
    return {"collected": roles}


def join_graph(deferred=False):
    b = StateGraph(Joined)
    b.add_node("parts", lambda s: {"findings": [{"role": "parts", "data": stock()}]})
    b.add_node("prepare_manuals", lambda s: {})
    b.add_node("manuals", lambda s: {"findings": [{"role": "manuals", "data": guidance()}]})
    b.add_node("collect", collect, defer=deferred)
    b.add_edge(START, "parts")
    b.add_edge(START, "prepare_manuals")
    b.add_edge("prepare_manuals", "manuals")
    if deferred:
        b.add_edge("parts", "collect")
        b.add_edge("manuals", "collect")
    else:
        b.add_edge(["parts", "manuals"], "collect")
    b.add_edge("collect", END)
    return b.compile()


for deferred in [False, True]:
    for part in join_graph(deferred).stream({"findings": []}, stream_mode="updates"):
        print("deferred :", deferred, "update :", part)
'''),
])


demo(6, "conflicts", "Conflicts", [
    section("a · conflicting-writes", "We give seller and buyer opposite proposals for the same stock. Two concurrent writes to an unreduced decision key raise InvalidUpdateError. Keeping both proposals makes the conflict inspectable."),
    code(r'''
from langgraph.errors import InvalidUpdateError


class DecisionState(TypedDict):
    decision: str


bad = StateGraph(DecisionState)
bad.add_node("seller", lambda s: {"decision": "sell CE-CF-02"})
bad.add_node("buyer", lambda s: {"decision": "retain CE-CF-02"})
for role in ["seller", "buyer"]:
    bad.add_edge(START, role)
    bad.add_edge(role, END)
try:
    bad.compile().invoke({"decision": ""})
except InvalidUpdateError as exc:
    print("conflict :", str(exc).splitlines()[0])


class Proposals(TypedDict):
    proposals: Annotated[list[dict], operator.add]


fixed = StateGraph(Proposals)
fixed.add_node("seller", lambda s: {"proposals": [{"role": "seller", "action": "sell"}]})
fixed.add_node("buyer", lambda s: {"proposals": [{"role": "buyer", "action": "retain"}]})
for role in ["seller", "buyer"]:
    fixed.add_edge(START, role)
    fixed.add_edge(role, END)
print("retained proposals :", fixed.compile().invoke({"proposals": []}))
'''),
    section("b · voting", "We collect independent votes about selling cooling-fan stock. The reserve is a made-up policy input, not a field in the inventory database. We retain the evidence and reasons alongside each vote."),
    code(r'''
from typing import Literal
from pydantic import BaseModel


class Vote(BaseModel):
    action: Literal["sell", "retain"]
    reason: str


class VoteState(TypedDict):
    facts: dict
    reserve: int
    votes: Annotated[list[dict], operator.add]


def voter(role):
    def node(state):
        vote = llm.with_structured_output(Vote).invoke(
            f"Assess the proposal from the {role} role. Policy: never reduce stock below reserve. "
            "Proposal: sell four CE-CF-02.\n" + json.dumps({"facts": state["facts"], "reserve": state["reserve"]}))
        return {"votes": [{"role": role, **vote.model_dump()}]}
    return node


voting = StateGraph(VoteState)
for role in ["inventory", "workshop", "procurement"]:
    voting.add_node(role, voter(role))
    voting.add_edge(START, role)
    voting.add_edge(role, END)
votes = voting.compile().invoke({"facts": FACTS, "reserve": 4, "votes": []})["votes"]
counts = {action: sum(v["action"] == action for v in votes) for action in ["sell", "retain"]}
for vote in sorted(votes, key=lambda v: v["role"]):
    print("vote :", vote)
print("counts :", counts)
print("majority :", max(counts, key=counts.get))
'''),
    section("c · judge-and-tie-break", "We supply a deliberately tied pair to make the tie rule visible. A model judge explains the proposals, while code applies the reserve invariant and a fixed retain-on-tie rule."),
    code(r'''
tied = [{"role": "seller", "action": "sell", "reason": "Release storage."},
        {"role": "buyer", "action": "retain", "reason": "Keep workshop reserve."}]
judge = llm.with_structured_output(Vote).invoke(
    "Judge these proposals against the evidence and the reserve. The proposal sells four units.\n"
    + json.dumps({"facts": FACTS, "reserve": 4, "proposals": tied}))


def resolve(votes, available, quantity, reserve):
    counts = {action: sum(v["action"] == action for v in votes) for action in ["sell", "retain"]}
    chosen = "sell" if counts["sell"] > counts["retain"] else "retain"
    if chosen == "sell" and available - quantity < reserve:
        return "retain", "reserve invariant"
    return chosen, "retain on tie" if counts["sell"] == counts["retain"] else "majority"


print("judge :", judge.model_dump())
print("tie rule :", resolve(tied, FACTS["stock"], 2, 4))
print("policy override :", resolve([tied[0], tied[0]], FACTS["stock"], 4, 4))
'''),
    md("Votes are proposals. They do not authorise a sale. Shared prompts and evidence can produce correlated mistakes. The judge's reason stays visible, and code rejects a reserve violation even when the majority favours it."),
])


demo(7, "buyer-and-seller", "Buyer and seller", [
    section("a · the-conflict", "We adapt the seller and buyer from Yair's crew to Veenhaven Bus. Both serve one owner with competing objectives. We use a made-up reserve and record proposals without changing the service database."),
    code(r'''
from pydantic import BaseModel, Field


class Proposal(BaseModel):
    quantity: int = Field(ge=0, le=6)
    reason: str


class FleetState(TypedDict):
    facts: dict
    reserve: int
    proposals: Annotated[list[dict], operator.add]
    settlement: dict


def propose(role):
    goal = {"seller": "Propose a quantity to sell to reduce stored surplus.",
            "buyer": "Propose a quantity to keep for workshop continuity."}[role]
    def node(state):
        proposal = llm.with_structured_output(Proposal).invoke(goal + " Give a reason. This is a proposal only.\n"
            + json.dumps({"facts": state["facts"], "reserve": state["reserve"]}))
        return {"proposals": [{"role": role, **proposal.model_dump()}]}
    return node


def settle(state):
    proposals = {p["role"]: p for p in state["proposals"]}
    available = state["facts"]["stock"]
    retained = max(state["reserve"], min(available, proposals["buyer"]["quantity"]))
    sale = min(proposals["seller"]["quantity"], max(0, available - retained))
    return {"settlement": {"sell": sale, "retain": available - sale, "external_action": False}}


fleet = StateGraph(FleetState)
for role in ["seller", "buyer"]:
    fleet.add_node(role, propose(role))
    fleet.add_edge(START, role)
fleet.add_node("settle", settle)
fleet.add_edge(["seller", "buyer"], "settle")
fleet.add_edge("settle", END)
result = fleet.compile().invoke({"facts": FACTS, "reserve": 4, "proposals": []})
print("facts :", FACTS)
for proposal in sorted(result["proposals"], key=lambda p: p["role"]):
    print("proposal :", proposal)
print("settlement :", result["settlement"])
'''),
    section("b · least-privilege-per-agent", "We expose separate tools and use trusted runtime context to select a role's credential scope. The credential labels below are synthetic. An enforcement function checks the scope even if a caller requests the other role's operation."),
    code(r'''
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool


@dataclass(frozen=True)
class Principal:
    role: str
    credential_scope: str


def authorise(principal, operation):
    allowed = {"seller": ("sales-draft-only", "draft-sale"),
               "buyer": ("procurement-draft-only", "draft-purchase")}
    if allowed.get(principal.role) != (principal.credential_scope, operation):
        raise PermissionError("Operation outside this principal's scope.")


@tool
def draft_sale(quantity: int, runtime: ToolRuntime[Principal]) -> str:
    """Draft a CE-CF-02 sale proposal. No external action."""
    authorise(runtime.context, "draft-sale")
    return json.dumps({"principal": runtime.context.role, "operation": "draft-sale", "quantity": quantity,
                       "part_no": "CE-CF-02", "external_action": False})


@tool
def draft_purchase(quantity: int, runtime: ToolRuntime[Principal]) -> str:
    """Draft a CE-DA-03 purchase proposal. No external action."""
    authorise(runtime.context, "draft-purchase")
    return json.dumps({"principal": runtime.context.role, "operation": "draft-purchase", "quantity": quantity,
                       "part_no": "CE-DA-03", "external_action": False})


seller = create_agent(llm, tools=[draft_sale], context_schema=Principal,
    system_prompt="Draft the requested sale with draft_sale. Do not claim a sale completed.")
buyer = create_agent(llm, tools=[draft_purchase], context_schema=Principal,
    system_prompt="Draft the requested purchase with draft_purchase. Do not claim an order completed.")
for agent, principal, task in [
    (seller, Principal("seller", "sales-draft-only"), "Draft a sale of two CE-CF-02 cooling fans."),
    (buyer, Principal("buyer", "procurement-draft-only"), "Draft a purchase of one CE-DA-03 door actuator."),
]:
    output = agent.invoke({"messages": [HumanMessage(task)]}, LIMIT, context=principal)
    print("principal :", principal)
    print("tool results :", [(m.name, m.content) for m in output["messages"] if isinstance(m, ToolMessage)])
    print("answer :", output["messages"][-1].content)
print("seller schema :", draft_sale.args)
print("buyer schema :", draft_purchase.args)
try:
    authorise(Principal("seller", "sales-draft-only"), "draft-purchase")
except PermissionError as exc:
    print("denied :", str(exc))
'''),
    md("We simulate role-scoped credentials and enforce operations in code. Production isolation also needs separate service identities or browser profiles and downstream authorisation. A prompt, hidden tool schema or approval gate alone cannot contain every shared credential."),
])

print("module 06 notebooks written")
