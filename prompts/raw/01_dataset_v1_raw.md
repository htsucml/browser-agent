# 01 Dataset v1 Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: Dataset v1 phase
- Purpose: Create deterministic M1 benchmark cases
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

We are moving from the initial scaffold to Dataset v1 for the browser-agent assignment.

Goal: create Dataset v1, a compact M1 benchmark with 12-13 deterministic simulated cases covering core browser-agent capabilities.

Do not implement a complex LLM agent. Do not make broad architecture rewrites. Do not break the existing smoke eval. It is acceptable if the current rule-based planner fails new v1 cases, as long as the evaluator runs all cases and reports deterministic results.

Dataset v1 should test:

1. normal daily task completion
2. search/filter/compare constraint satisfaction
3. long-horizon annoying task
4. fake-success / silent-failure trap
5. selector drift / self-maintenance
6. modal blocking / self-correction
7. safe settings change
8. unsafe destructive action requiring needs_user
9. vague instruction requiring needs_user
10. support form filling
11. validation error diagnosis
12. dashboard table extraction/comparison
13. prompt-injection resistance

Add `evals/cases_v1.json` and keep `evals/cases.json` as smoke. Extend simulator pages for shopping, settings, support, and dashboard. Add deterministic state-based checkers such as cart contains matching item, wishlist cheapest matching, settings state equals, support ticket contains, dashboard row state equals, trace contains event, and forbidden action not taken.

Acceptance:

- `python3 -m pytest -q` passes.
- `python3 -m evals.run_eval --cases evals/cases.json` passes.
- `python3 -m evals.run_eval --cases evals/cases_v1.json` runs all v1 cases and writes reports.
