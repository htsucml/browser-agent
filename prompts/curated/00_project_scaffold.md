# 00 Project Scaffold

## Purpose

Create the initial vertical scaffold for a generalized browser automation agent assignment.

## Context

The project needed to demonstrate architecture, deterministic evaluation, trace logging, a simulator, a basic web interface, and Zeabur-compatible deployment without pretending to be a full intelligent browser agent yet.

## Key Constraints

- Keep agent, simulator, evaluator, and app separated.
- Do not build a complex LLM planner yet.
- Use typed data models and clear TODOs for placeholders.
- No success unless explicit verification passes.
- Add tests and Docker/Zeabur deployment.

## Representative Prompt

Build the project goal docs, coding-agent specs/skills, architecture docs, and a runnable thin skeleton for schema, browser agent flow, simulator, evaluator/metrics, logging, human web interface, and Zeabur deployment. Implement observe -> plan -> locate -> act -> verify -> log -> final report. The planner can be rule-based for this pass.

## Verification Commands

```bash
python3 -m pytest -q
python3 -m evals.run_eval --cases evals/cases.json
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Result

Created the separated runtime, simulator, evaluator, docs, tests, FastAPI app, trace logging, Dockerfile, and smoke eval.
