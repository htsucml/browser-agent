# 06 BYOK / Zeabur Safeguards

## Purpose

Make the public demo safer for BYOK use on Zeabur.

## Context

The app could run locally with real OpenAI keys, but public deployment should not have a server-side key. Users should provide their own key only for a single request, behind a demo token and runtime limits.

## Key Constraints

- `ALLOW_BYOK=false` by default.
- `ALLOW_SERVER_OPENAI_KEY=false` by default.
- Do not store or render keys.
- Redact secret-like strings.
- Require `DEMO_TOKEN` when set.
- Add rate limits, active-run guard, runtime/cost caps, and URL safety.
- Do not call real OpenAI in tests.

## Representative Prompt

Add safe BYOK support and Zeabur safeguards: per-request OpenAI key handling, demo token, per-IP rate limit, max active runs, max run seconds, LLM call/output/step caps, URL blocking for localhost/private/metadata IPs, UI password fields and warnings, and tests proving secrets are not logged.

## Verification Commands

```bash
python3 -m pytest -q
docker build -t browser-agent-baseline .
docker run --rm -p 8000:8000 -e ALLOW_BYOK=true -e ALLOW_SERVER_OPENAI_KEY=false -e DEMO_TOKEN=local-demo-password browser-agent-baseline
```

## Result

Added BYOK safeguards, Zeabur env documentation, URL safety tests, token/rate/concurrency tests, and public-demo guidance to avoid server-side `OPENAI_API_KEY`.
