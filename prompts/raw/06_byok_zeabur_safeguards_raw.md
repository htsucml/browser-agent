# 06 BYOK / Zeabur Safeguards Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: Public-demo hardening phase
- Purpose: Add BYOK and Zeabur-safe public demo safeguards
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

Add safe BYOK support and minimal demo safeguards locally, preparing for a later Zeabur BYOK demo.

Requirements:

- `ALLOW_BYOK=false` by default
- `ALLOW_SERVER_OPENAI_KEY=false` by default
- user-provided OpenAI key is used only for that request
- do not store key in trace JSON, logs, cookies, localStorage, files, or app state
- do not echo key in HTML or errors
- redact secret-like strings
- if `DEMO_TOKEN` is set, run endpoints require it
- `/health` remains public
- missing/wrong token returns 401/403
- add per-IP rate limiting with `RATE_LIMIT_RUNS` and `RATE_LIMIT_WINDOW_SECONDS`
- add `MAX_ACTIVE_RUNS`
- enforce runtime/cost caps
- block unsafe URLs in real-web read-only mode: localhost, loopback, private IPs, metadata IPs, link-local, file scheme, non-HTTP schemes, and domains resolving to private/internal IPs
- no real OpenAI calls in tests

Acceptance:

- tests pass without `OPENAI_API_KEY`
- BYOK disabled by default
- server key fallback disabled by default
- no secrets logged
- Docker verification passes
