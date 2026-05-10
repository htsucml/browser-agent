# 00 Project Scaffold Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: Initial scaffold phase
- Purpose: Create the first runnable project skeleton
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

We are implementing an AI engineering assignment: Task 2, Generalized Browser Automation Agent.

Build a browser agent that accepts natural language task descriptions and reliably executes them across different sites. The agent should demonstrate self-correction, self-maintenance, silent-failure prevention, evaluation with a reliability dataset, and Zeabur-compatible deployment.

Create the project goal docs, coding-agent specs/skills, architecture docs, and a runnable thin skeleton for:

- schema
- browser agent flow
- simulator
- evaluator/metrics
- logging
- human web interface
- Zeabur deployment

Do not build a full intelligent browser agent yet. Build a minimal vertical scaffold with interfaces and one smoke-test case.

Implementation requirements:

- Define schemas/stubs for eval cases, traces, eval results, actions, verification results, failures, recovery, maintenance, and safety.
- Implement one fake shopping simulator page with deterministic resettable state.
- Implement observe -> plan -> locate -> act -> verify -> log -> final report.
- Rule-based planner is acceptable for this pass.
- Write JSON traces under `logs/runs/`.
- Add runtime verifier so no success is reported unless verification passes.
- Add offline evaluator and metrics.
- Add minimal FastAPI app.
- Add Dockerfile and README commands.
- Add tests for schemas, verifier, metrics, false success, and trace schema.

Acceptance:

- `python3 -m pytest -q` passes.
- `python3 -m evals.run_eval --cases evals/cases.json` runs.
- FastAPI app starts locally.
- Dockerfile is suitable for Zeabur.
