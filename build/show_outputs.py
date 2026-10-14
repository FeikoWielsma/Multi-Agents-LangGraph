"""Print the non-setup outputs of executed notebooks : uv run python build/show_outputs.py NB [NB ...]"""
import json
import sys

for f in sys.argv[1:]:
    nb = json.load(open(f, encoding="utf-8"))
    print("=====", f)
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code" or "course-setup" in c.get("metadata", {}).get("tags", []):
            continue
        parts = []
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                parts.append(f"ERROR {o['ename']}: {o['evalue'][:300]}")
            else:
                parts.append("".join(o.get("text", "")) or "".join(o.get("data", {}).get("text/plain", "")))
        text = "\n".join(l for l in "\n".join(parts).splitlines() if l.strip() and "Warning" not in l)
        if text:
            print(f"[{i}] {text[:700]}")
