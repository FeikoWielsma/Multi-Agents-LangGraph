"""Build module 03, State Management, on the pinned LangGraph stack.

Ports the reducer examples from ARI510 demo20, checkpoint/time-travel
structure from demo22, and namespace/profile operations from demo18.
"""
from nb import code, md, section, write_demo

MODULE = "03-state-management"


def demo(number, slug, title, cells):
    write_demo(MODULE, f"demo{number:02d}-{slug}", [
        md(f"# Demo {number:02d} : {title}\n\nRun the cells in order and watch. There is nothing to write."),
        *cells,
        md("## Things to try\n\nOptional : we can change a ticket, a thread id or a returned update and compare the saved state."),
    ])


demo(1, "state-schemas", "State schemas", [
    section("a · typed-dict", "We return a partial update. The other state keys keep their values."),
    code('''
        import csv
        from dataclasses import dataclass
        from typing import TypedDict
        from langgraph.graph import END, START, StateGraph

        with open(data("demo-world/tickets.csv"), newline="", encoding="utf-8") as file:
            ticket = next(csv.DictReader(file))

        class TicketState(TypedDict):
            ticket_id: str
            symptom: str
            status: str

        def mark_open(state: TicketState):
            return {"status": "open"}

        builder = StateGraph(TicketState)
        builder.add_node("mark_open", mark_open)
        builder.add_edge(START, "mark_open")
        builder.add_edge("mark_open", END)
        inputs = {"ticket_id": ticket["ticket_id"], "symptom": ticket["symptom"], "status": "new"}
        print("typed dict :", builder.compile().invoke(inputs))
    '''),
    md("We use a dataclass when state needs defaults. Nodes receive an instance and still return a dictionary update."),
    code('''
        @dataclass
        class TicketDefaults:
            ticket_id: str
            status: str = "new"

        def inspect_default(state: TicketDefaults):
            print("default :", state.status)
            return {"status": "open"}

        defaults = StateGraph(TicketDefaults)
        defaults.add_node("open", inspect_default)
        defaults.add_edge(START, "open")
        defaults.add_edge("open", END)
        print("dataclass :", defaults.compile().invoke({"ticket_id": ticket["ticket_id"]}))
    '''),
    section("b · pydantic", "We validate the input to a node with Pydantic. We catch the invalid input so Run All continues."),
    code('''
        from pydantic import BaseModel, Field, ValidationError

        class ValidatedTicket(BaseModel):
            ticket_id: str
            hours: float = Field(ge=0)

        def round_hours(state: ValidatedTicket):
            return {"hours": round(state.hours, 1)}

        validated = StateGraph(ValidatedTicket)
        validated.add_node("round", round_hours)
        validated.add_edge(START, "round")
        validated.add_edge("round", END)
        validated_graph = validated.compile()
        print("valid :", validated_graph.invoke({"ticket_id": ticket["ticket_id"], "hours": float(ticket["hours"])}))
        try:
            validated_graph.invoke({"ticket_id": ticket["ticket_id"], "hours": -1})
        except ValidationError as error:
            print("invalid :", error.errors()[0]["type"])
    '''),
    md("We return an invalid final update to locate the validation boundary. Pydantic validates node inputs, but the final dictionary returned by invoke is not automatically validated."),
    code('''
        boundary = StateGraph(ValidatedTicket)
        boundary.add_node("invalid_output", lambda state: {"hours": -1})
        boundary.add_edge(START, "invalid_output")
        boundary.add_edge("invalid_output", END)
        print("final update :", boundary.compile().invoke({"ticket_id": ticket["ticket_id"], "hours": 1}))
    '''),
    section("c · input-and-output", "We expose the ticket as input and the status as output. Internal state can contain both."),
    code('''
        class TicketInput(TypedDict):
            ticket_id: str

        class StatusOutput(TypedDict):
            status: str

        class InternalState(TypedDict):
            ticket_id: str
            status: str

        public = StateGraph(InternalState, input_schema=TicketInput, output_schema=StatusOutput)
        public.add_node("open", lambda state: {"status": "open"})
        public.add_edge(START, "open")
        public.add_edge("open", END)
        print("public output :", public.compile().invoke({"ticket_id": ticket["ticket_id"]}))
    '''),
    section("d · private-state", "We declare a private channel through a node's input schema. It is absent from invoke output, but remains visible in state streams."),
    code('''
        class PrivateState(TypedDict):
            working_note: str

        def prepare(state: TicketInput):
            return {"working_note": f"Inspect {state['ticket_id']}"}

        def finish(state: PrivateState):
            return {"status": state["working_note"] + " at depot"}

        private = StateGraph(InternalState, input_schema=TicketInput, output_schema=StatusOutput)
        private.add_node("prepare", prepare)
        private.add_node("finish", finish)
        private.add_edge(START, "prepare")
        private.add_edge("prepare", "finish")
        private.add_edge("finish", END)
        private_graph = private.compile()
        print("output :", private_graph.invoke({"ticket_id": ticket["ticket_id"]}))
        for part in private_graph.stream({"ticket_id": ticket["ticket_id"]}, stream_mode="values"):
            print("state :", part)
    '''),
])

demo(2, "reducers", "Reducers", [
    section("a · add-messages", "We port ARI510 demo20's message edits. add_messages appends new ids, replaces an existing id and applies RemoveMessage."),
    code('''
        from langchain.messages import AIMessage, HumanMessage, RemoveMessage
        from langgraph.graph import END, START, MessagesState, StateGraph
        from langgraph.graph.message import add_messages

        history = add_messages([], [HumanMessage("Inspect bus 4012", id="request"), AIMessage("Pending", id="reply")])
        history = add_messages(history, [AIMessage("Assigned to workshop", id="reply")])
        print("edited :", [(message.id, message.content) for message in history])
        history = add_messages(history, [RemoveMessage(id="request")])
        print("removed :", [(message.id, message.content) for message in history])

        class ServiceState(MessagesState):
            depot: str

        messages = StateGraph(ServiceState)
        messages.add_node("reply", lambda state: {"messages": [AIMessage("Workshop notified")]})
        messages.add_edge(START, "reply")
        messages.add_edge("reply", END)
        result = messages.compile().invoke({"messages": [("user", "Inspect bus 4012")], "depot": "Noord"})
        print("messages :", [message.content for message in result["messages"]])
        print("depot :", result["depot"])
    '''),
    section("b · custom-reducers", "We first keep ARI510 demo20's small sequential example. We then merge workshop findings with a custom reducer that removes duplicates and sorts the result."),
    code('''
        import operator
        from typing import Annotated, TypedDict

        class Collect(TypedDict):
            collected: Annotated[list[str], operator.add]
            last: str

        collected = StateGraph(Collect)
        collected.add_node("a", lambda state: {"collected": ["a"], "last": "a"})
        collected.add_node("b", lambda state: {"collected": ["b"], "last": "b"})
        collected.add_edge(START, "a")
        collected.add_edge("a", "b")
        collected.add_edge("b", END)
        print("sequential :", collected.compile().invoke({"collected": [], "last": ""}))

        def merge_findings(current: list[str], incoming: list[str]) -> list[str]:
            return sorted(set(current) | set(incoming))

        class Findings(TypedDict):
            findings: Annotated[list[str], merge_findings]

        findings = StateGraph(Findings)
        findings.add_node("inspect", lambda state: {"findings": ["brake inspection", "brake inspection"]})
        findings.add_edge(START, "inspect")
        findings.add_edge("inspect", END)
        print("merged :", findings.compile().invoke({"findings": ["parts lookup"]}))
    '''),
    section("c · overwriting", "We replace a reduced value with Overwrite. An ordinary empty list would pass through the reducer and retain the existing findings."),
    code('''
        from langgraph.types import Overwrite

        reset = StateGraph(Findings)
        reset.add_node("clear", lambda state: {"findings": Overwrite(value=[])})
        reset.add_edge(START, "clear")
        reset.add_edge("clear", END)
        print("ordinary empty update :", merge_findings(["parts lookup"], []))
        print("overwrite :", reset.compile().invoke({"findings": ["parts lookup"]}))
    '''),
    section("d · concurrent-updates", "We run two parallel branches that write one unreduced key. We catch InvalidUpdateError, then keep both findings with a reducer."),
    code('''
        from langgraph.errors import InvalidUpdateError

        class NoReducer(TypedDict):
            result: str

        parallel = StateGraph(NoReducer)
        parallel.add_node("parts", lambda state: {"result": "parts lookup"})
        parallel.add_node("workshop", lambda state: {"result": "brake inspection"})
        parallel.add_edge(START, "parts")
        parallel.add_edge(START, "workshop")
        parallel.add_edge("parts", END)
        parallel.add_edge("workshop", END)
        try:
            parallel.compile().invoke({"result": ""})
        except InvalidUpdateError as error:
            print("InvalidUpdateError :", str(error).splitlines()[0])

        fixed = StateGraph(Findings)
        fixed.add_node("parts", lambda state: {"findings": ["parts lookup"]})
        fixed.add_node("workshop", lambda state: {"findings": ["brake inspection"]})
        fixed.add_edge(START, "parts")
        fixed.add_edge(START, "workshop")
        fixed.add_edge("parts", END)
        fixed.add_edge("workshop", END)
        print("fixed :", fixed.compile().invoke({"findings": []}))
    '''),
])

CHAT = '''
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

def answer(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("answer", answer)
builder.add_node("record", lambda state: {})
builder.add_edge(START, "answer")
builder.add_edge("answer", "record")
builder.add_edge("record", END)
'''

demo(3, "checkpointers", "Checkpointers", [
    section("a · threads", "We keep ARI510 demo22's checkpointer structure and give a service assistant separate threads. The same thread retains messages across calls."),
    code(CHAT),
    code('''
        graph = builder.compile(checkpointer=InMemorySaver())
        morning = {"configurable": {"thread_id": "u1-morning"}}
        afternoon = {"configurable": {"thread_id": "u1-afternoon"}}
        graph.invoke({"messages": [("user", "My bus is 4012 and my depot is Noord. Acknowledge briefly.")]}, morning)
        remembered = graph.invoke({"messages": [("user", "Which bus and depot did I mention?")]}, morning)
        separate = graph.invoke({"messages": [("user", "Which bus and depot did I mention? If unknown, say so.")]}, afternoon)
        print("same thread :", remembered["messages"][-1].content)
        print("new thread :", separate["messages"][-1].content)
        snapshot = graph.get_state(morning)
        print("saved messages :", len(snapshot.values["messages"]))
        print("next :", snapshot.next)
        print("checkpoint :", snapshot.config["configurable"]["checkpoint_id"])
    '''),
    md("We compare the saved messages as well as the replies. A model can guess a bus or depot on a new thread, but the checkpoint shows which context it received."),
    section("b · sqlite-saver", "We close a SQLite connection after a saved pause. We open the same file and compile a second graph to restore and finish the run."),
    code('''
        from pathlib import Path
        from uuid import uuid4
        from langgraph.checkpoint.sqlite import SqliteSaver

        notebook_dir = ROOT / "notebooks" / "03-state-management" if ROOT else Path("notebooks/03-state-management")
        notebook_dir.mkdir(parents=True, exist_ok=True)
        database = notebook_dir / "module03.db"
        config = {"configurable": {"thread_id": f"sqlite-{uuid4().hex}"}}
        with SqliteSaver.from_conn_string(str(database)) as saver:
            persistent = builder.compile(checkpointer=saver, interrupt_after=["answer"])
            persistent.invoke({"messages": [("user", "Write one short acknowledgement of brake inspection for bus 4012.")]}, config)
            print("saved next :", persistent.get_state(config).next)

        with SqliteSaver.from_conn_string(str(database)) as saver:
            restored = builder.compile(checkpointer=saver)
            snapshot = restored.get_state(config)
            print("restored next :", snapshot.next)
            print("saved reply :", snapshot.values["messages"][-1].content)
            restored.invoke(None, config)
            print("finished next :", restored.get_state(config).next)
        print("file exists :", database.exists())
    '''),
])

demo(4, "history-and-time-travel", "History and time travel", [
    section("a · state-history", "We port ARI510 demo22's checkpoint history and fork. A draft node calls the model, then a record node copies the draft into state without an external action."),
    code('''
        import csv
        from typing import TypedDict
        from langgraph.graph import END, START, StateGraph
        from langgraph.checkpoint.memory import InMemorySaver

        with open(data("demo-world/tickets.csv"), newline="", encoding="utf-8") as file:
            ticket = next(csv.DictReader(file))

        class Reply(TypedDict):
            symptom: str
            draft: str
            recorded: str

        calls = []
        def draft(state: Reply):
            calls.append("draft")
            return {"draft": llm.invoke("Write one short acknowledgement of this bus service report. Do not claim a repair is complete: " + state["symptom"]).content}

        builder = StateGraph(Reply)
        builder.add_node("draft", draft)
        builder.add_node("record", lambda state: {"recorded": state["draft"]})
        builder.add_edge(START, "draft")
        builder.add_edge("draft", "record")
        builder.add_edge("record", END)
        graph = builder.compile(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "ticket-history"}}
        original = graph.invoke({"symptom": ticket["symptom"], "draft": "", "recorded": ""}, config)
        history = list(graph.get_state_history(config))
        for snapshot in history:
            print("step :", snapshot.metadata["step"], "next :", snapshot.next, "draft :", snapshot.values.get("draft", ""))
        before_draft = next(snapshot for snapshot in history if snapshot.next == ("draft",))
        before_record = next(snapshot for snapshot in history if snapshot.next == ("record",))
        original_final = graph.get_state(config).config
        print("original :", original["recorded"])
    '''),
    section("b · replay", "We invoke None with a historical checkpoint config. Execution continues from its next nodes, so replay before draft calls the model again and can change the wording."),
    code('''
        count_before = len(calls)
        replayed = graph.invoke(None, before_draft.config)
        print("replayed :", replayed["recorded"])
        print("new model calls :", len(calls) - count_before)
        print("saved original :", graph.get_state(original_final).values["recorded"])
    '''),
    section("c · forking", "We edit the saved draft as an update from the draft node. The returned config selects a new checkpoint whose next node is record."),
    code('''
        forked = graph.update_state(before_record.config, {"draft": "Bus report received. The workshop will review it."}, as_node="draft")
        count_before = len(calls)
        alternative = graph.invoke(None, forked)
        print("fork :", alternative["recorded"])
        print("new model calls :", len(calls) - count_before)
        print("parent unchanged :", graph.get_state(before_record.config).values["draft"] == before_record.values["draft"])
    '''),
    md("We also inspect DeltaChannel on this pin. Its reducer receives a batch of writes, and the checkpoint saver reconstructs the accumulated list from saved writes. The API is beta."),
    code('''
        from typing import Annotated
        from langgraph.channels import DeltaChannel

        def merge_batches(current, writes):
            return current + [item for batch in writes for item in batch]

        class LongThread(TypedDict):
            entries: Annotated[list[str], DeltaChannel(merge_batches, snapshot_frequency=2)]

        long_builder = StateGraph(LongThread)
        long_builder.add_node("append", lambda state: {"entries": ["workshop checked"]})
        long_builder.add_edge(START, "append")
        long_builder.add_edge("append", END)
        long_graph = long_builder.compile(checkpointer=InMemorySaver())
        long_config = {"configurable": {"thread_id": "delta-thread"}}
        long_graph.invoke({"entries": ["ticket opened"]}, long_config)
        long_graph.invoke({"entries": ["parts arrived"]}, long_config)
        print("delta restored :", long_graph.get_state(long_config).values["entries"])
        print("delta history :", [snapshot.values["entries"] for snapshot in long_graph.get_state_history(long_config) if "entries" in snapshot.values])
    '''),
])

demo(5, "the-store", "The Store", [
    section("a · the-store", "We port ARI510 demo18's namespace and key operations. The same namespace and key replace a profile document; a collection uses separate keys."),
    code('''
        from langgraph.store.memory import InMemoryStore

        store = InMemoryStore()
        namespace = ("users", "u1", "profile")
        store.put(namespace, "depot", {"text": "depot: Noord"})
        store.put(namespace, "language", {"text": "language: Dutch"})
        store.put(("users", "u2", "profile"), "depot", {"text": "depot: Zuid"})
        print("profile :", store.get(namespace, "depot").value)
        print("u1 keys :", sorted(item.key for item in store.search(namespace)))
        print("u2 :", [item.value for item in store.search(("users", "u2", "profile"))])
        store.put(namespace, "depot", {"text": "depot: West"})
        print("updated :", store.get(namespace, "depot").value)
        store.delete(namespace, "language")
        print("deleted :", store.get(namespace, "language"))
    '''),
    md("We pass a user id through runtime context and keep it independent of thread_id. The graph retrieves the same profile from separate threads for one user."),
    code('''
        from dataclasses import dataclass
        from typing import TypedDict
        from langgraph.graph import END, START, StateGraph
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.runtime import Runtime

        @dataclass
        class Context:
            user_id: str

        class MemoryState(TypedDict):
            depot: str

        def recall(state: MemoryState, runtime: Runtime[Context]):
            item = runtime.store.get(("users", runtime.context.user_id, "profile"), "depot")
            return {"depot": item.value["text"] if item else "unknown"}

        builder = StateGraph(MemoryState, context_schema=Context)
        builder.add_node("recall", recall)
        builder.add_edge(START, "recall")
        builder.add_edge("recall", END)
        graph = builder.compile(store=store, checkpointer=InMemorySaver())
        for user, thread in [("u1", "u1-morning"), ("u1", "u1-afternoon"), ("u2", "u2-afternoon")]:
            result = graph.invoke({"depot": ""}, {"configurable": {"thread_id": thread}}, context=Context(user))
            print(user, thread, result["depot"])
    '''),
    md("We keep ticket facts in a collection and filter by stored fields. Search without an embedding index retrieves matching items; it does not rank by meaning."),
    code('''
        import csv

        with open(data("demo-world/tickets.csv"), newline="", encoding="utf-8") as file:
            tickets = list(csv.DictReader(file))[:3]
        for ticket in tickets:
            store.put(("bus", tickets[0]["fleet_no"], "issues"), ticket["ticket_id"],
                      {"text": ticket["symptom"], "error_code": ticket["error_code"]})
        hits = store.search(("bus", tickets[0]["fleet_no"], "issues"), filter={"error_code": tickets[0]["error_code"]})
        print("filtered :", [(item.key, item.value) for item in hits])
    '''),
])

demo(6, "debugging-with-stream-modes", "Debugging with stream modes", [
    section("a · stream-modes", "We port ARI510's streaming modes and inspect state alongside a live model reply. A checkpoint saver enables checkpoint events."),
    code('''
        from typing import TypedDict
        from langgraph.graph import END, START, StateGraph
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.config import get_stream_writer

        class DebugState(TypedDict):
            report: str
            reply: str

        def acknowledge(state: DebugState):
            get_stream_writer()({"status": "drafting"})
            return {"reply": llm.invoke("Write one brief acknowledgement of this bus service report: " + state["report"]).content}

        builder = StateGraph(DebugState)
        builder.add_node("acknowledge", acknowledge)
        builder.add_edge(START, "acknowledge")
        builder.add_edge("acknowledge", END)
        graph = builder.compile(checkpointer=InMemorySaver())
        inputs = {"report": "Bus 4012 needs brake inspection at Noord.", "reply": ""}
        config = {"configurable": {"thread_id": "debug-live"}}
        modes = ["values", "updates", "debug", "messages", "custom", "checkpoints", "tasks"]
        parts = list(graph.stream(inputs, config, stream_mode=modes, version="v2"))
        for part in parts:
            if part["type"] == "messages":
                continue
            if part["type"] in {"debug", "tasks", "checkpoints"}:
                print(part["type"], ":", str(part["data"])[:500])
            else:
                print(part["type"], ":", part["data"])
        tokens = [part["data"][0].content for part in parts if part["type"] == "messages"]
        print("message chunks :", len(tokens))
        print("reply :", graph.get_state(config).values["reply"])
        print("v2 keys :", sorted(parts[0]))
        print("namespace :", parts[0]["ns"])
        print("emitted modes :", sorted({part["type"] for part in parts}))
    '''),
    md("We inspect experimental v3 projections on a deterministic graph to avoid another model call. Iterating a projection drives the run; output becomes available when the run finishes."),
    code('''
        class Counter(TypedDict):
            value: int

        small = StateGraph(Counter)
        small.add_node("increment", lambda state: {"value": state["value"] + 1})
        small.add_edge(START, "increment")
        small.add_edge("increment", END)
        small_graph = small.compile()
        run = small_graph.stream_events({"value": 0}, version="v3")
        for state in run.values:
            print("v3 value :", state)
        print("v3 output :", run.output)
        print("v3 interrupted :", run.interrupted)
        parent = StateGraph(Counter)
        parent.add_node("counter", small_graph)
        parent.add_edge(START, "counter")
        parent.add_edge("counter", END)
        lifecycle = parent.compile().stream_events({"value": 0}, version="v3")
        for event in lifecycle.lifecycle:
            print("v3 lifecycle :", event)
    '''),
])

print("module 03 notebooks written")
