# Schema Steward

Use this skill when changing trace, dataset, eval result, or browser-agent boundary schemas.

## Workflow

1. Update `browser_agent/schemas.py` first.
2. Update matching JSON Schema files in `docs/` or `evals/`.
3. Add or update tests that load representative payloads.
4. Run `pytest -q`.

## Guardrails

- Keep schema changes backward-aware and explicit.
- Do not allow trace success without `verified: true`.
- Keep timestamps ISO-8601 strings.
- Include placeholders for token and cost fields even before LLM integration.
