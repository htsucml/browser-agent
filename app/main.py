"""Human web interface for running scaffold browser-agent tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from browser_agent.agent import BrowserAgent
from browser_agent.run_readonly import run_readonly

app = FastAPI(title="Browser Agent Scaffold")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"start_url": "simulator://shopping", "task": "Add Red Shoes to the cart", "result": None},
    )


@app.post("/run", response_class=HTMLResponse)
def run_task(request: Request, start_url: str = Form(...), task: str = Form(...)) -> HTMLResponse:
    if start_url.startswith(("http://", "https://")):
        result = run_readonly(start_url, task)
        trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
    else:
        result = BrowserAgent().run(start_url=start_url, task=task)
        trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    return templates.TemplateResponse(
        request,
        "index.html",
        {"start_url": start_url, "task": task, "result": result, "trace": trace},
    )


def port() -> int:
    return int(os.environ.get("PORT", "8000"))
