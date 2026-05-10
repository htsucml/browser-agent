# 05 Real-Web Read-Only Demo Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: Real-web read-only phase
- Purpose: Add safe real-web extraction and optional LLM summarization
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

Add optional LLM summarization / answering for real-web read-only mode.

For HTTP/HTTPS URLs:

- open page with existing Playwright read-only backend
- extract URL, title, headings, visible text, and links count
- truncate visible text to `MAX_EXTRACT_CHARS`
- if planner/provider indicates LLM mode, call LLM once to answer the user's read-only task
- return both extracted evidence and `llm_answer`

Important:

- read-only only
- no clicks
- no form filling
- no navigation beyond initial page load
- do not claim browser actions beyond extraction
- do not call real OpenAI in tests
- use fake provider for deterministic tests
- preserve simulator evals

Polish answer rendering:

- ask the LLM for plain Markdown text, not JSON
- store raw LLM answer as text
- preserve bullet line breaks in UI
- normalize safe collapsed bullet text for display
- keep raw JSON debug trace unchanged

Acceptance:

- Docker verification passes
- real-web fake summarization works
- no external API calls in tests
- no secrets logged
