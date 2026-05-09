# Failure Log Analysis

Use this skill when investigating failed runs or improving recovery.

## Workflow

1. Inspect the trace under `logs/runs/`.
2. Identify the first failed assumption in observe, plan, locate, act, or verify.
3. Add a `FailureEvent` taxonomy label.
4. Add a deterministic regression case when possible.
5. Improve recovery or maintenance without weakening verification.

## Guardrails

- Do not mark a run successful by relaxing checks.
- Preserve failure evidence in the trace.
- Prefer locator strategy improvements over single-selector fixes.
