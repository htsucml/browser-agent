# AI Engineering Assignment Agent Guide

This repository is for Task 2: Generalized Browser Automation Agent.

## Project Goal

Build a browser automation agent that accepts natural language task descriptions and executes them across sites with explicit verification, recovery, maintenance hooks, and deterministic evaluation.

This pass intentionally builds a thin vertical scaffold, not a full intelligent browser agent.

## Coding-Agent Rules

- Keep browser runtime modules under `browser_agent/`.
- Keep deterministic simulator code under `simulator/`.
- Keep evaluation code and datasets under `evals/`.
- Keep the human web interface under `app/`.
- Never report success unless a `VerificationResult.passed` value is true.
- Prefer typed models from `browser_agent.schemas` for boundaries and trace records.
- Add deterministic tests before expanding behavior.
- Do not add an LLM-as-judge evaluator.
- Do not commit generated trace or eval logs unless explicitly requested.

## Runtime Browser-Agent Rules

Runtime browser-agent modules are normal application code. They are not Codex skills.

- Observe current page/state.
- Plan with an explicit target and expected verification.
- Locate with strategies that can be maintained when UI changes.
- Act through browser/controller interfaces.
- Verify through deterministic checks.
- Log all actions, failures, recovery, maintenance, safety events, and final evidence.

## Useful Commands

```bash
python3 -m pytest -q
python3 -m evals.run_eval --cases evals/cases.json
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
