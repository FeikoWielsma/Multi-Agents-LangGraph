---
footer: Production Deployment
---

# Exercise 11 : An Async Subagent on a Server

Open `exercises/exercise11-an-async-subagent-on-a-server.ipynb` and run the setup cell. You serve an Aurelia supervisor and diagnosis worker, then start and collect an async task by replacing the `____` blanks ; the solution is `solutions/exercise11-an-async-subagent-on-a-server.ipynb`.

Worked examples to revisit : `demo03 · async-subagents`.

Made up, not from work. The Aurelia diagnoses, manuals and stock are fictional.

---

### Step 1 : Graph sources

Run the cell that writes `course_runtime.py`, `graphs.py` and `langgraph.json`, then the file check. Read the printed graph configuration.

Which graph ids does `langgraph.json` expose?

### Step 2 : Agent Server

Run the server helpers. Fill the port blanks in `start_server` and `connect` to match the supplied `/ok` request. Run the startup cell and the assistant check.

Which assistants does the server list?

### Step 3 : Task lifecycle

Run `supervise` to start the E-CT-110 and CT-FN-02 diagnosis, check `task_id` and list the tasks. Expect the worker to hold for about two minutes before its model call so the first check sees `running`. Replace the final blank with assertions that `first_status` has the expected status and `used` includes all three requested lifecycle tools.

Which lifecycle tool names does `used` contain after the list request?

### Step 4 : Task result

Run `client.runs.join` on the child run and expect to wait for the hold and diagnosis to finish. Check the task again through `supervise`. Replace the final blank with assertions on `status` and the returned diagnosis facts. Run the final cell to stop every process in `servers` ; call `stop_server` on those processes at once if a cell fails while the server runs.

What first action and CT-FN-02 stock does the collected answer report?

### If time permits

- Cancel a second delayed task before it finishes
- Steer the running task with `update_async_task` to look up UX-BT-02 instead
- Restart the server in the same folder and read whether the thread still lists the task
