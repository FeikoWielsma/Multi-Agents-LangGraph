# Notes : LangChain Academy, Introduction to Deep Agents

Read 13 October 2026 from `github.com/langchain-ai/lca-deepagents`, the course's
public repo : lesson pages in `thinkific/src`, code in `python/`. No licence
file, so all rights reserved. These notes record structure and ideas in our own
words. Copy no lesson text, diagram or code ; write ours against our stack and
data. Its stack : `deepagents` 0.7.0, `langchain-mcp-adapters`, Claude Haiku 4.5
by default, OpenRouter and Ollama as alternatives, EU LangSmith endpoint noted.

## Shape

| module | lessons | words | ARI520 |
| --- | --- | --- | --- |
| 1 Building | overview, running, models, system prompt and caching, tools, MCP, threads and checkpointers, HITL, a judge-persona practice | about 39K | 08 opening, compressed : days 1 and 2 cover most |
| 2 Execution environment | environment, filesystem backends and permissions, sandboxes and local shell, interpreter | about 17K | 08 |
| 3 Context management | summarisation and offloading, skills, memory | about 16K | 08 |
| 4 Delegation | delegation, a subagent team, dynamic subagents | about 21K | 05 and 08 |
| 5 Putting it together | the sales assistant, local deployment, async subagents, sandboxed advanced version | about 20K | 08 capstone stage, 09 |
| 6 Managed Deep Agents | what it is, project layout and deploy | about 5K | 09, one slide |

Their order is single-agent harness first, delegation in module 4. Ours builds
the patterns by hand on day 2 and reaches Deep Agents on day 3. Keep ours.

## Ideas worth taking

**The capstone shape (module 5).** A sales assistant over the Chinook database.
Each specialist subagent owns one resource : an analyst owns the database, an
inbox manager owns mail through a mock MCP server, a reviewer checks quotes, a
researcher fans out once per genre. Skills are playbooks, one per task. The
interpreter does the quote arithmetic exactly. HITL gates the two consequential
actions. A plain-text `AGENTS.md` is the operating manual. Our stage 4 can take
the same shape on Aurelia : a parts analyst owning `service.db`, a ticket agent
owning tickets behind our own MCP server, an order reviewer, skills for the
service procedures, the interpreter for order totals, approval on orders and on
mail to a hospital.

**Orchestration patterns for many subagents (4.3).** Six named shapes for
dynamic subagents : classify and act, fan-out and synthesise, adversarial
verification, generate and filter, tournament, loop until done. Each with when
it fits. Belongs on the collaboration slides in 05, next to maker-checker and
debate, and in 08 under dynamic subagents. Our wording, our examples.

**When to use dynamic subagents.** Many units of work, or a count known only at
runtime ; a guarantee that every unit is covered ; orchestration the model
would otherwise rebuild every turn. A plain team for a few fixed roles. The loop
in code is the guarantee, not the model's memory : a good line for 05 and 08.

**Recursive language models.** Split a long input, call each part, combine,
recurse. Zhang, Kraska and Khattab, MIT CSAIL, `arxiv.org/abs/2512.24601`. One
slide in 08 ; read the paper before writing it.

**When to reach for a subagent, and when not (4.1).** Use one for cluttering
multi-step work, a specialised domain, a different model, or to keep the main
agent coordinating. Skip it for single-step tasks and when the intermediate
context must stay. Matches our thesis ; cite the docs page, not the lesson.

**Scoped scratch folders (4.2).** Researchers may write only under their own
folder ; the editor may read it but not write. Filesystem permissions per
subagent. Pairs with Yair's shared logins on the least-privilege slide in 06.

**Sandbox return channel (5.5).** Errors from a sandbox must reach the agent so
it can correct itself, so that channel carries untrusted text : an injected
"send the API key" riding on a real error. Their answer : put the whole
filesystem inside the sandbox, keep secrets out of it, and extract results by a
non-agentic path. A security slide in 09, and a demo candidate.

**Two deployments, one supervisor (5.4).** The async lab : two `langgraph.json`
projects, a supervisor launching and checking a specialist on the other. Same
shape as our exercise11 ; confirms it is feasible locally.

**Memory isolation between users (3.3).** A lab proving one user cannot read
another's memory. A candidate for 03 or 08 with the `Store` namespaces.

**Prompt caching lab (1.4).** Shows cached tokens in the trace. Luna reports
cache reads on OpenRouter at $0.01 per 1M ; a cost slide in 09 could measure it.

## Not taken

- Their Python script layout : we use notebooks
- Personas (pirate, cowboy) : below the level of day 3
- The TypeScript track
