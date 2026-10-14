# Module 06 measurements

Date : 14 October 2026. Model : `openai/gpt-6-luna` through OpenRouter, temperature 0, reasoning effort `none`. Notebooks set `COURSE_RPS=0.06`, `max_tokens=500` and `max_retries=0`. Installed versions, from `importlib.metadata` : Python 3.12.13, `langchain` 1.4.5, `langgraph` 1.2.15, `langgraph-cli` 0.4.33, `langgraph-api` 0.16.0, `deepagents` 0.7.24.

The notebook `Counter` counts `on_chat_model_start` and sums `usage_metadata` from `on_llm_end` on the notebook's own `llm`. Seconds are wall time from that cell to `finish_metrics`, including the rate limiter. They are not model latency. Model calls inside `langgraph dev` do not reach this counter.

Inventory is a read-only query of `data/demo-world/service.db`. Every notebook that prints `FACTS` or a parts answer reports CE-CF-02, traction cooling fan, stock 6, 420 euro, depot Rietpoort. The manuals line used for F-CE-110 is from `ce-12-error-codes.md` : check the traction cooling fan, and replace it if airflow is below 80 percent. CE-DA-03, returned by the served parts graph, is stock 0 at Rietpoort. No row is updated.

## Notebook counters

| Notebook | Calls | Input tokens | Output tokens | Seconds |
| --- | --- | --- | --- | --- |
| demo01 what agents share | 7 | 871 | 315 | 118.9 |
| demo02 subgraph communication | 4 | 326 | 176 | 68.5 |
| demo03 served agents | 0 | 0 | 0 | 42.1 |
| demo04 two agents over A2A | 0 | 0 | 0 | 66.5 |
| demo05 events and synchronisation | 1 | 55 | 32 | 18.0 |
| demo06 conflicts | 4 | 564 | 134 | 68.2 |
| demo07 buyer and seller | 6 | 702 | 153 | 101.4 |

Demo01's seven calls are the shared-state report, the envelope note, four context boundaries, and the summary returned to the caller. The per-context input tokens printed on the replies are 149 (full history), 115 (task only), 162 (fork) and 136 (summary). The task-only answer states stock and depot and does not state the first action. The full-history, fork and summary answers include the fan check and the 80 percent condition. Wording is one sample.

Demo02's four calls are the parts reply, the parent manuals reply, the shared-key report and the mapped report. The parent receiver list contains the stock note (6 at Rietpoort). The written answer then says it does not have the stock or location. `working_note` is absent from the parent result (`private key returned : False`). The mapped child input is only `part_no`.

Demo05's one call is the stock sentence. The v3 projection uses a deterministic child and makes no model call. The child namespace is `parts:` plus a generated id. Custom events `lookup-started` and `lookup-finished` appear beside the update and are not keys of the returned state. Both broadcast readers see the same snapshot, stock 6 at Rietpoort. Both the plain join and the deferred collector print `collected : ['manuals', 'parts']`.

## Agent Server and A2A

Servers were `langgraph dev` on 127.0.0.1 ports 2124 and 2125, with `--no-browser`, `--no-reload` and `--allow-blocking`. Each notebook stops them in its last cell. `servers stopped : True` is printed for demo03 and demo04.

The keyless subprocess removes `LANGSMITH_*` and `LANGCHAIN_*`, then sets `LANGSMITH_TRACING=false`. It serves the echo graph. The notebook prints `metadata loop skipped : True`, `EU metadata endpoint : False`, and Studio `https://smith.langchain.com/studio/`. `POST /runs/wait` with assistant id `echo` returns `local echo`. A2A `SendMessage` to the echo UUID returns `TASK_STATE_COMPLETED` and the text `local echo`. A LangSmith key is not required to serve the graph or to complete that task.

The parts server inherits the repository environment, tracing left off. The notebook prints `metadata loop skipped : False` and `EU metadata endpoint : True`. The surviving log names `https://eu.api.smith.langchain.com/v1/metadata/submit` and a 204 response. The Studio banner stays `https://smith.langchain.com/studio/`. This pass did not start a server with tracing turned on.

`POST /runs/wait` accepts the graph id `parts`. Its printed usage is 65 input tokens and 19 output tokens, and the answer is CE-CF-02 stock 6 at Rietpoort.

On `langgraph-api` 0.16.0 the card and the A2A path do not accept that graph id. Docs and `build/research-2026-10.md` section 3 describe `/.well-known/agent-card.json?assistant_id=...` and `/a2a/{assistant_id}`. With `assistant_id=echo` the card returns HTTP 400 and `Invalid assistant ID: must be a UUID`. `POST /a2a/echo` returns the same message. `POST /assistants/search` returns one UUID per graph id, and it matches `uuid5` of the graph id with namespace `6ba7b821-9dad-11d1-80b4-00c04fd430c8` :

| Graph id | Assistant UUID |
| --- | --- |
| echo | 046b5dc7-2108-582c-9c6c-31d556d138f0 |
| parts | b67dba3b-3342-5f55-b1fe-bdcc570cc1a4 |
| coordinator | 1e63a636-5cd8-5425-94a1-d65cc0913fbc |

The parts card reports `protocolBinding` JSONRPC, `protocolVersion` 1.0, `supportsA2A` true, and card `version` 0.16.0. The default history scope in the card extension is `context`. The card has no credential field.

`SendMessage` returns `result.task` with `status.state` `TASK_STATE_COMPLETED`, artifacts, and the CE-DA-03 answer (stock 0 at Rietpoort). `GetTask` returns the task itself. Its keys omit `artifacts`. Its status text is `Task completed successfully`. `contextId` is the thread id : `GET /threads/{contextId}/state` returns the same answer. A `contextId` of `BW-7001` returns `Failed to create run: Invalid thread ID`.

Demo04 runs the coordinator on 2124 and the parts specialist on 2125. The coordinator's own usage is 76 input and 36 output tokens. The specialist thread's usage for that first task is 72 input and 35 output tokens. The context ids match and the task ids differ. `message/send` returns the task unwrapped, with `status.state` `completed`. After that second turn, `GetTask` history length is 4 with the default scope and 2 with `historyScope` `task`. The follow-up answer says CE-DA-03 is out of stock. The notebook counter stays at 0 because those calls run in the server processes. The follow-up's tokens are not in the printed usage dicts.

## Conflicts and settlement

Two writes to an unreduced `decision` raise `InvalidUpdateError`. The first line is `At key 'decision': Can receive only one value per step. Use an Annotated key to handle multiple values.` The reduced list keeps both proposals, buyer `retain` and seller `sell`.

The vote is to sell four CE-CF-02 from stock 6 with reserve 4. All three roles returned `retain`. Counts are sell 0, retain 3. That is one sample. The slide does not treat a unanimous vote as a property of the model. The judge also returned `retain`. The code results are `('retain', 'retain on tie')` for one sell and one retain, and `('retain', 'reserve invariant')` for two sell votes of quantity 4.

Demo07 proposals in this run : buyer quantity 4, seller quantity 2. Settlement is sell 2, retain 4, `external_action` false. The seller tool result is a draft sale of two CE-CF-02. The buyer tool result is a draft purchase of one CE-DA-03. Both schemas list only `quantity`. `authorise` on the seller principal with `draft-purchase` raises `Operation outside this principal's scope.`

## Accuracy and prose review

Reviewed 14 October 2026 against the installed packages and every committed notebook output. `importlib.metadata.version` also reports `langgraph-sdk` 0.4.7. All seven notebooks have execution counts for every code cell and zero stored error outputs. This review changed no notebook code and made no model calls ; the counters above remain the original run at `COURSE_RPS=0.06`. Any review rerun must use `COURSE_RPS=0.03` and only ports 2124 and 2125.

The reviewed deck has 28 slides, 28 source-bearing speaker notes and 17 demo pills. The pill text and order are unchanged. Excluding notes and fenced code, the deck has 131 top-level bullets and zero lead-ins with exactly one sub-bullet, a lead-in share of 0 percent. The opening speaker note allocates about 70 minutes of teaching time ; this is a trainer budget, not a measured execution duration.

Additional numeric evidence from the existing outputs :

- Demo01 prints parent history length 3 and copied fork history length 4.
- Demo03's native usage totals 84 tokens, from 65 input and 19 output tokens. `ListTasks` prints one task for the new parts context.
- Demo04's first coordinator call totals 112 tokens, from 76 input and 36 output tokens. The first specialist call totals 107 tokens, from 72 input and 35 output tokens. These are server-side calls, not the notebook counter.
- The voting proposal leaves stock 2 when four units are sold from stock 6 ; reserve 4 rejects that sale. The fixed tied pair has one vote per action. The override example supplies two sell votes.

Numeric settings in the module's own code are inputs, not measurements. The shared module cell sets `max_tokens=500`, `max_retries=0` and `recursion_limit=16`. Demo07's proposal schema allows quantities from 0 through 6 for this six-unit inventory example. Server startup allows 90 seconds, probes with a 3-second timeout every 0.5 seconds, and waits up to 20 seconds during shutdown. Assistant searches request limits of 50 in the notebook helper and 20 in the coordinator. Other HTTP timeouts are 30 and 180 seconds. The coordinator delay is `1 / COURSE_RPS` seconds between specialist and coordinator model requests. Python, package, JSON-RPC 2.0, A2A 1.0 and stream v2/v3 labels identify versions ; they are not measured counts. Bus, part, error and case numbers identify records.

Accuracy corrections and their evidence :

- `historyScope="task"` selects the requested task's response history. It does not select the latest task or restrict model input history. Source : installed `langgraph_api/api/a2a.py`, `handle_tasks_get`, `_get_historical_messages_for_task` and `_convert_messages_to_a2a_format`. Demo04 requests the follow-up task, which explains the two returned history entries. Its markdown and matching builder text were corrected ; code and outputs were preserved.
- `resolve` selects the majority with retain on tie, then checks a selected sale against the reserve. The model judge's result is printed separately and is not an input to `resolve`. Source : demo06 c.
- `settle` caps the buyer's retention request at available stock, takes the greater of that request and the reserve, and caps the sale at the remaining surplus and the seller's proposal. Source : demo07 a. The shown stock exceeds the reserve ; the function does not replenish a reserve that is already deficient.
- Default graph assistants use `uuid5` ; custom assistant UUIDs need not derive from graph names. A2A checks UUID syntax and a `messages` input property. Sources : installed `langgraph_api/graph.py` and `langgraph_api/api/a2a.py`. The completed-task response shapes on the slides match demo03 and demo04 ; they do not promise completion for every request.
- The keyless echo and environment-inheriting parts servers are separate runs. The Studio host is an observation of both tracing-off runs, not an established rule for tracing-enabled configurations. Source : demo03 outputs.
- Child v3 projection iteration can drive the root graph pump. Consuming children inside discovery is the notebook's consumption pattern, not a parent scheduling barrier. Source : installed `langgraph/stream/run_stream.py`.
- List-edge joins and deferred collectors are alternative constructions in demo05 d. The slide now shows their different edges separately.
- In-process agents may share process credentials ; separate servers require configured identities. Shared browser logins expose authenticated services, without establishing that every unrelated credential on the computer is accessible. The demo uses synthetic scopes and code authorisation. Sources : demo07 b and research section 5.

Remaining source limitation : research section 5 records Yair's public post, exact quote and permission, but no stable post URL. The slide cites that record and attributes the quote to @finebutwhy ; no URL was invented. The visible quote matches `a conflict of interest i've chosen to ignore` exactly.

The local annotation probe reproduced `ValueError: Found edge ending at unknown node \`manuals\`` when the child handoff is annotated `Command[Literal["manuals"]]`. It uses no model or server. The slide retains the unannotated notebook function. The required slide lint passes with `All slides within budget.` No PDF build was run.
