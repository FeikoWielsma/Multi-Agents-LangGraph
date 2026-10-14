"""Probe the pinned stack against the course endpoint.

Run from the repository root before a delivery, and after any change to the pins :

    uv run python check_setup.py

Checks, per model : create_agent with one tool, structured output, a minimal
Deep Agent that calls a tool and writes a file, and that langchain.mcp imports.
Record the result in build/research-2026-10.md when it changes.
"""
import os
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
KEY = os.environ.get("COURSE_API_KEY")
BASE = os.environ.get("COURSE_BASE_URL", "https://openrouter.ai/api/v1")
# The course model first ; the second is the step up, see build/plan.md
MODELS = [os.environ.get("COURSE_MODEL", "openai/gpt-6-luna"), "xiaomi/mimo-v2.6-pro"]
MODELS = list(dict.fromkeys(MODELS))

if not KEY:
    raise SystemExit("COURSE_API_KEY is not set ; copy .env.example to .env")

import deepagents
import langchain
import langgraph.version
import openai
from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

print(f"langchain {langchain.__version__} ; langgraph {langgraph.version.__version__} ; "
      f"deepagents {deepagents.__version__} ; openai {openai.__version__}")


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


class City(BaseModel):
    name: str
    country: str


def check(label, fn):
    start = time.time()
    try:
        detail = fn()
        print(f"  PASS  {label:<18} {time.time() - start:5.1f} s  {detail}")
        return True
    except Exception as exc:
        print(f"  FAIL  {label:<18} {type(exc).__name__}: {str(exc)[:200]}")
        return False


results = []
for model in MODELS:
    print(model)
    llm = ChatOpenAI(model=model, base_url=BASE, api_key=KEY, temperature=0,
                     extra_body={"reasoning": {"effort": "none"}})

    def agent_run():
        out = create_agent(llm, tools=[add]).invoke(
            {"messages": [{"role": "user", "content": "What is 17 + 25? Use the tool."}]})
        kinds = [m.type for m in out["messages"]]
        assert "tool" in kinds, kinds
        return kinds

    def structured_run():
        return llm.with_structured_output(City).invoke("Utrecht is a city in which country?")

    def deep_run():
        out = create_deep_agent(model=llm, tools=[add], system_prompt="Be brief.").invoke(
            {"messages": [{"role": "user", "content":
                "Write a file notes.txt containing the sum of 17 and 25, then say what you wrote."}]})
        files = list(out.get("files", {}))
        assert files, "no file written"
        return files

    results += [check("create_agent", agent_run),
                check("structured output", structured_run),
                check("deep agent", deep_run)]


def mcp_import():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from langchain.mcp import MCPAdapter  # noqa: F401
    return [w.category.__name__ for w in caught][:1]


results.append(check("langchain.mcp", mcp_import))
print(f"{sum(results)} of {len(results)} checks passed")
raise SystemExit(0 if all(results) else 1)
