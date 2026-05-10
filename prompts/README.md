# Prompt Records

These prompt records document the AI collaboration process used to build this browser-agent prototype.

The records are organized in two forms:

- `curated/`: cleaned, reviewer-friendly prompt records. These summarize the purpose, context, constraints, representative prompt text, verification commands, and outcome for each major phase.
- `raw/`: exact or reconstructed prompt excerpts. Each file explicitly labels whether it is an exact raw prompt or a reconstructed representative prompt.

Exactness is labeled per file. Some prompts are reconstructed from the session history, implemented changes, README/docs, and milestone summaries rather than copied from a complete transcript export.

No API keys, BYOK keys, Zeabur tokens, generated logs, or secrets are included.

## Covered Phases

| Phase | Curated | Raw / reconstructed |
| --- | --- | --- |
| Initial scaffold / architecture | `curated/00_project_scaffold.md` | `raw/00_project_scaffold_raw.md` |
| Dataset v1 creation | `curated/01_dataset_v1.md` | `raw/01_dataset_v1_raw.md` |
| Evaluation/reporting v2 | `curated/02_evaluation_reporting_v2.md` | `raw/02_evaluation_reporting_v2_raw.md` |
| LLMPlanner MVP with fake provider | `curated/03_llm_planner_mvp.md` | `raw/03_llm_planner_mvp_raw.md` |
| Available-action-only contract, support preflight, shopping grounding, dashboard prompt injection | `curated/04_available_action_contract.md` | `raw/04_available_action_contract_raw.md` |
| Real-web read-only demo and LLM summarization | `curated/05_real_web_readonly_demo.md` | `raw/05_real_web_readonly_demo_raw.md` |
| BYOK / Zeabur safeguards | `curated/06_byok_zeabur_safeguards.md` | `raw/06_byok_zeabur_safeguards_raw.md` |
| Final docs/report generation | `curated/07_final_docs.md` | `raw/07_final_docs_raw.md` |
