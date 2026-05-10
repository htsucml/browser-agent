# 03 LLMPlanner MVP Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: LLMPlanner MVP phase
- Purpose: Add LLMPlanner behind a configuration flag with fake provider tests
- Safety notes: No real API key or external LLM calls included

## Prompt Excerpt

Add an LLMPlanner behind a configuration flag, but test it only with a FakeLLMClient / mock provider. Do not call a real OpenAI API. Do not require any API key for tests.

Requirements:

- RulePlanner remains default.
- LLMPlanner selected with `PLANNER=llm`.
- Provider selected with `LLM_PROVIDER=fake` or `LLM_PROVIDER=openai`.
- FakeLLMClient never calls external APIs and can return scripted structured JSON.
- OpenAI-compatible provider reads `OPENAI_API_KEY` only from environment or request wiring and fails gracefully if missing.
- LLMPlanner input may include user instruction, current observation, visible text or structured simulator state, available actions, action history, and previous failure context.
- LLMPlanner must not receive evaluator-only hidden ground truth such as success checks, forbidden outcomes, expected status, or answer keys.
- Output must be structured JSON supporting click, type, select, stop, and needs_user.
- Invalid JSON should produce controlled failure, not crash.
- Add safe trace metadata: planner type, provider, model, call counts, token counts.
- Add caps: `MAX_LLM_CALLS_PER_RUN`, `MAX_STEPS`, `MAX_OUTPUT_TOKENS`, `REQUEST_TIMEOUT_SECONDS`.

Acceptance:

- tests pass without `OPENAI_API_KEY`
- default rule baseline does not regress
- fake LLM dry run works
- no external API calls in tests
- no secrets are logged
