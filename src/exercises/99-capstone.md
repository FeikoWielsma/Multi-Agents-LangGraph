---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Real-World Applications
---

# Capstone : Aurelia Service Desk

Open `exercises/capstone-stage1.ipynb` and run the setup cell. Build a service desk for Aurelia Imaging Systems, a fictional maker of hospital imaging equipment. Find each stage's solution in `solutions/capstone-stageN.ipynb`.

Use the supplied data in `data/capstone/`, made up, not from work. Inspect `service.db`, `manuals/`, `tickets.csv` and `eval.jsonl`. Keep `untrusted/` out of the trusted manuals search.

Run the supplied previous-stage definitions at the start of each later notebook. A missed stage does not block the next one. Complete all numbered steps unless the trainer takes the stage 3 A2A cut. Items under `If time permits` are optional.

Keep `COURSE_RPS=0.08` and run one notebook at a time. Use the supplied server cells and run the final stop cell in stages 3 to 5, including after a failed cell. Keep the course key in `.env`.

---

### Stage 1 : Graph workflow

Open `exercises/capstone-stage1.ipynb`. Add triage, database lookup, answers and checkpoints to Aurelia's desk after module 03 on Monday. Allow 45 to 60 minutes.

### Step 1 : Triage

1. Complete the typed evidence field and the edge from lookup to answer.
2. Inspect the supplied triage expressions and read-only queries.
3. Run the lookup check and compare the ticket fields with the database result.

Which device field does triage extract before the database lookup?

---

### Step 2 : Checkpoints

1. Compile the workflow with an in-memory checkpointer.
2. Run the three database questions.
3. Compare each returned answer with the saved state on its thread.

Does each saved answer match the returned answer?

### Step 3 : Boundaries

1. Run the unknown-device and mixed-fault questions.
2. Read both answers beside the database evidence.

Which question needs a manual before Aurelia can identify a replacement part?

### If time permits

- Add a site contract lookup
- Restore a checkpoint with `SqliteSaver`
- Inspect state history before the answer node

---

### Stage 2 : Specialist supervisor

Open `exercises/capstone-stage2.ipynb` and run the supplied stage 1 definitions. Add parts, manuals and scheduling specialists behind Aurelia's supervisor after module 05 on Tuesday. Allow 45 to 60 minutes.

### Step 1 : Specialists

1. Complete the manuals tool list and scheduling query parameters.
2. Inspect each specialist's tool schema.
3. Run the certification and trusted-manual checks.

Which engineers does the scheduling query return for MR-150?

---

### Step 2 : Delegation

1. Complete the isolated parts invocation.
2. Build the supervisor with a checkpointer.
3. Follow the worker messages and returned summary when running the next cell.

How many messages does the parts worker's printed context contain?

### Step 3 : Measurements

1. Run the same three questions through stage 1 and stage 2.
2. Compare the answers, calls, input tokens and output tokens.

Does stage 2 answer these database questions more accurately at the additional call cost?

### If time permits

- Ask the mixed fault question and inspect both specialist summaries
- Add a ticket-history specialist
- Remove an unnecessary delegation and measure again

---

### Stage 3 : Diagnosis and approval

Open `exercises/capstone-stage3.ipynb` and run the supplied stage 2 definitions. Add parallel diagnosis, a judge, a served manuals agent and order approval to Aurelia's desk after module 07 on Tuesday. Allow 60 to 75 minutes.

### Step 1 : Manuals service

1. Run the export cell and inspect `GRAPH_SOURCE`.
2. Complete the A2A method and UUID context id.
3. Start the manuals server on port 2145 and read its agent card.

Does the printed assistant id match the graph name `manuals`?

On `langgraph-api` 0.16.0, use the assistant UUID resolved by `assistants.search` for the A2A endpoint and a fresh UUID for `contextId`.

---

### Tuesday trainer cut

Skip the A2A part when the trainer takes this cut :

1. Run the server-helper cell to initialise the empty server list for cleanup.
2. Use the local manuals worker with `record_trace` in place of A2A.
3. Skip server startup and the remote-usage assertion.
4. Keep the three-finding check, parallel diagnosis and order approval.

### Step 2 : Parallel diagnosis

1. Complete the fan-in edge to the judge.
2. Run the mixed fault question.
3. Compare all three findings with the judge's answer.

Which airflow condition does the judge retain before recommending CT-FN-02?

---

### Step 3 : Order approval

1. Request a fan through the supervisor's order subagent.
2. Inspect the ledger while the top-level graph is interrupted.
3. Resume that supervisor on the same thread with approval.
4. Request another fan and reject it. Inspect the ledger again.

When does a simulated order enter the ledger?

Run the final server stop cell, including after the trainer cut.

### If time permits

- Request a tube above 10000 EUR and inspect the service-manager rule
- Compare A2A with the in-process manuals worker
- Inspect the child checkpoint while approval waits

---

### Stage 4 : Deep Agent desk

Open `exercises/capstone-stage4.ipynb` and run the supplied stage 3 definitions. Rebuild Aurelia's desk with procedure skills and specialist subagents after module 08 on Wednesday. Allow 60 to 75 minutes.

### Step 1 : Procedure skills

1. Complete the virtual skills source and compiled specialist entry.
2. Read the diagnosis, scheduling and ordering procedures.
3. Run the harness configuration check.

Which procedure files are available to the desk?

---

### Step 2 : Graph baseline

1. Start the stage 3 manuals server.
2. Run `db-01`, `db-03`, `db-04`, `man-01` and `mix-01` through the graph.
3. Read every answer beside its phrase screen, especially the MR-150 certification answer.

Does the passing `db-04` screen agree with the answer's claim about certification?

### Step 3 : Harness comparison

1. Run the same five cases through the Deep Agent.
2. Compare answers, screens, calls, tokens and the printed code counts.
3. Inspect the worker traces for missing certification evidence.

Does the Deep Agent use fewer orchestration lines while consuming more input tokens?

Compare only the counted stage additions, which exclude shared tools and stage 4's reused approval code.

---

### Step 4 : Approval transfer

1. Request a fan through the Deep Agent's orders subagent.
2. Inspect the top-level interrupt and reject the request.
3. Check the ledger and run the final server stop cell.

Does rejection leave the ledger empty?

### If time permits

- Pin a procedure and compare `read_file` calls
- Inspect the general-purpose subagent's scope
- Add human-reviewed correctness labels beside the phrase screens

---

### Stage 5 : Served evaluation

Open `exercises/capstone-stage5.ipynb` and run the supplied stage 4 definitions. Serve Aurelia's desk, launch async diagnosis and score answers and ticket costs after module 09 on Wednesday. Allow 60 to 75 minutes.

### Step 1 : Graph exports

1. Inspect the service, dispatcher and diagnostician exports in `GRAPH_SOURCE`.
2. Complete the diagnostician registration.
3. Start the supplied server on port 2144 and check its graph ids.

Which three graphs does the server register?

---

### Step 2 : Async diagnosis

1. Launch the long diagnosis with `start_async_task` and retain its task id.
2. Complete the SDK wait on the child run.
3. Ask the dispatcher to fetch fresh status with `check_async_task`.
4. Inspect the child's answer and usage.

Which status appears at launch and which appears after the dispatcher fetches the result?

---

### Step 3 : Agent scores

1. Complete the trajectory coverage mode and run the same five cases through the served desk.
2. Compare specialist coverage, system coverage, phrase screens and final answers.
3. Inspect the printed arguments for `db-04` and `mix-01` against the database values.

Which two answers fail despite coverage scoring `True`?

Inspect the saved solution : all coverage scores are `True`, but two of five answers are wrong or incomplete after `lookup_parts(model="CT400")` instead of `CT-400` and `engineers(model="Aurelia MR-150", region="")` instead of canonical `MR-150`.

---

### Step 4 : Ticket costs

1. Read the notebook's dated public OpenRouter price snapshot.
2. Complete the output-token rate lookup.
3. Calculate each ticket's cost from its measured input and output tokens.

Which of the five tickets has the highest estimated cost?

Treat the result as an uncached token list-price estimate, excluding infrastructure, retries, discounts and optional judge calls.

Run the final server stop cell.

### If time permits

- Add argument validation for canonical model names and the optional region filter
- Judge one failed trajectory and compare a human correctness label
- Steer or cancel a second async task before its model call
