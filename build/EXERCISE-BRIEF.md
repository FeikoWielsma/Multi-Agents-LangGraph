# Brief for the exercise and capstone agents

Read with `build/BUILD-BRIEF.md`, which still applies : house style, running
notebooks, rate budgets, measurements, never a key in a file, never the PDF build.

## Read first

- `build/plan.md` : "The capstone", "The days", the module sections your exercises follow
- `build/course-map.md` : exercise numbers and titles ; they are fixed
- The slides and executed demo notebooks of the modules your exercises follow. An
  exercise practises what those demos showed, on a different problem
- ARI510, the published sibling course, as the model for form. Copy freely, never edit :
  - `../Agentic-AI-LangChain/build/exercise-prerequisites.md` : the current standard for
    exercises and how each one names the demos it builds on
  - `../Agentic-AI-LangChain/src/exercises/12-graphs-and-loops.md`,
    `13-human-approval.md`, `17-multi-agent-patterns.md`, `99-capstone.md` : guides
  - `../Agentic-AI-LangChain/build/make_module08.py`, `make_module10.py`,
    `make_capstone.py` : how `write_exercise`, `blank` and `hint` build the skeleton
    and the solution from one source
- `../Presentation-Template/WRITING-STYLE.md` : house style ; it wins

## What one exercise is

- A guide `src/exercises/NN-slug.md`, Marp front matter with `footer:` the module name,
  as ARI510's : a title slide with three or four bullets on the idea, one sentence on
  what the student builds, "Worked examples to revisit : demoNN · slug, ...", the
  notebook to open ; then `### Step N : ...` sections, each with a question to answer ;
  then `### If time permits` with two or three extensions
- `exercises/exerciseNN-slug.ipynb` (skeleton) and `solutions/exerciseNN-slug.ipynb`
  (completed), both from one builder through `nb.write_exercise`. Blanks are `____`
  in the skeleton ; a `hint(...)` cell after a hard blank. Every step ends with a check
  cell that prints whether the behaviour is right
- Data : the Aurelia capstone world in `data/capstone/` (`service.db`, `manuals/`,
  `tickets.csv`, `eval.jsonl`, `untrusted/`). Demos use Veenhaven Bus ; exercises do not
- Size : 30 to 45 minutes for a student who watched the demos. Three to five steps
- The solution notebook is executed against the course model and saved with outputs,
  0 errors. The skeleton is saved without outputs. Check with
  `uv run python build/run_notebook.py solutions/exerciseNN-slug.ipynb`
- Builder : `build/make_exercises_NN_MM.py` for your range, or `build/make_capstone.py`.
  Do not edit the module builders `build/make_moduleNN.py`
- Record each solution run (calls, tokens, seconds, results) in
  `build/measurements-exercises.md` under a heading per exercise, or
  `build/measurements-capstone.md`. Several agents append to the exercises file : add
  your own section only, never rewrite another's

## Not yours

- Slides. The lead adds the exercise and capstone pills to the module summary slides
- `pyproject.toml`, `build/nb.py`, `build/setup_cell.py`. Ask in your report if you
  need a change

## Agent Server ports

Each agent has its own pair ; use only yours, `--no-browser`, and stop the server in
a final cell :

| agent | ports |
| --- | --- |
| exercises 05 to 07 | 2124, 2125 |
| exercises 08 to 11 | 2134, 2135 |
| capstone | 2144, 2145 |

## Report

Files written ; per notebook PASS or FAIL, seconds, calls and tokens ; anything in the
docs that the installed packages do differently ; open questions for the lead.
