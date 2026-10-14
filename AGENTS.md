# AGENTS.md : ARI520 Multi Agents with LangGraph

Instructions for coding agents working in this repository.

## Status

Built and executed on 14 October 2026 for the delivery of 2 to 4 November 2026 :
slides 00 to 10, 67 demo notebooks, exercises 01 to 11, capstone stages 1 to 5,
both PDFs. What is left, and the decisions taken during the build, are in the
"Status" section at the end of `build/plan.md`. Read it before changing anything.

## Read first

- `build/plan.md` : the decisions, the module plan, the capstone, the days, the status
- `build/course-map.md` : every demo notebook and section, exercise and capstone stage
- `build/research-2026-10.md` : the October 2026 survey ; multi-agent patterns, the stack, the industry view
- `build/measurements.md` and `build/measurements-*.md` : every measured number, and
  where the installed packages differ from the docs. Append ; do not rewrite history
- `../Agentic-AI-LangChain/build/research-2026.md` : the September survey this one builds on
- `../Presentation-Template/WRITING-STYLE.md` : house style for slides, exercises and notebooks. It wins over this file

To change a module, also read `build/BUILD-BRIEF.md` ; to change an exercise or the
capstone, `build/EXERCISE-BRIEF.md`.

## Relation to ARI510

`../Agentic-AI-LangChain` is ARI510, built and published. Its modules 08, 10, 11
and 12, its capstone data and its build tooling are the source for most ported
material. Copy from it ; never edit it from here.

## Layout

```
src/slides/NN-slug/NN-slug.md   Marp slides, one module per folder, footer = module name
src/exercises/NN-slug.md        exercise guides (00 setup, 01 to 11, 99 capstone), built into the exercises PDF
notebooks/NN-module/            demo notebooks, one folder per module, committed with outputs
exercises/  solutions/          skeleton and completed exercise and capstone notebooks ; only .ipynb is committed
data/demo-world/                Veenhaven Bus, for the demos
data/capstone/                  Aurelia Imaging Systems, for the exercises and the capstone
build/                          plan, research, measurements, briefs, builders ; never shipped
```

Notebooks are generated, never edited by hand : `build/make_moduleNN.py` writes the
demos, `build/make_exercises_01_04.py`, `_05_07.py`, `_08_11.py` and
`build/make_capstone.py` write the exercises and capstone, all through `build/nb.py`.
The setup cell comes from `build/setup_cell.py` ; `build/stamp_setup.py` refreshes it
in every notebook. Notebooks that serve agents write their own server files at run
time ; those are gitignored.

## Commands

```bash
uv sync --group server                                  # Python environment from uv.lock
uv run python check_setup.py                            # probe the stack against the course endpoint
uv run python build/make_module05.py                    # regenerate one module's notebooks (outputs are lost)
COURSE_RPS=0.1 uv run python build/run_notebook.py notebooks/05-*/demo04-*.ipynb   # execute and save
uv run python build/show_outputs.py <notebook>          # read the outputs
bun run --cwd build lint                                # slide height and house style, all decks
bun run --cwd build build                               # slides PDF
bun run --cwd build build -- --exercises                # exercises PDF
```

Agent Server notebooks use fixed port pairs : module 06 and exercises 05 to 07 use
2124 and 2125, module 09 and exercises 08 to 11 use 2134 and 2135, the capstone 2144
and 2145. On Windows, lint can fail with `EBUSY` while another lint holds the browser
profile ; wait and rerun.

## Rules for the stack

- Versions are pinned in `pyproject.toml` and locked in `uv.lock` : LangGraph 1.2.15,
  LangChain 1.4.5, Deep Agents 0.7.24 with `langchain-quickjs` 0.3.9, langgraph-api
  0.16.0. Upgrade only on purpose, re-run `check_setup.py` and every notebook, and
  record the result in `build/`. The stack freezes about 27 October
- Multi-agent through the documented patterns : subagents, handoffs, skills, router,
  custom workflow. `langgraph-supervisor` and `langgraph-swarm` appear only as history
- Every pattern is built from LangGraph primitives before a harness hides it
- MCP through `langchain.mcp`, never `langchain-mcp-adapters`
- The course model is `openai/gpt-6-luna` through OpenRouter, with reasoning off ;
  `xiaomi/mimo-v2.6-pro` is the step up. Every call goes through the shared rate
  limiter in the setup cell ; `COURSE_RPS` sets its budget. The account allows 20
  requests a minute per model : keep the sum of all running agents' budgets under 0.3
- LangSmith is the EU region (`LANGSMITH_ENDPOINT` in `.env`) ; tracing is off by default

## Rules for content

- A number in prose is measured, and the measurement is recorded in `build/`
- `Verified` means executed against the course endpoint. A notebook that parses is not verified
- Industry claims cite a primary source ; secondary sources stay in `build/`
- Borrow structure and ideas from LangChain Academy freely. Adapt code only from
  MIT-licensed repositories, with attribution in the notebook. The Academy's
  `lca-deepagents` repository has no licence : ideas only, no text or code
- Yair (@finebutwhy) gave permission to quote his crew posts ; quote them verbatim
- Never put a key in a notebook, a slide or a commit. Keys live in `.env`, which is gitignored

## Remotes

`origin` is Forgejo `SpiralTrain/Multi-Agents-LangGraph`, which builds and releases
the PDFs on every push to `main` (`.forgejo/workflows/release.yml`). `github` is the
public mirror the Colab setup cell downloads data from. Push both.
