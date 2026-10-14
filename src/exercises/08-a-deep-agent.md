---
footer: Deep Agents
---

# Exercise 08 : A Deep Agent

Open `exercises/exercise08-a-deep-agent.ipynb` and run the setup cell. You build an Aurelia briefing agent with a manuals backend, a skill and a parts subagent by replacing the `____` blanks ; the solution is `solutions/exercise08-a-deep-agent.ipynb`.

Worked examples to revisit : `demo02b · write-todos`, `demo04d · composite`, `demo06b · skills`, `demo07 · subagents`.

Made up, not from work. The Aurelia manuals, parts and stock are fictional.

---

### Step 1 : Manuals backend

Run the cell that defines `part_stock`, `disk` and `backend`, then the check. Read the sample from the CT-400 error-code manual and the `disk.ls("/")` listing.

How many manuals does `PAGES` contain?

### Step 2 : Skill

Complete the front matter and body in `SKILL_MD` for `error-briefing`. Tell the agent to read the Aurelia manuals, state the error's meaning and first action, and keep the briefing to three bullets. Run the skill-text check.

Which directory does the printed skill tell the agent to read?

### Step 3 : Parts subagent

Complete `name`, `description`, `system_prompt` and `tools` in `parts` for stock lookups through `part_stock`. Keep `parts_llm` as its model and run the check.

Which name and description does the cell print for the subagent?

### Step 4 : Briefing

Fill `backend`, `middleware`, `skills` and `subagents` in `create_deep_agent`. Use the objects from the earlier cells, add planning with `TodoListMiddleware`, and point skills at `/skills/`. Run the supplied E-CT-110 and CT-FN-02 request, then the check. Read `todos`, `files` and `seen_by_parts` alongside the answer.

Does `seen_by_parts` contain the parent skill text or only the delegated stock request?

### If time permits

- Change the skill so the briefing must name the depot as well, and run again
- Add a second dict subagent for manuals and move the parent's `/manuals/` reads into it
- Compare tokens with and without `TodoListMiddleware` on the same task
