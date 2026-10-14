---
footer: State Management
---

# Exercise 02 : State for Two Agents

Open `exercises/exercise02-state-for-two-agents.ipynb` and run the setup cell. You run a triage node and a parts node in parallel on Aurelia ticket T-1001 by replacing the `____` blanks ; the solution is `solutions/exercise02-state-for-two-agents.ipynb`.

Worked examples to revisit : `demo01 · state-schemas`, `demo02 · reducers`, `demo03 · checkpointers`, `demo04 · history-and-time-travel`.

Made up, not from work. The Aurelia tickets and `service.db` are fictional.

---

### Step 1 : Shared key

Run the cell that reads T-1001 from `tickets.csv`. Add the two edges from `START` to `triage` and `parts`, then run the check cell. Both nodes write `note`.

Which error does the check catch, and what does its first line say about `note`?

### Step 2 : Reducer

Give `findings` in `Shared` a list type with a reducer that appends. Run both nodes again.

Which findings does the result keep, and which keys did each node read?

### Step 3 : Private key

`lookup` writes `stock_note`, the stock line for the slip ring brush kit. Type `stock_note` in `PartsView`, and choose the `output_schema` that leaves it out of the result.

Which keys does the invoke result contain? Where does `stock_note` still appear, and which keys did triage read?

### Step 4 : History

Compile `desk` again with a checkpointer, give `cfg` a thread id, and list the thread's state history.

How many checkpoints does the thread keep, and which step has an empty `next`?

### If time permits

- Open a second thread id on `saved` and compare `get_state` on both
- Replace `InMemorySaver` with `SqliteSaver` and open the same thread again
- Fork the checkpoint before `parts` with `update_state` and change `stock_note`
