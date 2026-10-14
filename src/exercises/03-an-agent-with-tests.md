---
footer: Building Agents
---

# Exercise 03 : An Agent with Tests

Open `exercises/exercise03-an-agent-with-tests.ipynb` and run the setup cell. You build a stock agent on Aurelia's `service.db`, test it with a scripted model under pytest and run it once on the course model ; the solution is `solutions/exercise03-an-agent-with-tests.ipynb`.

Worked examples to revisit : `demo02 · create-agent`, `demo05 · agent-failures`, `demo07 · testing-agents`.

Made up, not from work. The Aurelia parts and stock are fictional.

---

### Step 1 : Tool

Complete the query in `part_stock` so it reads `stock` from `parts` for one `part_no`. The function already returns `Unknown part` when no row comes back.

What does the tool return for `CT-SR-03` and for `UNKNOWN`?

### Step 2 : Scripted model

`GenericFakeChatModel.bind_tools` raises `NotImplementedError`. Make `FakeToolModel.bind_tools` return the model itself, then run the scripted `part_stock` call and final answer.

Which message carries the tool result, and what is its `tool_call_id`?

### Step 3 : Pytest

Fill the middleware in `test_run_limit_stops_the_second_call` with a `ModelCallLimitMiddleware` that allows one model call and ends the run. Write the module and run pytest.

How many tests pass? The script has two tool calls ; how many tool results does the limit let through?

### Step 4 : Live run

Run the same tool on `llm` with `run_limit=4` and ask for the stock of `CT-SR-03`.

How many model calls did the live run make, and did it reach an answer before the limit?

### If time permits

- Add `ToolCallLimitMiddleware` on `part_stock` and script a second call
- Give the live agent a checkpointer, run two thread ids and compare `get_state`
- Change `run_limit` to 1 on the live agent and read the limit message
