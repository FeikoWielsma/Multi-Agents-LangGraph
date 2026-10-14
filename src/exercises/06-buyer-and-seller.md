---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Agent Communication
---

# Exercise 06 : Buyer and Seller

Open `exercises/exercise06-buyer-and-seller.ipynb` and run the setup cell. You let an Aurelia procurement agent and a parts seller agent negotiate three helium compressor filters, each under a private price policy, by replacing the `____` blanks ; the solution is `solutions/exercise06-buyer-and-seller.ipynb`.

Worked examples to revisit : `demo06 · conflicts`, `demo07 · buyer-and-seller`.

Made up, not from work. The Aurelia stock and both price policies are fictional.

---

### Step 1 : Private policies

Complete `read_policy` : raise `PermissionError` unless the principal's role is `owner` and its scope is `expected_scope[owner]`. Run the two policy checks.

Which values in `ORDER` come from `service.db`, and which values live only in `BUYER` or `SELLER`?

---

### Step 2 : Scoped agents

Give `buyer` and `seller` each its own policy tool. `ToolRuntime` passes the principal as context.

What does the printed tool schema of `buyer_policy` contain, and can the model name a role through it?

---

### Step 3 : Settlement

In `settle`, fill the condition that sends non-overlapping prices to review and the midpoint price. Join `buyer` and `seller` into `settle`, then run the three fixture checks.

Why does `proposals` need a reducer when both agents write it in the same step?

---

### Step 4 : Negotiation

Run the two rounds. Only the public prices of round 1 go into round 2.

What were the opening offers, and what did round 2 settle on? Which rule would keep a crossed result in review?

---

### Step 5 : Access denial

Read the seller policy with the buyer principal. The cell then tries a seller role with the buyer's scope. Run the metrics cell.

Which message does the denial print, and does it come from the prompt or from `read_policy`?

---

### If time permits

- Raise the seller floor above the buyer ceiling and confirm the result stays in review
- Replace the midpoint rule with a model judge, then check its output against both policies
- Add a delivery deadline to each private policy and share only the proposed delivery date
