# 04 Available-Action Contract

## Purpose

Make LLM action selection robust by grounding model decisions in stable available action IDs.

## Context

Early real-key smoke tests showed model outputs could choose fuzzy or wrong selectors, such as a red-shoes button for a USB-C hub task. The verifier caught the failure, but execution needed stronger pre-mutation validation.

## Key Constraints

- Do not hardcode case IDs.
- Do not weaken evaluator checks.
- Do not add endless semantic action aliases.
- Unknown or wrong action IDs must fail safely before mutation.
- Missing required information should return `needs_user`.
- Webpage prompt-injection text is untrusted observation.

## Representative Prompt

Refactor LLMPlanner output toward available-action-only selection. If `available_actions` are provided, the model must return `decision=act` and a valid `action_id`. Add compact shopping/support/dashboard observations, support-form fill contracts, missing-info preflight, shopping wishlist grounding, and prompt-injection-resistant dashboard actions.

## Verification Commands

```bash
python3 -m pytest -q
PLANNER=llm LLM_PROVIDER=fake python3 -m evals.run_eval --cases evals/cases_llm_smoke.json
python3 -m evals.run_ablation --cases evals/cases_llm_dev.json --configs rule,llm_fake
```

## Result

LLMPlanner can solve validated settings, shopping compare, support validation/form, dashboard table, and dashboard prompt-injection cases through stable action IDs and deterministic validation.
