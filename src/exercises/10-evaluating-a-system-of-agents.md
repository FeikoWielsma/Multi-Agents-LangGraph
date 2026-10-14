---
footer: Production Deployment
---

# Exercise 10 : Evaluating a System of Agents

Open `exercises/exercise10-evaluating-a-system-of-agents.ipynb` and run the setup cell. You score Aurelia's parts agent, manuals agent and desk on cases from `eval.jsonl` by replacing the `____` blanks ; the solution is `solutions/exercise10-evaluating-a-system-of-agents.ipynb`.

Worked examples to revisit : `demo05 · evaluating-agents`, `demo05b · trajectory-match`, `demo05d · each-agent`.

Made up, not from work. The Aurelia service records, manuals and evaluation cases are fictional.

---

### Step 1 : Agents and cases

Run the cell that builds `parts_agent`, `manuals_agent` and `desk`. Read their tool lists and the case ids in `SELECTED`, then run the check.

Which six case ids does the cell select from `CASES`?

### Step 2 : Answer scores

Complete the message type, case conversion and tool-list blanks in `score_answer`. Check for at least one expected fact in the answer and every expected tool in the messages. Run all `SELECTED` cases through `desk` and read `desk_results`.

How many cases pass both `facts_ok` and `tools_ok` in your run?

### Step 3 : Trajectory match

Run the live `man-01` comparison against `reference`. Fill `trajectory_match_mode` in the fixture loop to compare `strict` and `unordered`, keeping `tool_args_match_mode="ignore"`. Run the reordered-call and one-call fixtures, then the check.

How do the two modes score the live messages, `reversed_calls` and `one`?

### Step 4 : Per-agent scores

Fill the two agent blanks in `per_agent` with the specialist for `db_case` and the specialist for `man_case`. Run the mixed-case calls and compare each specialist's row with `desk_mix`, then run the check.

Which `mix-01` rows pass `facts_ok` but fail `tools_ok`?

### If time permits

- Re-score the live `man-01` trajectory without `tool_args_match_mode="ignore"` and compare the argument checks
- Add `subset` and `superset` to the trajectory table
- Replace the fact check with a trajectory judge on one mixed case
