"""Build the notebooks for module 10, Real-World Applications.

    uv run python build/make_module10.py
    COURSE_RPS=0.03 uv run python build/run_notebook.py notebooks/10-real-world-applications/*.ipynb

The examples use the Veenhaven Bus demo data. `demo05 · firstmate` is a
trainer demonstration and has no notebook.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb import code, md, section, write_demo

MODULE = "10-real-world-applications"
TARGETS = sys.argv[1:]


def should_write(slug):
    return not TARGETS or slug in TARGETS or any(slug.startswith(t) for t in TARGETS)


if should_write("demo01-research-agent"):
    write_demo(MODULE, "demo01-research-agent", [
        md("""
        # Demo 01 : A research agent

        We use local manuals and service tickets to answer a question that spans both sources. Run the cells in order and watch. There is nothing to write.
        """),
        section("a · research-agent", "We keep the corpus small and search only local files. The graph separates planning, parallel research and report writing, following the shape of `open_deep_research` without web access."),
        code("""
        import csv
        from pathlib import Path

        from langchain.messages import HumanMessage, SystemMessage
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Send
        from typing_extensions import TypedDict
        import operator
        from typing import Annotated
        from pydantic import BaseModel

        manuals_dir = Path(data_folder("demo-world/manuals"))
        manuals = [(p.name, p.read_text(encoding="utf-8")) for p in sorted(manuals_dir.glob("*.md"))]
        with open(data("demo-world/tickets.csv"), encoding="utf-8") as f:
            tickets = list(csv.DictReader(f))

        def search(query, limit=2):
            words = set(query.lower().split())
            ranked = sorted(manuals, key=lambda row: sum(row[1].lower().count(w) for w in words), reverse=True)
            return [(name, body) for name, body in ranked[:limit]]

        QUESTION = "Which repeated fault took the most recorded mechanic hours, and what local procedure applies?"
        hours = {}
        for row in tickets:
            key = (row["error_code"], row["symptom"])
            hours[key] = hours.get(key, 0) + float(row["hours"])
        ticket_facts = sorted(hours.items(), key=lambda item: item[1], reverse=True)[:4]
        print("manual files:", len(manuals), "ticket rows:", len(tickets))
        print("top ticket groups:", ticket_facts[:2])
        """),
        md("""
        A planner divides the question into a ticket query and a manual query. We run fixed local retrieval for each branch, then ask the model to interpret only the retrieved facts.
        """),
        code("""
        class Plan(BaseModel):
            questions: list[str]

        plan = llm.with_structured_output(Plan).invoke(
            "Return JSON with two short questions, one for tickets and one for manuals. "
            "The goal is to answer: " + QUESTION)
        questions = plan.questions
        if len(questions) < 2:
            questions = ["Which fault has the most hours in the tickets?", "Which procedure covers the leading fault?"]
        branches = [
            {"source": "tickets", "question": questions[0], "context": str(ticket_facts), "files": ["tickets.csv"]},
            {"source": "manuals", "question": questions[1],
             "context": "\\n\\n".join(f"[{n}]\\n{body[:1000]}" for n, body in search("F-CE-410 traction over-temperature procedure")),
             "files": [n for n, _ in search("F-CE-410 traction over-temperature procedure")]},
        ]
        print("research branches:", [(b["source"], b["question"]) for b in branches])
        """),
        code("""
        class ResearchState(TypedDict):
            question: str
            branches: list[dict]
            notes: Annotated[list[dict], operator.add]
            report: str

        def fan_out(state):
            return [Send("research", branch) for branch in state["branches"]]

        def research(branch):
            answer = llm.invoke([
                SystemMessage("Use only the supplied context. State what it supports and name the source file."),
                HumanMessage(f"Question: {branch['question']}\\nFiles: {branch['files']}\\nContext: {branch['context']}")
            ]).content
            return {"notes": [{"source": branch["source"], "files": branch["files"], "finding": answer}]}

        def write_report(state):
            notes = "\\n".join(f"{n['finding']} [" + ", ".join(n["files"]) + "]" for n in state["notes"])
            report = llm.invoke("Answer the question using only these notes. Keep file citations beside claims. "
                                f"Question: {state['question']}\\nNotes:\\n{notes}").content
            return {"report": report}

        graph = StateGraph(ResearchState)
        graph.add_node("research", research)
        graph.add_node("write_report", write_report)
        graph.add_conditional_edges(START, fan_out, ["research"])
        graph.add_edge("research", "write_report")
        graph.add_edge("write_report", END)
        result = graph.compile().invoke({"question": QUESTION, "branches": branches, "notes": [], "report": ""})
        print("report:\\n", result["report"])
        print("sources:", sorted({name for note in result["notes"] for name in note["files"]}))
        """),
        md("""
        A source list checks provenance, not whether each source supports the sentence beside it. We read the cited passage before using the report as an operational recommendation.

        ## Things to try

        - Ask about a fault code found in the ticket file
        - Change retrieval to return one manual and compare the evidence
        """),
    ])


if should_write("demo02-customer-support"):
    write_demo(MODULE, "demo02-customer-support", [
        md("""
        # Demo 02 : Customer support handoffs

        We route a Veenhaven Bus service request to a specialist and preserve the request in shared graph state. Run the cells in order and watch. There is nothing to write.
        """),
        section("a · customer-support", "A triage model chooses a specialist. The graph hands the same request to that specialist, which checks local records before answering."),
        code("""
        import sqlite3
        from pathlib import Path
        from typing import Literal

        from langchain.messages import HumanMessage
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Command
        from pydantic import BaseModel
        from typing_extensions import TypedDict

        DB = data("demo-world/service.db")
        REQUEST = "Bus CE12-2021-0117 reports error F-CE-410. What should the mechanic do first, and is the part in stock?"

        class Triage(BaseModel):
            specialist: Literal["manuals", "parts"]
            reason: str

        class SupportState(TypedDict):
            request: str
            specialist: str
            reason: str
            evidence: list[str]
            answer: str

        triage = llm.with_structured_output(Triage).invoke("Route the request to manuals for fault procedure or parts for stock. " + REQUEST)
        print("handoff:", triage.specialist, "because", triage.reason)
        """),
        md("""
        The first specialist may discover that another specialty is needed. A `Command` changes the destination while keeping the user request and collected evidence in state.
        """),
        code("""
        def manuals(state):
            rows = []
            for path in sorted(Path(data_folder("demo-world/manuals")).glob("*.md")):
                text = path.read_text(encoding="utf-8")
                if "F-CE-410" in text or "CE-IM-04" in text:
                    rows.append(f"[{path.name}] {text[:1200]}")
            return {"evidence": state["evidence"] + rows}

        def parts(state):
            with sqlite3.connect(f"file:{Path(DB).as_posix()}?mode=ro", uri=True) as db:
                rows = db.execute("SELECT part_no, stock, depot FROM parts WHERE part_no = 'CE-IM-04'").fetchall()
            fact = f"parts table: {rows}"
            return {"evidence": state["evidence"] + [fact]}

        def route(state):
            return state["specialist"]

        def specialist_node(name, function, next_agent):
            def run(state):
                update = function(state)
                evidence = state["evidence"] + update["evidence"]
                if next_agent:
                    return Command(goto=next_agent, update={"evidence": evidence})
                return {"evidence": evidence}
            return run

        def compose(state):
            answer = llm.invoke("Answer briefly using only the records below. Name the source file or table. "
                                f"Request: {state['request']}\\nEvidence:\\n" + "\\n".join(state["evidence"])).content
            return {"answer": answer}

        graph = StateGraph(SupportState)
        graph.add_node("manuals", specialist_node("manuals", manuals, "parts"))
        graph.add_node("parts", specialist_node("parts", parts, None))
        graph.add_node("compose", compose)
        graph.add_conditional_edges(START, route, ["manuals", "parts"])
        graph.add_edge("parts", "compose")
        graph.add_edge("compose", END)
        initial = {"request": REQUEST, "specialist": triage.specialist, "reason": triage.reason,
                   "evidence": [], "answer": ""}
        result = graph.compile().invoke(initial)
        print("evidence items:", len(result["evidence"]))
        print("answer:\\n", result["answer"])
        """),
        md("""
        The handoff preserves evidence gathered by the first specialist. The graph owns the destination and the final answer; a real support system would add a person before refunds, orders or account changes.
        """),
    ])


if should_write("demo03-code-review"):
    write_demo(MODULE, "demo03-code-review", [
        md("""
        # Demo 03 : Code review

        We send a small patch to independent reviewers, then ask a judge to resolve their findings. A deterministic checker enforces required evidence in the final review. Run the cells in order and watch. There is nothing to write.
        """),
        section("a · code-review", "Parallel reviewers receive different questions about one patch. A judge sees both findings and the patch before selecting actionable issues."),
        code("""
        import operator
        from typing import Annotated

        from langchain.messages import HumanMessage, SystemMessage
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Send
        from pydantic import BaseModel
        from typing_extensions import TypedDict

        PATCH = '''
        def reserve_part(db, part_no, quantity):
            row = db.execute("SELECT stock FROM parts WHERE part_no = ?", (part_no,)).fetchone()
            if row is None:
                return True
            db.execute("UPDATE parts SET stock = stock - ? WHERE part_no = ?", (quantity, part_no))
            return True
        '''

        class ReviewState(TypedDict):
            patch: str
            findings: Annotated[list[dict], operator.add]
            verdict: str

        def review(role):
            def run(state):
                text = llm.invoke([
                    SystemMessage("Review only the assigned concern. Report concrete issues with a short quote from the patch. If none, say none."),
                    HumanMessage(f"Concern: {role}\\nPatch:\\n{state['patch']}")
                ]).content
                return {"findings": [{"role": role, "text": text}]}
            return run

        def dispatch(state):
            return [Send(role, {"patch": state["patch"], "findings": [], "verdict": ""})
                    for role in ["correctness", "database_safety"]]

        print(PATCH)
        """),
        code("""
        class Judge(BaseModel):
            accepted_findings: list[str]
            rationale: str

        def judge(state):
            findings = llm.with_structured_output(Judge).invoke(
                "Keep only findings supported by the patch. Include quoted evidence for each accepted issue. "
                f"Patch:\\n{state['patch']}\\nReviews:\\n{state['findings']}")
            return {"verdict": "\\n".join(findings.accepted_findings) + "\\n" + findings.rationale}

        graph = StateGraph(ReviewState)
        graph.add_node("correctness", review("correctness and edge cases"))
        graph.add_node("database_safety", review("database safety and transaction behavior"))
        graph.add_node("judge", judge)
        graph.add_conditional_edges(START, dispatch, ["correctness", "database_safety"])
        graph.add_edge(["correctness", "database_safety"], "judge")
        graph.add_edge("judge", END)
        review_result = graph.compile().invoke({"patch": PATCH, "findings": [], "verdict": ""})
        print("reviewers:", [item["role"] for item in review_result["findings"]])
        print("judge:\\n", review_result["verdict"])
        """),
        md("""
        A code checker can reject structural mistakes without another model call. `no-mistakes` applies this idea to a coding fleet as a pipeline of review, tests, documentation, lint, push, pull request and CI checks.
        """),
        code("""
        REQUIRED = ["reserve_part", "SELECT", "UPDATE"]
        checks = {token: token in PATCH for token in REQUIRED}
        print("pipeline checks:", checks)
        print("checker:", "pass" if all(checks.values()) else "reject")
        """),
    ])


if should_write("demo04-data-and-content"):
    write_demo(MODULE, "demo04-data-and-content", [
        md("""
        # Demo 04 : Data and content pipelines

        We query the service database for a repeat fault, then turn sourced procedure details into a checked draft bulletin. Run the cells in order and watch. There is nothing to write.
        """),
        section("a · data-analysis", "We compute the ranking in SQL and ask the model to explain the returned rows. The database result stays visible for verification."),
        code("""
        import sqlite3

        db_path = data("demo-world/service.db")
        with sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True) as db:
            rows = db.execute("SELECT error_code, COUNT(*) AS work_orders "
                              "FROM work_orders GROUP BY error_code ORDER BY COUNT(*) DESC LIMIT 5").fetchall()
        print("query rows:", rows)
        """),
        code("""
        explanation = llm.invoke("Explain this service workload result in two sentences. Do not infer causes or totals outside the rows. "
                                 + repr(rows)).content
        print("explanation:\\n", explanation)
        """),
        section("b · content-pipeline", "We retrieve a local procedure, draft a service bulletin, and run deterministic checks before the draft can leave the pipeline."),
        code("""
        from pathlib import Path

        procedure_path = Path(data_folder("demo-world/manuals")) / "cd-12-procedure-cd-af-01.md"
        procedure = procedure_path.read_text(encoding="utf-8")
        draft = llm.invoke(f"Draft a brief internal bulletin for F-CD-101 from this procedure. Cite the source file name {procedure_path.name}, include the part, the two-hour workshop estimate, and the post-repair self test. Do not add instructions. "
                           f"\\nSource {procedure_path.name}:\\n{procedure}").content
        print("draft:\\n", draft)
        """),
        code("""
        checks = {
            "source named": procedure_path.name in draft,
            "part named": "CD-AF-01" in draft,
            "time retained": "2 hour" in draft.lower() or "two hour" in draft.lower(),
            "self test retained": "self test" in draft.lower() or "self-test" in draft.lower(),
        }
        print("checks:", checks)
        print("release:", "ready for editor" if all(checks.values()) else "hold for correction")
        """),
        md("""
        The checks establish that required details appear in the draft. An editor still compares each claim with the retrieved procedure before publication.

        ## Things to try

        - Change the SQL grouping from fault code to mechanic
        - Remove one required detail from the prompt and inspect the pipeline result
        """),
    ])

print("module 10 notebooks written")
