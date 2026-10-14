---
footer: Multi-Agent Patterns
---

# Exercise 04 : A Multi-Agent Visit Planner

Open `exercises/exercise04-a-multi-agent-visit-planner.ipynb` and run the setup cell. You plan an engineer's visit to Aurelia site S04 with a parts agent, a manuals agent and a code checker, then compare it with one agent ; the solution is `solutions/exercise04-a-multi-agent-visit-planner.ipynb`.

Worked examples to revisit : `demo01 · subagents`, `demo03 · router`, `demo07 · maker-checker`, `demo09 · what-each-pattern-costs`.

Made up, not from work. The Aurelia sites, devices and manuals are fictional.

---

### Step 1 : Tools

Run the two cells. They define `run_sql` and `search_manuals` and list the devices at S04.

What does `run_sql` return for `DELETE FROM devices`?

### Step 2 : Checker

Write `check_plan(plan, site_id)`. It returns a list of problems, empty when the plan passes :

- Every device at the site appears in the plan by serial number
- Every part number that `PART` matches exists in `parts`
- A part with stock 0 has "out of stock" on the same line

Error codes such as `E-MR-202` do not match `PART`. The test cell must pass before you go on.

Which three problems does `BAD` have?

### Step 3 : Router

Complete `manuals_question` from `state["devices"]`, `dispatch` with one `Send` to `parts` and one to `manuals`, and `after_check` : `"assemble"` while problems remain and `rounds` is under 2, otherwise `END`. Replace the blank line with an edge from both specialists to `assemble`.

Which nodes does `dispatch` send to, and what does `after_check` return once `rounds` reaches 2?

### Step 4 : Cost

Run the planner for S04, then the single agent with both tools on the same task. The metrics lines print calls and tokens for each.

How many model calls and tokens did each design use? Did the checker pass the planner's plan?

### If time permits

- Plan site S01 with `run_planner`
- Add a fourth check : every CT-400 on firmware below 5.2 gets the 12-month fan interval
- Replace the router with a handoff. Disable parallel tool calls, and forward the full worker history with the transfer receipt, as in `demo04 · handoffs`
