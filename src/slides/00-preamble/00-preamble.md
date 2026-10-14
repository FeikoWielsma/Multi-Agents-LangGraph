---
marp: true
theme: spiraltrain
size: 16:10
paginate: true
footer: Multi Agents with LangGraph
pdfName: ARI520-Multi-Agents-LangGraph.pdf
language: python
style: |
  /* Keep dense generated topic lists inside the schedule slide. */
  section .sched-topics:has(li:nth-child(29)) { font-size: 16px !important; }
  section .sched-topics:has(li:nth-child(34)) { font-size: 14px !important; }
---

<!-- _paginate: false _footer: "" -->

# Multi Agents with LangGraph

## Patterns, Communication and Deep Agents

<!-- NOTES:
Welcome to ARI520. Three days : LangGraph as the runtime on day 1, the multi-agent patterns and how agents communicate on day 2, Deep Agents and deployment on day 3.
Ask in the first ten minutes what they build at work and whether they write Python daily. The pivots in build/plan.md depend on the answer.
-->

---
# General Course Remarks

<div style="flex:1;display:flex;flex-direction:column;">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 2em;align-items:center;">
<div style="font-size:1.15em;">

- Course times
- Drinks
- Meals
- Toilettes
- Smoking
- Mobile Phones
- Manual
- Software

</div>
<div>

<em>Everything should be made as simple as possible, but not simpler</em>
<div style="text-align:right;margin-top:0.4em;"><strong>Albert Einstein</strong></div>

</div>
</div>
<div style="margin-top:auto;padding-top:1em;">

<em>Ja, was ich hier geschrieben habe, macht im Einzelnen überhaupt nicht den Anspruch auf Neuheit; und darum gebe ich auch keine Quellen an, weil es mir gleichgültig ist, ob das was ich gedacht habe, vor mir schon ein anderer gedacht hat.</em>
<div style="text-align:right;margin-top:0.4em;"><strong>Ludwig Wittgenstein</strong></div>

</div>
</div>

<!-- NOTES:
Logistics : start and end times, lunch, coffee, restrooms, phones on silent.
Einstein : one agent first ; add a second when a measurement says so.
Wittgenstein : the patterns in this course are the ones the field and the LangChain documentation have settled on.
-->

---
# Lab Environment

- Labs run as Jupyter notebooks on the classroom laptop :
  - `uv sync` installs the pinned stack from `uv.lock`
  - `.env` holds the course key, outside every notebook
  - `uv run jupyter lab` from the repository root
- Course model `gpt-6-luna` through OpenRouter ; no local model needed
- Google Colab runs the same notebooks as a fallback
- `check_setup.py` confirms the stack and the key in under a minute

<!-- NOTES:
Run check_setup.py on the laptop before the participant arrives. It calls the course model and the fallback, so it also proves the venue network reaches OpenRouter.
-->
