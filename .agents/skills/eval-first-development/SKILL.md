# Eval-First Development

Use this skill before adding browser-agent behavior.

## Workflow

1. Add or update a deterministic case in `evals/cases.json`.
2. Add checker support in `evals/checkers.py` if needed.
3. Confirm the evaluator can fail before implementation.
4. Implement the smallest runtime behavior.
5. Run `python -m evals.run_eval --cases evals/cases.json` and `pytest -q`.

## Guardrails

- No LLM-as-judge.
- No hidden network dependency.
- Cases should cover varied domains and task types over time.
- False success must be measurable.
