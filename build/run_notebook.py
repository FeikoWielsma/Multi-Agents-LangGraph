"""Execute course notebooks in place against the live endpoint and keep the outputs.

    uv run python build/run_notebook.py notebooks/demo04a-create-agent.ipynb [more ...]
    uv run python build/run_notebook.py --colab notebooks/demo04a-create-agent.ipynb
    uv run python build/run_notebook.py --check solutions/*.ipynb      # run, do not save

Each notebook runs with its own folder as the working directory. `--colab`
fakes `google.colab` so the setup cell takes the Colab branch ; the key still
comes from .env. Errors are listed per cell, then a summary line per notebook.
"""
import os
import argparse
import json
import sys
import time
from pathlib import Path

import nbformat
from dotenv import load_dotenv
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--colab", action="store_true")
parser.add_argument("--check", action="store_true")
parser.add_argument("--workdir", type=Path, help="Isolated runtime folder for this batch")
parser.add_argument("--report", type=Path, help="Write execution results as JSON")
parser.add_argument("paths", type=Path, nargs="+")
args = parser.parse_args()
colab, check, paths = args.colab, args.check, args.paths
if args.workdir:
    args.workdir.mkdir(parents=True, exist_ok=True)

failed = 0
reports = []
for path in paths:
    nb = nbformat.read(path, as_version=4)
    if colab:
        fake = nbformat.v4.new_code_cell(
            "import sys, types, os\n"
            "m = types.ModuleType('google.colab')\n"
            "m.userdata = types.SimpleNamespace(get=lambda k: os.environ[k])\n"
            "sys.modules['google.colab'] = m\n"
            "os.environ['COURSE_SKIP_INSTALL'] = '1'   # the uv venv has no pip\n")
        nb.cells.insert(0, fake)
    start = time.time()
    stopped = None
    client = NotebookClient(nb, timeout=900, kernel_name="python3", allow_errors=True,
                            resources={"metadata": {"path": str(
                                args.workdir.resolve() if args.workdir else path.resolve().parent)}})
    try:
        client.execute()
    except Exception as exc:            # a cell timeout or a dead kernel : keep the partial run, go on
        print(f"  execution stopped : {type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
        stopped = type(exc).__name__
        failed += 1
    if colab:
        nb.cells.pop(0)
    errors = []
    for i, cell in enumerate(nb.cells):
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                errors.append(f"  cell {i}: {out['ename']}: {out['evalue'][:300]}")
    if not check and not colab:
        nbformat.write(nb, path)
    print("\n".join(errors))
    elapsed = round(time.time() - start, 1)
    status = "FAILED" if errors or stopped else "PASS"
    print(f"{path.name}: {status}, {len(errors)} errors, {elapsed:.0f} s")
    reports.append({"notebook": path.as_posix(), "status": status, "errors": len(errors),
                    "stopped": stopped, "seconds": elapsed, "colab": colab})
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    failed += bool(errors)

sys.exit(1 if failed else 0)
