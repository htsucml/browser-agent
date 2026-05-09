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

```bash
python3 -m evals.run_eval --cases evals/cases.json
python3 -m evals.run_eval --cases evals/cases_v1.json
```

This writes run traces to `logs/runs/` and reports to:

- `logs/eval_report.json`
- `logs/eval_report.md`

## Start Web App

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

The web app keeps simulator tasks as the default. For `http://` or `https://` URLs, it uses the read-only Playwright backend and reports page title/text evidence without clicking or filling forms.

## Read-Only Online Smoke

Install Playwright and its browser binary, then run:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m browser_agent.run_readonly --url https://example.com --task "Return the page title and main visible text."
```

The read-only runner writes a trace to `logs/runs/` and reports success only when a page title or non-empty visible text is extracted.

## Docker

```bash
docker build -t browser-agent-task2 .
docker run --rm -p 8000:8000 -e PORT=8000 browser-agent-task2
```

## Zeabur Notes

Zeabur can build this Dockerfile directly. The app command reads the `PORT` environment variable:

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

## Current Fake or Stubbed Pieces

- Planner is a deterministic regex/rule-based fake planner.
- Browser adapter targets the simulator, not a real browser.
- Real-browser support is read-only through Playwright; it does not click or fill forms on external sites.
- Recovery records safe placeholders.
- Maintenance events support locator-strategy adaptation hooks but do not persist learned selectors yet.
- Token and cost fields are placeholders.
- Dataset contains one passing smoke case and one negative false-success guard case.
- Dataset v1 contains 13 deterministic simulated cases across shopping, settings, support, and dashboard workflows.

## Next Milestone

Add a Playwright-backed browser adapter, expand simulator variants for selector drift, and grow the eval dataset across forms, search, navigation, shopping, and account-free workflows while preserving deterministic verification.
