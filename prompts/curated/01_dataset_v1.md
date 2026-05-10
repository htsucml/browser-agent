# 01 Dataset v1

## Purpose

Create a compact deterministic benchmark for core browser-agent capabilities.

## Context

The initial scaffold had a smoke case. The next milestone was a real development dataset covering common task types and failure modes, even if the fake planner could not solve all cases yet.

## Key Constraints

- Do not implement a complex LLM agent.
- Do not break the smoke eval.
- Keep cases deterministic.
- Do not use LLM-as-judge.
- Add simulator pages/variants and deterministic checkers.

## Representative Prompt

Create `evals/cases_v1.json` with 12-13 deterministic simulated cases covering shopping, settings, support, dashboard, normal tasks, comparisons, long horizon, fake success, selector drift, modal blocking, safe settings, unsafe delete, vague instructions, support validation, table extraction, and prompt injection.

## Verification Commands

```bash
python3 -m pytest -q
python3 -m evals.run_eval --cases evals/cases.json
python3 -m evals.run_eval --cases evals/cases_v1.json
```

## Result

Added Dataset v1 with 13 deterministic cases, extended simulator domains, added state-based checkers, and kept the smoke dataset working.
