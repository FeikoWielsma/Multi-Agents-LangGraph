# AGENTS.md : ARI520 Multi Agents with LangGraph

Instructions for coding agents working in this repository.

## Read first

- `build/plan.md` : the decisions, the module plan, the capstone, the build order
- `build/research-2026-10.md` : the October 2026 survey ; multi-agent patterns, the stack, the industry view
- `../Agentic-AI-LangChain/build/research-2026.md` : the September survey this one builds on
- `../Presentation-Template/WRITING-STYLE.md` : house style for slides, exercises and notebooks. It wins over this file

## Relation to ARI510

`../Agentic-AI-LangChain` is ARI510, built and published. Its modules 08, 10, 11
and 12, its capstone data and its build tooling are the source for most ported
material. Copy from it ; never edit it from here.

## Layout

```
src/slides/NN-slug/NN-slug.md   Marp slides, one module per folder, footer = module name
src/exercises/NN-slug.md        exercise guides, built into the exercises PDF
notebooks/NN-module/            demo notebooks, one folder per module, committed with outputs
exercises/  solutions/          skeleton and completed exercise notebooks
data/                           course datasets
build/                          plan, research, package.json shim, builders ; never shipped
```

## Commands

```bash
uv sync --group server                     # Python environment from uv.lock
uv run python check_setup.py               # probe the stack against the course endpoint
bun run --cwd build lint                   # slide height and house style
bun run --cwd build build                  # slides PDF
bun run --cwd build build -- --exercises   # exercises PDF
```

## Rules for the stack

- Versions are pinned in `pyproject.toml` and locked in `uv.lock`. Upgrade only on
  purpose, re-run `check_setup.py`, and record the result in `build/`
- Multi-agent through the documented patterns : subagents, handoffs, skills, router,
  custom workflow. `langgraph-supervisor` and `langgraph-swarm` appear only as history
- Every pattern is built from LangGraph primitives before a harness hides it
- MCP through `langchain.mcp`, never `langchain-mcp-adapters`
- The course model is `openai/gpt-6-luna` through OpenRouter, with reasoning off ;
  `xiaomi/mimo-v2.6-pro` is the step up. Every call goes through the shared rate
  limiter in the setup cell ; `COURSE_RPS` sets its budget

## Rules for content

- A number in prose is measured, and the measurement is recorded in `build/`
- `Verified` means executed against the course endpoint. A notebook that parses is not verified
- Industry claims cite a primary source ; secondary sources stay in `build/`
- Borrow structure and ideas from LangChain Academy freely. Adapt code only from
  MIT-licensed repositories, with attribution in the notebook
- Never put a key in a notebook, a slide or a commit
