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
```

This writes run traces to `logs/runs/` and reports to:

- `logs/eval_report.json`
- `logs/eval_report.md`

## Planner Modes

RulePlanner is the default and requires no environment variables:

```bash
python3 -m evals.run_eval --cases evals/cases_v1.json
```

Fake LLMPlanner dry run uses a mock provider and never calls an external API:

```bash
PLANNER=llm LLM_PROVIDER=fake python3 -m evals.run_eval --cases evals/cases_v1.json
```

Real OpenAI-compatible LLMPlanner is for local experiments later. Do not deploy a public LLM key on Zeabur.

```bash
PLANNER=llm \
LLM_PROVIDER=openai \
OPENAI_API_KEY=... \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_STEPS=3 \
MAX_OUTPUT_TOKENS=300 \
python3 -m evals.run_eval --cases evals/cases_v1.json --case support_validation_001
```

LLMPlanner receives only agent-visible task and observation data. Runtime verifiers and offline evaluators remain deterministic and do not use LLM-as-judge.

## Start Web App

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

The web app keeps simulator tasks as the default. For `http://` or `https://` URLs, it uses the read-only Playwright backend and reports page title/text evidence without clicking or filling forms.

## Read-Only Online Smoke

Install Playwright and its browser binary locally, then run:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install --with-deps chromium
python3 -m browser_agent.run_readonly --url https://example.com --task "Return the page title and main visible text."
```

The read-only runner writes a trace to `logs/runs/` and reports success only when a page title or non-empty visible text is extracted.

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
