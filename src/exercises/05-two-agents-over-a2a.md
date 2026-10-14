---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Agent Communication
---

# Exercise 05 : Two Agents over A2A

Open `exercises/exercise05-two-agents-over-a2a.ipynb` and run the setup cell. You serve an Aurelia parts agent and a service desk agent on two local Agent Servers and let the desk call the parts agent over A2A by replacing the `____` blanks ; the solution is `solutions/exercise05-two-agents-over-a2a.ipynb`.

Worked examples to revisit : `demo03 · served-agents`, `demo04 · two-agents-over-a2a`.

Made up, not from work. The Aurelia parts and stock are fictional.

---

### Step 1 : Graph sources

In `coordinator_source`, fill the assistant id key from `/assistants/search`, the JSON-RPC method and the `contextId`. Run the cell that writes both sources into `parts` and `desk` runtime folders.

Which of the two sources opens `service.db`, and how does the desk get its stock facts?

---

### Step 2 : Agent cards

Fill the `assistant_id` parameter of the card request and run the cell. It starts the parts agent on port 2125 and the desk on 2124.

Which id appears at the end of each card's `url` : the graph name or a UUID?

---

### Step 3 : First task

Fill the context constructor, the method and the result key, then send the CT-400 visit request to the desk. The cell prints the desk's stored remote exchange.

Which part do the two task ids share, and which part differs?

---

### Step 4 : Same context

Send the follow-up with the saved `context` and no task id. Fill the method that fetches the new task by id.

Which keys does `GetTask` return, and where is the answer text? How long is the history with `historyScope="task"` and without it?

---

### Step 5 : Shutdown

Run the final cell. It stops both servers and prints the calls and tokens from both sides. Call `stop_servers()` at once if a cell fails while a server runs.

Are ports 2124 and 2125 released?

---

### If time permits

- Send a third question through the desk with the same context and compare both histories
- Call the parts agent with `message/send` and compare its response shape with `SendMessage`
- Send a context that is not a UUID and read the JSON-RPC error ; no model call is made
