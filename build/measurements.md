# Measurements

Every number a slide or notebook states, with how it was measured. Newest first.

## Model and pattern probe : 13 October 2026

Stack : `langchain` 1.4.5, `langgraph` 1.2.15, `deepagents` 0.7.24, `openai` 3.29.0,
`langchain-openai` 1.7.1, Python 3.12, through OpenRouter, reasoning effort `none`,
temperature 0. Scripts : `build/probe_reasoning.py`, `check_setup.py`,
`build/probe_patterns.py`. Raw rows : `probe-reasoning-2026-10-13.json`,
`probe-patterns-gpt-6-luna.json`, `probe-patterns-mimo-v2.6-pro.json`.

### Reasoning settings

Both models called the tool correctly under every setting. `reasoning.effort`
`none` and `reasoning.enabled false` both give zero reasoning tokens on both.
Luna reported zero reasoning tokens even at its default on this one-step task ;
MiMo spent 4 to 16. OpenRouter routed Luna to OpenAI and MiMo to DeepInfra.

### `check_setup.py`

7 of 7 on both models. Luna : `create_agent` 2.8 s, structured output 1.3 s, Deep
Agent 3.1 s. MiMo : 31.4 s, 1.4 s, 25.0 s. One run each.

### The five patterns and a Deep Agent

One question that needs a parts lookup and a workshop lookup : "Bus 4012 has a
brake fault and is at depot Noord. Is brake pad BR-220 in stock at Noord, and
when is the next free workshop slot there?" Correct means the answer has the
stock, 6, and the day, Thursday. Three runs per pattern per model ; medians.
`malformed` counts invalid tool calls across all three runs.

Seconds are not model latency : a shared rate limiter held every run to 0.3
requests a second, under OpenRouter's 20 a minute for new accounts. Compare
seconds within a model only, and prefer calls and tokens.

**`openai/gpt-6-luna`**

| pattern | correct | calls | input tokens | output tokens | seconds | malformed |
| --- | --- | --- | --- | --- | --- | --- |
| single agent | 3/3 | 2 | 399 | 96 | 6.7 | 0 |
| subagents | 3/3 | 6 | 781 | 204 | 20.3 | 0 |
| handoffs | 2/3 | 4 | 1,165 | 99 | 13.5 | 0 |
| skills | 3/3 | 4 | 1,036 | 131 | 14.6 | 0 |
| router | 3/3 | 6 | 622 | 184 | 20.6 | 0 |
| custom workflow | 3/3 | 5 | 472 | 129 | 17.0 | 0 |
| Deep Agent, two subagents | 3/3 | 6 | 11,044 | 214 | 20.6 | 0 |

**`xiaomi/mimo-v2.6-pro`**

| pattern | correct | calls | input tokens | output tokens | seconds | malformed |
| --- | --- | --- | --- | --- | --- | --- |
| single agent | 3/3 | 2 | 669 | 94 | 17.6 | 0 |
| subagents | 3/3 | 6 | 1,175 | 215 | 40.1 | 0 |
| handoffs | 2/3 | 4 | 1,215 | 109 | 42.1 | 0 |
| skills | 3/3 | 3 | 1,226 | 132 | 13.8 | 0 |
| router | 3/3 | 6 | 782 | 188 | 65.3 | 0 |
| custom workflow | 3/3 | 5 | 706 | 145 | 45.2 | 0 |
| Deep Agent, two subagents | 3/3 | 6 | 14,461 | 215 | 31.4 | 0 |

The Luna router run first scored as wrong wrote "six" ; the scorer now accepts
the word and the table counts it. The handoff misses : the parts agent answered
its half and ended without transferring (Luna), or dropped the count (MiMo).

What the numbers say, on this question and this data :

- A single agent answered it in 2 calls. Every multi-agent pattern needed 4 to 6
- The Deep Agent read 28 times the input tokens of the single agent, most of it
  its built-in prompt and tool descriptions, for the same answer
- Handoffs were the least reliable pattern on a two-part request, on both models
- No model produced a malformed tool call in 42 runs
- Both full probes, 42 runs each, plus the earlier checks cost $0.0225 together

### Handoffs : two faults in the documented example

The handoff code on `docs.langchain.com/oss/python/langchain/multi-agent/handoffs`
(subgraph variant with `Command.PARENT`), as read on 13 October 2026 :

1. **Parallel tool calls.** When the model called `part_stock` and the transfer
   tool in one turn, the transfer jumped to the other agent and the stock
   result never reached the parent state. The next request carried a tool call
   with no result, and OpenAI and Azure both rejected it : `No tool output found
   for function call`. Fix : `parallel_tool_calls=False` for handoff agents
2. **Lost work.** The transfer forwards only the last AI message. Lookups the
   agent made before handing off vanish, so the next agent repeats them or
   bounces the request back. Observed : parts to workshop to parts, ending with
   half an answer, 3 of 3 runs at effort `none`, `low` and `medium`. Fix :
   forward `runtime.state["messages"]` in the `Command` update

Both fixes are in `build/probe_patterns.py`. Teach the failure first, in demo10.

## Cost so far

| date | what | spent on the key |
| --- | --- | --- |
| 13 October | reasoning probe, `check_setup.py` twice, handoff debugging, two full pattern probes | $0.0225 |

## Stack change, 14 October 2026

Added `deepagents[quickjs]==0.7.24` and `langchain-quickjs==0.3.9` to `pyproject.toml`.
`uv sync` added four packages : langchain-quickjs 0.3.9, quickjs-rs 0.2.5, wasmtime 49.0.0,
bsdiff4 1.2.6. `langchain_quickjs` exports `CodeInterpreterMiddleware` and `PTCOption`.
Reason : module 08 demo05 b (the interpreter) and demo08 a (dynamic subagents) need it ;
without it, `execute` on `StateBackend` only returns a protocol error.
