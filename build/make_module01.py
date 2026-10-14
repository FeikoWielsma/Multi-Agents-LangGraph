"""Build the demo notebooks for module 01, Introduction to LangGraph.

    uv run python build/make_module01.py
    COURSE_RPS=0.08 uv run python build/run_notebook.py notebooks/01-intro-langgraph/demo01-one-agent-limits.ipynb

demo02 ports the first graph of ARI510 demo20 ; demo04 ports the idea of ARI510
demo01 and exercise01. demo01 and demo03 are new.
"""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb import code, md, section, write_demo

MODULE = "01-intro-langgraph"


def src(*parts):
    return "\n\n".join(textwrap.dedent(p).strip("\n") for p in parts)


DATA = """
import csv
import re
import sqlite3
from pathlib import Path

from langchain.tools import tool

db = sqlite3.connect(data("demo-world/service.db"), check_same_thread=False)
db.row_factory = sqlite3.Row

SECTIONS = []
for path in sorted(Path(data_folder("demo-world/manuals")).glob("*.md")):
    title, *parts = path.read_text(encoding="utf-8").split("\\n## ")
    SECTIONS += [f"{title.splitlines()[0]}\\n## {part}" for part in parts]
TICKETS = [", ".join(f"{k}={v}" for k, v in t.items())
           for t in csv.DictReader(open(data("demo-world/tickets.csv"), encoding="utf-8"))]


def rows(sql, *args):
    return [dict(r) for r in db.execute(sql, args)]


def words(text):
    return set(re.findall(r"[a-z0-9-]{3,}", text.lower()))


def best(texts, query, k):
    q = words(query)
    return sorted(texts, key=lambda t: -len(q & words(t)))[:k]


print("sections:", len(SECTIONS), " tickets:", len(TICKETS),
      " buses:", len(rows("SELECT * FROM buses")), " parts:", len(rows("SELECT * FROM parts")))
"""

TOOLS = """
@tool
def bus_info(fleet_no: str) -> str:
    \"\"\"Model, depot and firmware of one bus, by fleet number such as CE12-2021-0117.\"\"\"
    return str(rows("SELECT * FROM buses WHERE fleet_no = ?", fleet_no.strip().upper()) or "no such bus")


@tool
def part_stock(part_no: str) -> str:
    \"\"\"Name, units in stock, price and depot of one spare part, by part number such as CE-CF-02.\"\"\"
    return str(rows("SELECT * FROM parts WHERE part_no = ?", part_no.strip().upper()) or "no such part")


@tool
def parts_for_model(model: str) -> str:
    \"\"\"Every spare part for a bus model such as CE-12, with units in stock.\"\"\"
    return str(rows("SELECT * FROM parts WHERE model = ?", model.strip().upper()))


@tool
def search_manuals(query: str) -> str:
    \"\"\"Search the service manuals and bulletins. Returns the three best matching sections.\"\"\"
    return "\\n\\n---\\n\\n".join(best(SECTIONS, query, 3))
"""

MORE_TOOLS = """
@tool
def mechanics_for_model(model: str) -> str:
    \"\"\"Mechanics certified for a bus model such as CD-12, with their region.\"\"\"
    return str(rows("SELECT name, region, certified_models FROM mechanics WHERE certified_models LIKE ?",
                    f"%{model.strip().upper()}%"))


@tool
def depot_info(depot: str) -> str:
    \"\"\"Id, city and service contract of a depot, by name, city or id.\"\"\"
    d = depot.strip()
    return str(rows("SELECT * FROM depots WHERE depot_id = ? OR name LIKE ? OR city LIKE ?",
                    d.upper(), f"%{d}%", f"%{d}%"))


@tool
def work_orders_for_bus(fleet_no: str) -> str:
    \"\"\"Work orders for one bus : status, error code, summary and mechanic.\"\"\"
    return str(rows("SELECT * FROM work_orders WHERE fleet_no = ?", fleet_no.strip().upper()) or "none")


@tool
def search_tickets(query: str) -> str:
    \"\"\"Search past repair tickets by fleet number, error code or symptom. Returns the five best matches.\"\"\"
    return "\\n".join(best(TICKETS, query, 5))
"""

METER = """
from langchain_core.callbacks import BaseCallbackHandler


class Meter(BaseCallbackHandler):
    def __init__(self):
        self.calls = self.input = self.output = 0

    def on_llm_end(self, response, **kwargs):
        usage = response.generations[0][0].message.usage_metadata or {}
        self.calls += 1
        self.input += usage.get("input_tokens", 0)
        self.output += usage.get("output_tokens", 0)

    def __str__(self):
        return f"{self.calls} calls, {self.input:,} input tokens, {self.output:,} output tokens"


def correct(answer, expected):
    text = answer.lower()
    return all(any(alt in text for alt in item.split("|")) for item in expected)
"""

DIAGNOSE = """
def diagnose(fleet_no: str, error_code: str) -> dict:
    bus = rows("SELECT model, depot_id FROM buses WHERE fleet_no = ?", fleet_no)[0]
    manual = next(s for s in SECTIONS if s.startswith(f"# {bus['model']} error codes"))
    row = next(line for line in manual.splitlines() if line.startswith(f"| {error_code} |"))
    meaning, action = [cell.strip() for cell in row.split("|")[2:4]]
    part = next((p for p in rows("SELECT * FROM parts WHERE model = ?", bus["model"])
                 if p["name"] in action), None)
    return {"model": bus["model"], "meaning": meaning, "action": action, "part": part}
"""


# ---------------------------------------------------------------- demo01
write_demo(MODULE, "demo01-one-agent-limits", [
    md("""
    # Demo 01 : One agent and a growing tool list

    Run the cells in order and watch. There is nothing to write.
    """),
    md("""
    We load the Veenhaven Bus database, service manuals and past repair tickets.
    The database contains depots, mechanics, buses, parts and work orders.
    """),
    code(DATA),
    md("""
    We define eight tools for service desk lookups. Each is a small function over
    the data ; the model reads only the name, the arguments and the docstring.
    """),
    code(src(TOOLS, MORE_TOOLS, """
    CORE = [bus_info, part_stock, parts_for_model, mechanics_for_model, depot_info,
            work_orders_for_bus, search_manuals, search_tickets]
    print("core tools:", [t.name for t in CORE])
    """)),
    md("""
    A real company has many more systems : timetables, rosters, payroll,
    procurement. When one agent serves the whole company, their tools land in the
    same list. We add 52 such tools. None of them helps with a repair question,
    and each answers that it has no records.
    """),
    code("""
    from langchain_core.tools import StructuredTool
    from pydantic import create_model

    OTHER = [
        ("timetable_for_route", "Departure times for a bus route on a given day.", "route"),
        ("route_detours", "Current detours and closed stops on a route.", "route"),
        ("stop_info", "Location, shelter and accessibility of a bus stop.", "stop"),
        ("passenger_counts", "Boardings per trip on a route last week.", "route"),
        ("fare_for_journey", "Adult fare between two stops.", "journey"),
        ("ticket_machine_status", "Faults reported by the ticket machine on board a bus.", "fleet_no"),
        ("driver_roster", "Which driver is rostered on which duty on a date.", "date"),
        ("driver_leave", "Approved leave for a driver.", "driver"),
        ("driver_training", "Training records and licence expiry of a driver.", "driver"),
        ("payroll_period", "Payroll status for a pay period.", "period"),
        ("fuel_card_spend", "Fuel card transactions for a depot this month.", "depot"),
        ("charger_availability", "Free charging points at a depot right now.", "depot"),
        ("energy_price", "Contracted electricity price for a depot.", "depot"),
        ("cleaning_schedule", "Interior cleaning schedule for a depot.", "depot"),
        ("lost_property", "Items handed in on buses, by description.", "description"),
        ("passenger_complaints", "Complaints from passengers, by route or topic.", "topic"),
        ("cctv_request", "Status of a request for on-board camera footage.", "request_id"),
        ("insurance_claims", "Open insurance claims after collisions.", "claim_id"),
        ("accident_reports", "Accident reports filed by drivers.", "report_id"),
        ("supplier_contracts", "Framework contracts with a supplier.", "supplier"),
        ("invoice_status", "Payment status of a supplier invoice.", "invoice_no"),
        ("purchase_orders", "Purchase orders raised by procurement.", "po_number"),
        ("tyre_inspections", "Tyre tread readings from the last depot inspection.", "depot"),
        ("bus_washing_log", "When a bus last went through the wash.", "fleet_no"),
        ("advertising_contracts", "Advertising wraps booked on the fleet.", "advertiser"),
        ("school_contracts", "Contracted school trips for a term.", "school"),
        ("event_services", "Extra buses planned for a public event.", "event"),
        ("staff_directory", "Phone number and role of a staff member.", "name"),
        ("it_helpdesk_tickets", "Office IT helpdesk tickets.", "ticket_id"),
        ("meeting_rooms", "Free meeting rooms at head office.", "date"),
        ("weather_forecast", "Weather forecast for a city.", "city"),
        ("road_works", "Planned road works affecting bus routes.", "city"),
        ("punctuality_reports", "Punctuality figures reported to the transport authority.", "month"),
        ("emissions_report", "CO2 emissions of a depot for a month.", "depot"),
        ("depot_access_badges", "Access badges issued for a depot.", "depot"),
        ("parking_permits", "Staff parking permits at a depot.", "depot"),
        ("uniform_orders", "Uniform orders for drivers.", "driver"),
        ("safety_incidents", "Workplace safety incidents in depots.", "depot"),
        ("vacancies", "Open job vacancies.", "role"),
        ("helpline_calls", "Calls to the passenger helpline.", "topic"),
        ("social_media_mentions", "Mentions of the company on social media.", "topic"),
        ("department_budget", "Budget and spend for a department.", "department"),
        ("board_decisions", "Decisions of the management board.", "topic"),
        ("tender_documents", "Documents of an open tender.", "tender"),
        ("bus_position", "GPS position of a bus right now.", "fleet_no"),
        ("delay_alerts", "Live delay alerts on a route.", "route"),
        ("signal_priority", "Bus priority settings at a junction.", "junction"),
        ("bike_rack_bookings", "Bike rack bookings on intercity routes.", "route"),
        ("assistance_requests", "Assistance requests from passengers with a disability.", "request_id"),
        ("survey_results", "Passenger satisfaction survey results for a route.", "route"),
        ("holiday_timetables", "Timetable changes for a public holiday.", "holiday"),
        ("driver_breaks", "Scheduled break locations for drivers on a route.", "route"),
    ]


    def other_system(name, description, arg):
        return StructuredTool.from_function(
            func=lambda **kw: f"no records for {kw[arg]}", name=name, description=description,
            args_schema=create_model(name, **{arg: (str, ...)}))


    OTHER_TOOLS = [other_system(*spec) for spec in OTHER]
    print("other tools:", len(OTHER_TOOLS))
    """),
    md("""
    We use six questions over the desk's data, each with the facts a correct
    answer contains. `Meter` counts model calls and tokens through a callback,
    and `correct` checks the facts. A `|` separates accepted alternatives.
    """),
    code(src(METER, """

    QUESTIONS = [
        ("Is part CE-DA-03 in stock?", ["0|out of stock|not in stock|none"]),
        ("What firmware runs on bus CE12-2023-0342?", ["5.1"]),
        ("Which mechanics are certified for the CD-12?", ["nora dalen", "ivo rietman"]),
        ("Bus CE12-2021-0117 shows F-CE-110. What part do I need and is it in stock?",
         ["ce-cf-02|cooling fan", "6|six"]),
        ("What fixed F-RR-120 on earlier tickets?", ["rr-bp-03|auxiliary battery pack"]),
        ("Which mechanic in region Zuid can fix F-CD-101 at Broekdam Depot?", ["nora dalen"]),
    ]
    """)),
    section("a · one-agent-limits", """
    We build one agent with `n` tools : the eight core tools plus the
    first `n - 8` others, shuffled so the core tools are not all at the front.
    It asks every question once and prints a line per question. A detour is a
    call to one of the other systems' tools.
    """),
    code("""
    import random

    from langchain.agents import create_agent

    PROMPT = "You are the service desk assistant for Veenhaven Bus. Answer from the tools only. Be brief."
    CORE_NAMES = {t.name for t in CORE}
    results = []


    def measure(n):
        tools = CORE + OTHER_TOOLS[:n - len(CORE)]
        random.Random(n).shuffle(tools)
        agent = create_agent(llm, tools=tools, system_prompt=PROMPT)
        row = {"tools": n, "correct": 0, "calls": 0, "input": 0, "output": 0, "detours": 0}
        for question, expected in QUESTIONS:
            meter = Meter()
            messages = agent.invoke({"messages": [{"role": "user", "content": question}]},
                                    {"callbacks": [meter]})["messages"]
            used = [m.name for m in messages if m.type == "tool"]
            ok = correct(messages[-1].content, expected)
            detours = sum(name not in CORE_NAMES for name in used)
            for key, value in [("correct", ok), ("calls", meter.calls), ("input", meter.input),
                               ("output", meter.output), ("detours", detours)]:
                row[key] += value
            print(f"{'ok' if ok else 'WRONG':5} {meter.calls} calls {meter.input:>7,} in  {used}")
            print("answer:", messages[-1].content)
        results.append(row)
        print(f"{n} tools : {row['correct']}/{len(QUESTIONS)} correct, {row['calls']} calls, "
              f"{row['input']:,} input tokens, {row['detours']} detours")
    """),
    md("""
    First the eight core tools alone. This is the baseline : every tool is
    relevant, and the tool list is short.
    """),
    code("measure(8)"),
    md("""
    Twenty tools : twelve of them belong to other systems.
    """),
    code("measure(20)"),
    md("""
    Forty tools.
    """),
    code("measure(40)"),
    md("""
    We reach sixty tools : eight repair tools and 52 distractors.
    """),
    code("measure(60)"),
    md("""
    We compare the four runs, including average input tokens per call. The
    model receives the full tool list on every call, including unused tools.
    """),
    code("""
    print(f"{'tools':>5} {'correct':>8} {'calls':>6} {'input':>8} {'per call':>9} {'output':>7} {'detours':>8}")
    for r in results:
        print(f"{r['tools']:>5} {r['correct']:>6}/{len(QUESTIONS)} {r['calls']:>6} {r['input']:>8,} "
              f"{r['input'] // r['calls']:>9,} {r['output']:>7} {r['detours']:>8}")
    """),
    md("""
    We compare correctness, calls and tokens before splitting the agent. More
    tool descriptions add input context, but correctness need not decrease.
    One run per question is a small sample ; the fact check uses text matches,
    so we also read each answer for contradictions and unsupported claims.
    """),
    md("""
    We read the saved run of 14 October 2026 as a non-monotonic result : one
    expected fact is missing at 40 tools and returns at 60. No distractor tool
    is called. At 20 and 40 tools, the ticket answer also mislabels RR-BP-03 as
    a door controller ; its accepted part number does not catch that error.
    """),
    md("""
    ## Things to try

    Optional.

    - Rename three of the other tools so they overlap with the core ones, for
      example `fleet_register` or `warehouse_stock`, and measure again
    - Run `measure(60)` with `make_llm(model="xiaomi/mimo-v2.6-pro")` in place
      of `llm`
    - Shorten the docstring of `part_stock` to two words and see which
      questions fail
    """),
])


# ---------------------------------------------------------------- demo02
write_demo(MODULE, "demo02-first-look", [
    md("""
    # Demo 02 : A first look at LangGraph

    Run the cells in order and watch. There is nothing to write.
    """),
    code(DATA),
    section("a · first-graph", """
    A graph of three plain functions, with no model anywhere. A driver's report
    names a bus and an error code ; the graph looks up the bus, reads the first
    action from the manual, and sends the bus to the workshop or fixes it on
    site.
    """),
    code("""
    from typing import Literal, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Report(TypedDict, total=False):
        fleet_no: str
        error_code: str
        model: str
        action: str
        where: str


    def look_up_bus(state: Report) -> dict:
        return {"model": rows("SELECT model FROM buses WHERE fleet_no = ?", state["fleet_no"])[0]["model"]}


    def read_manual(state: Report) -> dict:
        manual = next(s for s in SECTIONS if s.startswith(f"# {state['model']} error codes"))
        row = next(line for line in manual.splitlines() if line.startswith(f"| {state['error_code']} |"))
        return {"action": row.split("|")[3].strip()}


    def route(state: Report) -> Literal["workshop", "on_site"]:
        return "workshop" if "workshop" in state["action"] else "on_site"


    builder = StateGraph(Report)
    builder.add_node("look_up_bus", look_up_bus)
    builder.add_node("read_manual", read_manual)
    builder.add_node("workshop", lambda state: {"where": "workshop"})
    builder.add_node("on_site", lambda state: {"where": "on site"})
    builder.add_edge(START, "look_up_bus")
    builder.add_edge("look_up_bus", "read_manual")
    builder.add_conditional_edges("read_manual", route)
    builder.add_edge("workshop", END)
    builder.add_edge("on_site", END)
    graph = builder.compile()
    print(graph.get_graph().draw_mermaid())
    """),
    md("""
    The state is a dictionary that every node reads. Each node returns only the
    keys it changes, and LangGraph merges them. The conditional edge reads the
    state to pick the next node.
    """),
    code("""
    for report in [{"fleet_no": "CD12-2024-0098", "error_code": "F-CD-202"},
                   {"fleet_no": "CE12-2021-0117", "error_code": "F-CE-305"}]:
        result = graph.invoke(report)
        print(f"{result['fleet_no']} {result['error_code']} -> {result['where']:8} {result['action']}")
    """),
    md("""
    `stream` shows the same run one node at a time, with the update each node
    returned.
    """),
    code("""
    for step in graph.stream({"fleet_no": "MM09-2025-2350", "error_code": "F-MM-210"}):
        print(step)
    """),
    section("b · first-multi-agent", """
    We put two agents behind a supervisor, each with its own tools and prompt.
    The supervisor calls them as tools and reads their returned answers.
    """),
    code(src(TOOLS, METER)),
    code("""
    from langchain.agents import create_agent

    parts_agent = create_agent(llm, tools=[bus_info, part_stock, parts_for_model],
                               system_prompt="You answer questions about spare parts and stock. "
                                             "Use bus_info to resolve a fleet number to a model. "
                                             "Use parts_for_model to find a part number from a component name. "
                                             "Fault codes are not part numbers. Answer from the tools. Be brief.")
    manuals_agent = create_agent(llm, tools=[search_manuals],
                                 system_prompt="You answer questions from the service manuals. Be brief.")


    @tool
    def ask_parts_agent(question: str) -> str:
        \"\"\"Ask the parts agent about part numbers and stock.\"\"\"
        reply = parts_agent.invoke({"messages": [{"role": "user", "content": question}]})
        return reply["messages"][-1].content


    @tool
    def ask_manuals_agent(question: str) -> str:
        \"\"\"Ask the manuals agent about error codes, procedures and maintenance.\"\"\"
        reply = manuals_agent.invoke({"messages": [{"role": "user", "content": question}]})
        return reply["messages"][-1].content


    supervisor = create_agent(llm, tools=[ask_parts_agent, ask_manuals_agent],
                              system_prompt="You run the Veenhaven Bus service desk. Ask your agents, "
                                            "then answer the mechanic briefly.")
    """),
    md("""
    One question that needs both agents. The model decides how to split it, so
    the order and wording of the delegated questions vary between runs.
    """),
    code("""
    question = "Bus CE12-2021-0117 shows F-CE-110. What part do I need and is it in stock?"
    meter = Meter()
    result = supervisor.invoke({"messages": [{"role": "user", "content": question}]}, {"callbacks": [meter]})

    for m in result["messages"]:
        for call in getattr(m, "tool_calls", []):
            print(f"{call['name']:18} Q: {call['args']['question']}")
        if m.type == "tool":
            print(f"{m.name:18} A: {m.content[:200]}\\n")
    print("final:", result["messages"][-1].content)
    print("correct:", correct(result["messages"][-1].content, ["ce-cf-02|cooling fan", "6|six"]))
    print(meter)
    """),
    md("""
    We inspect the delegated questions to see what each agent received. Each
    specialist starts a fresh conversation ; the supervisor can include
    earlier findings in a later task. The meter includes nested model calls.
    """),
    md("""
    ## Things to try

    Optional.

    - Add a branch to the first graph for codes that are not in the manual
    - Ask the supervisor a question only one agent can answer, and count the calls
    - Print `parts_agent.get_graph().draw_mermaid()` : an agent is a graph too
    """),
])


# ---------------------------------------------------------------- demo03
write_demo(MODULE, "demo03-three-levels", [
    md("""
    # Demo 03 : One task at three levels

    Run the cells in order and watch. There is nothing to write.
    """),
    code(DATA),
    md("""
    Four tools over the data, a meter for calls and tokens, and the task with
    the facts a correct answer contains.
    """),
    code(src(TOOLS, METER, """
    TASK = "Bus MM09-2025-2350 shows F-MM-210. Which part does it need, and is it in stock?"
    EXPECTED = ["mm-bt-02|auxiliary battery", "0|out of stock|not in stock|none"]
    PROMPT = "You are the service desk assistant for Veenhaven Bus. Answer from the tools only. Be brief."
    TOOL_LIST = [bus_info, part_stock, parts_for_model, search_manuals]
    results = {}
    """)),
    section("a · graph-by-hand", """
    The graph fixes the steps. The model extracts the fleet number and the error
    code, plain Python looks up the bus, the manual and the part, and the model
    writes the answer.
    """),
    code(src(DIAGNOSE, """

    from typing import TypedDict

    from langgraph.graph import END, START, StateGraph
    from pydantic import BaseModel


    class Report(BaseModel):
        fleet_no: str
        error_code: str


    class Desk(TypedDict, total=False):
        question: str
        fleet_no: str
        error_code: str
        facts: dict
        answer: str


    def extract(state: Desk) -> dict:
        report = llm.with_structured_output(Report).invoke(
            f"Extract the fleet number and the error code.\\n\\n{state['question']}")
        return {"fleet_no": report.fleet_no, "error_code": report.error_code}


    def look_up(state: Desk) -> dict:
        return {"facts": diagnose(state["fleet_no"], state["error_code"])}


    def answer(state: Desk) -> dict:
        reply = llm.invoke(f"Answer the question from the facts. Be brief.\\n\\n"
                           f"Question : {state['question']}\\nFacts : {state['facts']}")
        return {"answer": reply.content}


    builder = StateGraph(Desk)
    builder.add_node("extract", extract)
    builder.add_node("look_up", look_up)
    builder.add_node("answer", answer)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "look_up")
    builder.add_edge("look_up", "answer")
    builder.add_edge("answer", END)
    graph = builder.compile()

    meter = Meter()
    result = graph.invoke({"question": TASK}, {"callbacks": [meter]})
    print("facts :", result["facts"])
    print("answer:", result["answer"])
    print(meter)
    results["graph by hand"] = (meter, correct(result["answer"], EXPECTED))
    """)),
    section("b · create-agent", """
    `create_agent` builds the tool-calling loop for us. The model decides which
    tools to call and in what order.
    """),
    code("""
    from langchain.agents import create_agent

    agent = create_agent(llm, tools=TOOL_LIST, system_prompt=PROMPT)
    meter = Meter()
    messages = agent.invoke({"messages": [{"role": "user", "content": TASK}]}, {"callbacks": [meter]})["messages"]
    print("tools :", [m.name for m in messages if m.type == "tool"])
    print("answer:", messages[-1].content)
    print(meter)
    results["create_agent"] = (meter, correct(messages[-1].content, EXPECTED))
    """),
    md("""
    We inspect the compiled graph. Its model and tool nodes form the agent loop.
    """),
    code("""
    print(list(agent.get_graph().nodes))
    """),
    section("c · deep-agent", """
    We pass the same four tools and prompt to `create_deep_agent`. Version
    0.7.24 adds filesystem tools, a general-purpose subagent and summarisation.
    Planning with a todo list requires additional middleware.
    """),
    code("""
    from deepagents import create_deep_agent

    deep = create_deep_agent(model=llm, tools=TOOL_LIST, system_prompt=PROMPT)
    meter = Meter()
    messages = deep.invoke({"messages": [{"role": "user", "content": TASK}]}, {"callbacks": [meter]})["messages"]
    print("tools :", [m.name for m in messages if m.type == "tool"])
    print("answer:", messages[-1].content)
    print(meter)
    results["create_deep_agent"] = (meter, correct(messages[-1].content, EXPECTED))
    print(list(deep.get_graph().nodes))
    """),
    md("""
    We compare the three runs on correctness, calls and tokens. The deep agent
    receives additional tool descriptions and middleware instructions. This
    short lookup measures their overhead ; it does not measure their value on
    a longer task.
    """),
    code("""
    print(f"{'level':18} {'correct':>7} {'calls':>6} {'input':>8} {'output':>7}")
    for name, (m, ok) in results.items():
        print(f"{name:18} {str(ok):>7} {m.calls:>6} {m.input:>8,} {m.output:>7}")
    """),
    md("""
    ## Things to try

    Optional.

    - Ask the three a question the graph was not built for, such as which
      mechanics are certified for the MM-09
    - Give the deep agent a task with five buses and inspect its tool calls
    """),
])


# ---------------------------------------------------------------- demo04
write_demo(MODULE, "demo04-workflow-or-agent", [
    md("""
    # Demo 04 : A workflow or an agent

    Run the cells in order and watch. There is nothing to write.
    """),
    code(DATA),
    md("""
    Four tools over the data, a meter for calls and tokens, `diagnose`, which
    looks up the manual and the part in plain Python, and four reports.
    """),
    code(src(TOOLS, METER, DIAGNOSE, """
    REPORTS = [
        "CE12-2021-0117 : F-CE-110 on the afternoon route.",
        "CD12-2024-0098 shows F-CD-202 again, pressure low.",
        "Bus RR14-2022-0210, error F-RR-120 at the last stop.",
        "The ramp on MM09-2025-2311 will not come out. No code on the display.",
    ]
    NOTE = ("Write a three-line note for the mechanic : the likely cause, the first action, "
            "and the part with its stock.")
    """)),
    section("a · workflow-or-agent", """
    We fix the workflow's path in code. A regular expression finds the fleet
    number and the error code, `diagnose` reads the manual and the parts table,
    and the model writes the note : one model call per report. A report without a
    code goes to second line.
    """),
    code("""
    from typing import Literal, TypedDict

    from langgraph.graph import END, START, StateGraph


    class Ticket(TypedDict, total=False):
        report: str
        fleet_no: str | None
        error_code: str | None
        facts: dict
        note: str


    def parse(state: Ticket) -> dict:
        fleet = re.search(r"[A-Z]{2}\\d{2}-\\d{4}-\\d{4}", state["report"])
        error = re.search(r"F-[A-Z]{2}-\\d{3}", state["report"])
        return {"fleet_no": fleet and fleet.group(), "error_code": error and error.group()}


    def route(state: Ticket) -> Literal["look_up", "escalate"]:
        return "look_up" if state["fleet_no"] and state["error_code"] else "escalate"


    def look_up(state: Ticket) -> dict:
        return {"facts": diagnose(state["fleet_no"], state["error_code"])}


    def write_note(state: Ticket) -> dict:
        return {"note": llm.invoke(f"{NOTE}\\n\\nReport : {state['report']}\\nFacts : {state['facts']}").content}


    builder = StateGraph(Ticket)
    builder.add_node("parse", parse)
    builder.add_node("look_up", look_up)
    builder.add_node("write_note", write_note)
    builder.add_node("escalate", lambda state: {"note": "No fleet number or error code : sent to second line."})
    builder.add_edge(START, "parse")
    builder.add_conditional_edges("parse", route)
    builder.add_edge("look_up", "write_note")
    builder.add_edge("write_note", END)
    builder.add_edge("escalate", END)
    workflow = builder.compile()
    print(workflow.get_graph().draw_mermaid())
    """),
    code("""
    runs = {}
    for report in REPORTS:
        meter = Meter()
        note = workflow.invoke({"report": report}, {"callbacks": [meter]})["note"]
        runs[report] = {"workflow": meter}
        print(f"> {report}\\n{note}\\n[{meter}]\\n")
    """),
    md("""
    The agent gets the four tools and the same instruction. It decides what to
    look up, and how often.
    """),
    code("""
    from langchain.agents import create_agent

    agent = create_agent(llm, tools=[bus_info, part_stock, parts_for_model, search_manuals],
                         system_prompt=f"You are the Veenhaven Bus service desk. {NOTE} Use the tools.")

    for report in REPORTS:
        meter = Meter()
        messages = agent.invoke({"messages": [{"role": "user", "content": report}]}, {"callbacks": [meter]})["messages"]
        runs[report]["agent"] = meter
        print(f"> {report}\\ntools: {[m.name for m in messages if m.type == 'tool']}")
        print(f"{messages[-1].content}\\n[{meter}]\\n")
    """),
    md("""
    On the three reports with a code, both usually reach the same part ; the
    workflow does it with one model call. On the ramp report the workflow
    escalates, because its path has no step for a report without a code. The
    agent can search the manuals for the symptom instead. Whether it finds the
    right procedure varies between runs, and the cost is several calls.
    """),
    code("""
    print(f"{'report':40} {'workflow':>16} {'agent':>16}")
    for report, r in runs.items():
        w, a = r["workflow"], r["agent"]
        print(f"{report[:40]:40} {w.calls:>3} calls {w.input:>6,} {a.calls:>3} calls {a.input:>6,}")
    """),
    md("""
    ## Things to try

    Optional.

    - Add a node to the workflow that calls the agent for reports without a
      code : a workflow with one agentic step
    - Write a report with a typo in the error code and run both
    """),
])
