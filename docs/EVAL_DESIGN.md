# Evaluation Design

Evaluation is deterministic and offline.

The evaluator:

- reads `evals/cases.json`
- resets simulator state
- runs the browser agent
- loads the emitted trace
- checks final simulator/page state
- computes metrics
- writes `logs/eval_report.json` and `logs/eval_report.md`

No LLM-as-judge is used.

Primary metric fields:

- `verified_success`
- `false_success`
- `unsafe_action`
- `correct_refusal`
- `browser_spl`
- `num_steps`
- `recovery_success`
- `selector_drift_recovery`
- `token_count`
