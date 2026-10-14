"""Which reasoning settings each candidate model accepts on OpenRouter, and what they cost.

    uv run python build/probe_reasoning.py

One tool-calling request per model and setting, raw `openai` client. Prints
latency, reasoning tokens, and whether the model called the tool.
"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = OpenAI(base_url=os.environ["COURSE_BASE_URL"], api_key=os.environ["COURSE_API_KEY"])

MODELS = ["openai/gpt-6-luna", "xiaomi/mimo-v2.6-pro"]
SETTINGS = {
    "default": {},
    "effort none": {"reasoning": {"effort": "none"}},
    "effort minimal": {"reasoning": {"effort": "minimal"}},
    "effort low": {"reasoning": {"effort": "low"}},
    "enabled false": {"reasoning": {"enabled": False}},
}
TOOLS = [{
    "type": "function",
    "function": {
        "name": "part_stock",
        "description": "Units in stock for a part number at a depot.",
        "parameters": {
            "type": "object",
            "properties": {"part": {"type": "string"}, "depot": {"type": "string"}},
            "required": ["part", "depot"],
        },
    },
}]
QUESTION = "How many units of part BR-220 are in stock at depot Noord? Use the tool."

rows = []
for model in MODELS:
    for label, extra in SETTINGS.items():
        start = time.time()
        try:
            r = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": QUESTION}],
                tools=TOOLS, temperature=0, extra_body=extra, timeout=120)
            u = r.usage
            details = getattr(u, "completion_tokens_details", None)
            reasoning = getattr(details, "reasoning_tokens", None) if details else None
            calls = r.choices[0].message.tool_calls or []
            args = calls[0].function.arguments if calls else ""
            rows.append(dict(model=model, setting=label, ok=True, s=round(time.time() - start, 1),
                             prompt=u.prompt_tokens, completion=u.completion_tokens,
                             reasoning=reasoning, tool=bool(calls), args=args,
                             provider=getattr(r, "provider", None)))
        except Exception as exc:
            rows.append(dict(model=model, setting=label, ok=False, s=round(time.time() - start, 1),
                             error=f"{type(exc).__name__}: {str(exc)[:160]}"))
        print(json.dumps(rows[-1]))

out = Path(__file__).with_name("probe-reasoning-2026-10-13.json")
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
