---
footer: Introduction to LangGraph
---

# Exercise 0 : Lab Setup

Open a terminal in the repository root on the classroom laptop. The trainer has installed `uv`, the repository and its packages ; you add the course key, run the check and start Jupyter.

---

### Step 1 : Key

Copy `.env.example` to `.env` and paste the OpenRouter key from the trainer after `COURSE_API_KEY=` :

```powershell
Copy-Item .env.example .env
notepad .env
```

Leave the other values as they are. Never paste a key into a notebook ; `.env` is ignored by git.

### Step 2 : Check

```powershell
uv run python check_setup.py
```

Does it report `7 of 7 checks passed`? An authentication failure on every line means the key is missing or wrong. A missing package means `uv sync --group server` has to run first. Tell the trainer either way.

### Step 3 : Notebooks

```powershell
uv run jupyter lab
```

Open `notebooks/` and run the setup cell of the notebook the trainer names. Keep this terminal open.

### If time permits

- Run `uv tree --depth 1` and compare the `langgraph` version with the one the check printed
- Find the line in `check_setup.py` that switches reasoning off for the course model
- Find the second model the check calls besides `COURSE_MODEL`
