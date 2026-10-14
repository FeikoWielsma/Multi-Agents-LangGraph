"""Refresh the course setup cell in every notebook from build/setup_cell.py.

    uv run python build/stamp_setup.py            # report
    uv run python build/stamp_setup.py --write    # rewrite changed notebooks

The setup cell is found by its `course-setup` tag. Outputs of a refreshed cell
are cleared ; re-run the notebook afterwards.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb import ROOT, _source, setup_source

write = "--write" in sys.argv
body = _source(setup_source())
changed = 0
for path in sorted(p for folder in ("notebooks", "exercises", "solutions")
                   for p in (ROOT / folder).rglob("*.ipynb") if "checkpoint" not in str(p)):
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if "course-setup" in c.get("metadata", {}).get("tags", [])]
    if not cells:
        print("no setup cell :", path.relative_to(ROOT))
        continue
    if cells[0]["source"] == body:
        continue
    cells[0]["source"] = body
    cells[0]["outputs"] = []
    cells[0]["execution_count"] = None
    changed += 1
    print(("wrote   " if write else "stale   ") + str(path.relative_to(ROOT)))
    if write:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{changed} notebook(s) {'updated' if write else 'out of date'}")
