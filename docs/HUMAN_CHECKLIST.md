# Human Checklist

Before submitting:

- `pytest -q` passes.
- `python -m evals.run_eval --cases evals/cases.json` completes.
- `logs/runs/` contains at least one trace JSON.
- `logs/eval_report.json` exists.
- False success is distinguishable from verified success.
- FastAPI app starts locally.
- Dockerfile uses `$PORT` when available.
- README has exact test, eval, app, and Docker commands.
- No runtime path claims success without verifier approval.
