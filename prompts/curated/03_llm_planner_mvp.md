# 03 LLMPlanner MVP

## Purpose

Add LLMPlanner plumbing behind a config flag while keeping tests fully offline.

## Context

The RulePlanner baseline worked, but the assignment needed an LLM planning path. The goal of this pass was plumbing, not model quality.

## Key Constraints

- RulePlanner remains default.
- `PLANNER=llm` selects LLMPlanner.
- `LLM_PROVIDER=fake` must work without network/API keys.
- OpenAI provider reads `OPENAI_API_KEY` only when explicitly selected.
- Do not call external LLMs in tests.
- LLM prompt payload must not include evaluator-only success checks or forbidden outcomes.

## Representative Prompt

Add LLMPlanner with fake and OpenAI-compatible providers. Use structured JSON actions, validate output before execution, log planner/provider/model/token metadata, enforce call/step/output caps, redact secrets, and add tests for fake provider, invalid JSON, `needs_user`, key redaction, and prompt leakage.

## Verification Commands

```bash
python3 -m pytest -q
python3 -m evals.run_eval --cases evals/cases_v1.json
PLANNER=llm LLM_PROVIDER=fake python3 -m evals.run_eval --cases evals/cases_v1.json
```

## Result

Added LLMPlanner, FakeLLMClient, OpenAI-compatible client, planner selection, tests, trace metadata, and fake LLM dry-run support.
