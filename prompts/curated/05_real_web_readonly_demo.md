# 05 Real-Web Read-Only Demo

## Purpose

Add useful real-web behavior without enabling real-web mutation.

## Context

The simulator agent was evaluated, but public demos benefit from opening real pages. The safe boundary was read-only extraction plus optional BYOK summarization.

## Key Constraints

- No real-web clicking.
- No real-web form filling.
- No navigation beyond initial page load.
- No external LLM calls in tests.
- Preserve simulator evals.
- Respect URL safety, caps, and redaction.

## Representative Prompt

Add optional LLM summarization/answering for real-web read-only mode. Extract URL, title, headings, visible text, and link count; truncate text; if LLM mode is selected, call the provider once to answer from extracted evidence. Return evidence and answer, and display readable answer before raw trace.

## Verification Commands

```bash
python3 -m pytest -q
python3 -m browser_agent.run_readonly --url https://example.com --task "Return the page title and main visible text."
PLANNER=llm LLM_PROVIDER=fake python3 -m browser_agent.run_readonly --url https://example.com --task "Summarize this page."
```

## Result

Added Playwright read-only extraction, fake/real LLM summarization path, answer-quality warnings, clean bullet formatting, and UI display of answer/source/title/evidence/metrics/trace.
