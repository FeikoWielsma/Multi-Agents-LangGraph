# Module 02 measurements

## Stack verification

- LangGraph version: `1.2.15`, read from the installed package metadata with `importlib.metadata.version("langgraph")` on 13 October 2026.
- Deferred nodes: `inspect.signature(StateGraph.add_node)` on the installed package showed `defer: bool = False`. The `defer=True` example in demo04 ran successfully.
- Conditional routing: `inspect.signature(StateGraph.add_conditional_edges)` showed `path_map: dict | list | None`. Both mapping and list forms ran in the module notebooks.
- Recursion handling: demo03 caught `langgraph.errors.GraphRecursionError` after invoking a deliberately unbounded cycle with `recursion_limit` set to `2`.

## Notebook execution

The six module notebooks were run with `COURSE_RPS=0.02` on 13 October 2026. Demos 01 to 05 are deterministic and use no model. Demo06 is the only notebook that calls the course model. Its saved output routed the electrical work order to the electrical bay. No model performance or token count is claimed in this module.

## Counts and timing

- Slide count: 26, counted from level-one Markdown slide headings in `02-graph-fundamentals.md` on 13 October 2026.
- Notebook count and sections: six notebooks and the 13 sections listed in `build/course-map.md`; checked against the generated notebook headings on 13 October 2026.
- The opening note gives an estimated 55-minute module slot for six demos. This is a course planning estimate, not an observed delivery time.
