# Architecture

This project has two execution surfaces:

1. A deterministic simulator-backed browser agent for benchmark evaluation.
2. A real-web read-only Playwright backend for BYOK summarization demos.

Both surfaces share the same engineering philosophy: the planner may propose what to do, but deterministic components validate, execute, verify, log, and report the result.

## Module Map

| Path | Role |
| --- | --- |
| `browser_agent/` | Runtime agent orchestration, planners, controller/executor, action validation, browser backends, verification, logging, display summaries, LLM clients, safety, and schemas. |
| `simulator/` | Deterministic fake websites and resettable state for shopping, settings, support, and dashboard tasks. |
| `evals/` | Dataset files, schema validation, offline evaluator, deterministic checkers, metrics, ablation runner, and failure-analysis reports. |
| `app/` | FastAPI human interface for simulator tasks and real-web read-only BYOK summarization. |
| `docs/` | Project report, evaluation report, architecture notes, demo guide, and progress log. |
| `tests/` | Unit and integration tests for schemas, verifier, evaluator, planner plumbing, BYOK safety, URL safety, read-only backend, and reporting. |
| `Dockerfile` | Zeabur-compatible runtime with Playwright Chromium installed. |

## Runtime Flow

Simulator task flow:

```text
user task
  -> observe simulator page/state
  -> planner selects next decision
  -> available action candidates generated
  -> action_id validated
  -> simulator executor mutates deterministic state
  -> runtime verifier checks expected condition
  -> trace logger writes JSON
  -> evaluator/checkers compute metrics
  -> display/report summarizes result
```

Real-web read-only flow:

```text
URL + task
  -> URL safety check
  -> Playwright goto(initial URL only)
  -> extract URL/title/headings/visible text/links count
  -> optional LLM summarization from extracted evidence
  -> trace logger writes JSON
  -> display result shows answer and evidence
```

Real-web mode does not click, fill forms, submit data, or navigate beyond the initial page load.

## Planner Interface

The project has two planner modes:

- `RulePlanner`: deterministic baseline and integration-test driver.
- `LLMPlanner`: model-driven planner that receives only agent-visible task and observation data.
- Controller/executor: validates planner output, applies safe simulator mutations, and records action outcomes.

Supported ablation configs:

- `rule`: `PLANNER=rule`
- `llm_fake`: `PLANNER=llm`, `LLM_PROVIDER=fake`
- `llm_openai`: `PLANNER=llm`, `LLM_PROVIDER=openai`

The planner is not responsible for declaring success. It proposes an action or `needs_user`; the verifier/evaluator decide whether the run actually passed.

## Available-Action Contract

The LLMPlanner uses a stable available-action-only contract. Instead of asking the model to invent CSS selectors or fuzzy button names, the system exposes compact action candidates and asks the model to choose one `action_id`.

Example:

```json
{
  "decision": "act",
  "action_id": "shopping:add_to_wishlist:compact-usb-c-hub",
  "reason": "It is the cheapest USB-C hub with rating at least 4.5."
}
```

Missing-info example:

```json
{
  "decision": "needs_user",
  "reason": "The support form requires an email address, but none was provided."
}
```

The executor rejects unknown or task-incompatible action IDs before mutation. Backward-compatible normalization handles model outputs such as `decision=click` or `decision=select` only when a valid `action_id` is present.

## Verifier and Evaluator Separation

The runtime verifier checks task completion during an agent run. The offline evaluator then loads traces and deterministic simulator state to compute metrics. Neither component uses LLM-as-judge.

This separation prevents silent success claims:

- The planner can stop or act.
- The controller can execute.
- The verifier decides runtime success.
- The evaluator decides benchmark pass/fail and false-success/unsafe-action metrics.

## Deterministic Components

Deterministic pipeline responsibilities:

- Available action generation.
- Action validation.
- Simulator execution.
- Runtime verification.
- Safety and missing-information preflight.
- Trace logging.
- Eval checkers.
- Metric computation.
- Failure analysis.
- URL blocking for public read-only mode.
- Secret redaction.
- Rate limiting and concurrency guarding.

## LLM Components

LLM responsibilities:

- Intent interpretation.
- Action selection from available candidates.
- Missing-information decisions.
- Read-only summarization/answering from extracted page evidence.

The LLM does not receive evaluator-only fields such as hidden success checks, forbidden outcomes, or expected answer keys.

## Real-Web Read-Only Backend

`PlaywrightBrowserBackend` supports:

- `goto(url)`
- `observe()`
- visible text extraction
- page title
- current URL
- headings
- link count
- optional screenshot
- `close()`

The CLI entry point is:

```bash
python3 -m browser_agent.run_readonly --url https://example.com --task "Summarize this page."
```

With LLM mode:

```bash
PLANNER=llm LLM_PROVIDER=fake python3 -m browser_agent.run_readonly --url https://example.com --task "Summarize this page."
```

The answer is stored as text in trace evidence. UI formatting normalizes multiline or collapsed bullet answers for readability while preserving raw trace JSON.

## BYOK and Key Handling

Public demo mode is BYOK-only:

- `ALLOW_BYOK=false` by default.
- `ALLOW_SERVER_OPENAI_KEY=false` by default.
- If BYOK is enabled, a request-provided OpenAI key is used only for that request.
- The key is not stored in traces, logs, cookies, localStorage, files, or app state.
- Secret-like strings are redacted from traces/errors/display.
- If `ALLOW_SERVER_OPENAI_KEY=false`, the app does not fall back to a server-side `OPENAI_API_KEY`.

Additional public-demo safeguards:

- `DEMO_TOKEN` gates `/run`; `/health` remains public.
- `RATE_LIMIT_RUNS` and `RATE_LIMIT_WINDOW_SECONDS` provide per-IP rate limiting.
- `MAX_ACTIVE_RUNS` defaults to 1.
- `MAX_RUN_SECONDS`, `MAX_STEPS`, `MAX_LLM_CALLS_PER_RUN`, `MAX_OUTPUT_TOKENS`, and `MAX_EXTRACT_CHARS` cap runtime/cost.
- HTTP(S) URL safety blocks localhost, loopback, private ranges, link-local, metadata IPs, and non-HTTP schemes.

## Trace Structure

Every run writes a JSON trace under `logs/runs/` with:

- run ID, task, start URL
- status and verified flag
- planner type, LLM provider/model
- actions
- verifications
- failures, recoveries, maintenance events, safety events
- final evidence
- token and call counts
- timestamps

Generated trace/eval logs are ignored by git and should not be committed unless explicitly requested.
