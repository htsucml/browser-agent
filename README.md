# Generalized Browser Automation Agent Scaffold

This repo is a thin vertical scaffold for Task 2: Generalized Browser Automation Agent.

It includes project docs, coding-agent skills, typed runtime schemas, a deterministic shopping simulator, trace logging, offline evaluation, tests, and a minimal FastAPI UI suitable for Zeabur deployment.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Inside an activated virtual environment, `python`, `pytest`, and `uvicorn` may also work directly.

## Run Tests

```bash
python3 -m pytest -q
```

## Run Eval

Default rule-planner eval:

```bash
python3 -m evals.run_eval --cases evals/cases.json
python3 -m evals.run_eval --cases evals/cases_v1.json
python3 -m evals.run_eval --cases evals/cases_smoke.json
python3 -m evals.run_eval --cases evals/cases_dev.json
```

This writes run traces to `logs/runs/` and reports to:

- `logs/eval_report.json`
- `logs/eval_report.md`

Dataset split scaffolding:

- `evals/cases_smoke.json`: current 2-case smoke set.
- `evals/cases_dev.json`: current Dataset v1 development set.
- `evals/cases_test.json`: small placeholder copied subset for plumbing only. A true test split should be frozen and not tuned on.
- `evals/cases_llm_smoke.json`: four-case LLM smoke suite.
- `evals/cases_llm_dev.json`: seven-case LLM-ready development subset copied from Dataset v1.

Compare planner configs with the ablation runner:

```bash
python3 -m evals.run_ablation --cases evals/cases_llm_smoke.json --configs rule,llm_fake
python3 -m evals.run_ablation --cases evals/cases_llm_dev.json --configs rule,llm_fake
./scripts/ablate_llm_dev_fake.sh
```

This writes `logs/ablation_report.json` and `logs/ablation_report.md`. The ablation runner does not run real OpenAI by default.

## Planner Modes

RulePlanner is the default and requires no environment variables:

```bash
python3 -m evals.run_eval --cases evals/cases_v1.json
```

RulePlanner is a baseline and integration-test driver, not the long-term intelligence layer. Future improvements should prefer shared pipeline mechanisms such as available-action generation, executor behavior, verifier coverage, preflight checks, recovery, and memory. Avoid growing case-specific rule spaghetti.

Fake LLMPlanner dry run uses a mock provider and never calls an external API:

```bash
PLANNER=llm LLM_PROVIDER=fake python3 -m evals.run_eval --cases evals/cases_v1.json
PLANNER=llm LLM_PROVIDER=fake python3 -m evals.run_eval --cases evals/cases_llm_smoke.json
./scripts/llm_smoke_fake.sh
./scripts/llm_smoke_suite_fake.sh
```

Unified ablation config meanings:

- `rule`: `PLANNER=rule`
- `llm_fake`: `PLANNER=llm`, `LLM_PROVIDER=fake`
- `llm_openai`: `PLANNER=llm`, `LLM_PROVIDER=openai`, strict caps, paid local run only

Real OpenAI-compatible LLMPlanner is for local one-case experiments later. Do not deploy a public LLM key on Zeabur. This uses paid API credits.

```bash
PLANNER=llm \
LLM_PROVIDER=openai \
OPENAI_API_KEY=... \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_STEPS=3 \
MAX_OUTPUT_TOKENS=300 \
REQUEST_TIMEOUT_SECONDS=30 \
python3 -m evals.run_eval --cases evals/cases_v1.json --case support_validation_001
```

Equivalent helper script:

```bash
OPENAI_API_KEY=... ./scripts/llm_smoke_one_case.sh support_validation_001
```

Four-case local LLM smoke suite for currently validated cases:

```bash
OPENAI_API_KEY=... ./scripts/llm_smoke_suite_openai.sh
```

The suite uses strict caps by default: `LLM_MODEL=gpt-4.1-nano`, `MAX_LLM_CALLS_PER_RUN=1`, `MAX_STEPS=3`, `MAX_OUTPUT_TOKENS=300`, and `REQUEST_TIMEOUT_SECONDS=30`. Run it locally only; do not put `OPENAI_API_KEY` on Zeabur yet.

Paid local LLM ablation over the seven-case LLM dev subset:

```bash
OPENAI_API_KEY=... python3 -m evals.run_ablation --cases evals/cases_llm_dev.json --configs rule,llm_openai --allow-paid
OPENAI_API_KEY=... ./scripts/ablate_llm_dev_openai.sh
```

`llm_openai` will be skipped unless `--allow-paid` is provided and `OPENAI_API_KEY` is set. The key is never printed by the runner or helper script.

LLMPlanner receives only agent-visible task and observation data. Runtime verifiers and offline evaluators remain deterministic and do not use LLM-as-judge.

## BYOK Demo Mode

The web app supports bring-your-own-key OpenAI runs for simulator tasks and read-only online summarization. BYOK is disabled by default and a submitted key is used only for that one request. The app does not store keys in traces, logs, cookies, localStorage, files, or app state, and key-like strings are redacted from trace errors.

Local BYOK app test:

```bash
ALLOW_BYOK=true \
ALLOW_SERVER_OPENAI_KEY=false \
DEMO_TOKEN=local-demo-password \
MAX_ACTIVE_RUNS=1 \
RATE_LIMIT_RUNS=5 \
RATE_LIMIT_WINDOW_SECONDS=600 \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_STEPS=3 \
MAX_OUTPUT_TOKENS=300 \
REQUEST_TIMEOUT_SECONDS=30 \
MAX_RUN_SECONDS=30 \
MAX_EXTRACT_CHARS=10000 \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://127.0.0.1:8000`, select `llm` and `openai`, enter the demo token and your OpenAI key in the password fields, and run one simulator smoke task or one read-only `https://` URL.

For public Zeabur demos, prefer BYOK and do not configure a server-side `OPENAI_API_KEY`. Recommended Zeabur environment variables:

```bash
ALLOW_BYOK=true
ALLOW_SERVER_OPENAI_KEY=false
DEMO_TOKEN=<random-password>
MAX_ACTIVE_RUNS=1
RATE_LIMIT_RUNS=5
RATE_LIMIT_WINDOW_SECONDS=600
MAX_LLM_CALLS_PER_RUN=1
MAX_STEPS=3
MAX_OUTPUT_TOKENS=300
REQUEST_TIMEOUT_SECONDS=30
MAX_RUN_SECONDS=30
MAX_EXTRACT_CHARS=10000
```

Do not enter secrets unless you trust the deployment. A BYOK request sends the key to this backend for that request only. Keep real-web mode read-only, do not set `OPENAI_API_KEY` on public Zeabur, and suspend the service when you are done testing.

## Start Web App

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

The web app keeps simulator tasks as the default. For `http://` or `https://` URLs, it uses the read-only Playwright backend and reports page title/text evidence without clicking, filling forms, or navigating beyond the initial page load. If planner mode is `llm`, it can optionally answer or summarize the task from the extracted evidence.

## Read-Only Online Smoke

Install Playwright and its browser binary locally, then run:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install --with-deps chromium
python3 -m browser_agent.run_readonly --url https://example.com --task "Return the page title and main visible text."
```

Fake LLM summarization, with no external API call:

```bash
PLANNER=llm LLM_PROVIDER=fake python3 -m browser_agent.run_readonly --url https://example.com --task "Summarize this page from the extracted evidence."
```

Local OpenAI/BYOK-style summarization:

```bash
PLANNER=llm \
LLM_PROVIDER=openai \
OPENAI_API_KEY=... \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_OUTPUT_TOKENS=300 \
REQUEST_TIMEOUT_SECONDS=30 \
MAX_EXTRACT_CHARS=10000 \
python3 -m browser_agent.run_readonly --url https://example.com --task "Summarize this page from the extracted evidence."
```

The read-only runner writes a trace to `logs/runs/` and reports success only when a page title or non-empty visible text is extracted. Optional LLM summarization receives only the extracted URL, title, headings, visible text, and links count. It does not click, fill forms, or use LLM-as-judge.

## Docker

The Docker image installs Playwright Chromium and creates `logs/runs/` for trace output.

```bash
docker build -t browser-agent-baseline .
docker run --rm -p 8000:8000 -e PORT=8000 browser-agent-baseline
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Container read-only online smoke:

```bash
curl -X POST http://127.0.0.1:8000/run \
  -F "start_url=https://example.com" \
  -F "task=Return the page title and main visible text."
```

## Zeabur Notes

Zeabur can build this Dockerfile directly. The image installs Chromium during build, and the app command reads Zeabur's `PORT` environment variable:

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

Use `/health` as a lightweight health route.

## Current Fake or Stubbed Pieces

- Planner is a deterministic regex/rule-based fake planner.
- LLMPlanner plumbing exists behind `PLANNER=llm`; fake mode is for tests/dry runs, while real API mode is local-only for now.
- Browser adapter targets the simulator, not a real browser.
- Real-browser support is read-only through Playwright; it does not click or fill forms on external sites.
- Recovery records safe placeholders.
- Maintenance events support locator-strategy adaptation hooks but do not persist learned selectors yet.
- Token and cost fields are placeholders.
- Dataset contains one passing smoke case and one negative false-success guard case.
- Dataset v1 contains 13 deterministic simulated cases across shopping, settings, support, and dashboard workflows.

## Next Milestone

Add a Playwright-backed browser adapter, expand simulator variants for selector drift, and grow the eval dataset across forms, search, navigation, shopping, and account-free workflows while preserving deterministic verification.
