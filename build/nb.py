"""Build course notebooks from Python, so their text lives in reviewable source.

    from nb import md, code, write
    write_demo("05-multi-agent-patterns", "demo04-handoffs", [md("..."), code("...")])

Every notebook gets the course setup cell first, tagged `course-setup`, so
build/stamp_setup.py can refresh it everywhere when the cell changes.
"""
import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP_INTRO = ("Run the next cell first. It loads the course key and builds `llm`, "
               "the course model. Nothing below it depends on where the notebook runs.")


def _source(text):
    text = textwrap.dedent(text).strip("\n")
    lines = text.split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": _source(text)}


def code(text, tags=None):
    cell = {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _source(text)}
    if tags:
        cell["metadata"]["tags"] = list(tags)
    return cell


def pins():
    """Runtime pins from pyproject.toml, for the Colab branch of the setup cell."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^dependencies = \[(.*?)^\]", text, re.S | re.M).group(1)
    names = re.findall(r'"([^"]+)"', block)
    return [n for n in names if not n.startswith(("jupyterlab", "ipykernel"))]


def setup_source():
    template = (ROOT / "build" / "setup_cell.py").read_text(encoding="utf-8")
    return template.replace("__PINS__", json.dumps(pins()))


def setup_cells():
    return [md(SETUP_INTRO), code(setup_source(), tags=["course-setup"])]


def hint(text):
    """A collapsed hint : the easy route through an exercise step."""
    body = textwrap.dedent(text).strip("\n")
    return md(f"<details><summary>Hint</summary>\n\n{body}\n\n</details>")


def blank(skeleton, solution):
    """A code cell that differs between the exercise and its solution."""
    return ("blank", skeleton, solution)


def write_exercise(slug, cells):
    """Write exercises/<slug>.ipynb with the blanks and solutions/<slug>.ipynb completed.

    Hint cells appear in the exercise only.
    """
    try:
        from exercise_prerequisites import prerequisite
    except ImportError:
        prerequisite = lambda slug: None
    reference = prerequisite(slug)
    if reference:
        cells = cells[:1] + [md(reference)] + cells[1:]
    skeleton, solution = [], []
    for cell in cells:
        if isinstance(cell, tuple):
            skeleton.append(code(cell[1]))
            solution.append(code(cell[2]))
        else:
            skeleton.append(cell)
            if "<summary>Hint</summary>" not in "".join(cell["source"]):
                solution.append(cell)
    write(f"exercises/{slug}.ipynb", skeleton)
    write(f"solutions/{slug}.ipynb", solution)


def write_demo(module, slug, cells, setup=True):
    """Write notebooks/<module>/<slug>.ipynb, for example ("05-multi-agent-patterns", "demo04-handoffs")."""
    return write(f"notebooks/{module}/{slug}.ipynb", cells, setup=setup)


def section(letter_slug, text=""):
    """A section heading that matches a slide pill : section("b · handoffs-fixed", "One line of prose.")."""
    body = f"## {letter_slug}"
    if text:
        body += "\n\n" + textwrap.dedent(text).strip("\n")
    return md(body)


def write(path, cells, setup=True):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    body = cells[:1] + setup_cells() + cells[1:] if setup else cells
    nb = {"cells": body,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    for i, cell in enumerate(nb["cells"]):
        cell["id"] = f"c{i:03d}"
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
