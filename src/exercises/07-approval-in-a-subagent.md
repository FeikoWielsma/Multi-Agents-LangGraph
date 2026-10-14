---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Advanced Workflows
---

# Exercise 07 : Approval in a Subagent

Open `exercises/exercise07-approval-in-a-subagent.ipynb` and run the setup cell. You build an Aurelia supervisor whose parts subagent pauses for a person's approval before it records a spare parts order, by replacing the `____` blanks ; the solution is `solutions/exercise07-approval-in-a-subagent.ipynb`.

Worked examples to revisit : `demo01 · interrupts`, `demo02 · interrupts-in-multi-agent`.

Made up, not from work. The Aurelia parts, prices and orders are fictional.

---

### Step 1 : Order policy

Complete `reviewer` : the manager above 10,000 EUR, the lead otherwise. Complete the quantity bound in `validated_order` : positive and within stock.

Which reviewer does each of the three requests get? What does `A-edit` cost at quantity 1?

---

### Step 2 : Parts subagent

In `review_order`, call `interrupt` and match the `reject`, `edit` and `approve` actions. An edit reads its new quantity from the decision.

Which statements in `review_order` run before `interrupt`, and will they run again on resume?

---

### Step 3 : Supervisor tool

Invoke `parts_subagent` inside `parts_specialist`, and give the supervisor an in-memory checkpointer.

Why does only the supervisor get a checkpointer, and not `parts_subagent`?

---

### Step 4 : Top-level pause

Run the three requests, each in its own supervisor thread.

What does `get_state(cfg).next` show for each thread, and is any order in `ORDERS` yet?

---

### Step 5 : Decisions

Fill the decisions : approve the helium filters, edit the fan order to quantity 1, and reject the detector module. Resume each saved supervisor thread with its decision.

Why do `tool_entries` and `review_entries` reach 2 for every order while `ORDERS` holds each approved order once?

---

### If time permits

- Edit an order to quantity 0 or above stock and read the validation error
- Print the supervisor state history and find the checkpoint with the pending approval
- Add a second review by the manager after the lead approves an expensive order
