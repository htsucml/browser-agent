# 02 Evaluation Reporting v2

## Purpose

Improve reporting so results are readable and refusal/needs-user cases are correctly counted.

## Context

`verified_success` alone made expected `needs_user` cases look like failures. The reports also needed ablation comparison, clearer action/SPL metrics, dataset split scaffolding, and deterministic failure analysis.

## Key Constraints

- Do not add agent capabilities.
- Do not change Dataset v1 semantics.
- Do not weaken verifier/evaluator checks.
- Do not add LLM-as-judge.

## Representative Prompt

Implement evaluation/reporting v2 with a user-facing result summary, unified ablation runner, clearer SPL/action metrics, dataset split scaffolding, and deterministic failure-analysis report. Add `task_passed = verified_success OR correct_refusal` and make markdown/ablation reports show task-passed and correct-refusal metrics clearly.

## Verification Commands

```bash
python3 -m pytest -q
python3 -m evals.run_eval --cases evals/cases_dev.json
python3 -m evals.run_ablation --cases evals/cases_llm_smoke.json --configs rule,llm_fake
```

## Result

Added task-passed metrics, readable display summaries, ablation reports, dataset split files, and deterministic failure-analysis grouping.
