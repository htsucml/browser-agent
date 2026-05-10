"""Human web interface for running scaffold browser-agent tasks."""

from __future__ import annotations

import concurrent.futures
import ipaddress
import json
import os
import socket
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from browser_agent.agent import BrowserAgent
from browser_agent.config import AppConfig, PlannerConfig
from browser_agent.display import build_display_result
from browser_agent.llm_clients import _USE_ENV_API_KEY
from browser_agent.run_readonly import run_readonly

app = FastAPI(title="Browser Agent Scaffold")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_RUN_LOCK = threading.Lock()
_ACTIVE_RUNS = 0
_RATE_LIMITS: dict[str, list[float]] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", _template_context(request))


@app.post("/run", response_class=HTMLResponse)
def run_task(
    request: Request,
    start_url: str = Form(...),
    task: str = Form(...),
    planner: str = Form("rule"),
    llm_provider: str = Form("fake"),
    llm_model: str = Form("gpt-4.1-nano"),
    openai_api_key: str = Form(""),
    demo_token: str = Form(""),
) -> HTMLResponse:
    app_config = AppConfig.from_env()
    _check_demo_token(app_config, demo_token)
    _check_rate_limit(request, app_config)
    _acquire_run_slot(app_config)
    try:
        result, trace = _run_with_timeout(
            app_config,
            start_url=start_url,
            task=task,
            planner=planner,
            llm_provider=llm_provider,
            llm_model=llm_model,
            openai_api_key=openai_api_key,
        )
    finally:
        _release_run_slot()

    return templates.TemplateResponse(
        request,
        "index.html",
        _template_context(
            request,
            start_url=start_url,
            task=task,
            planner=planner,
            llm_provider=llm_provider,
            llm_model=llm_model,
            result=result,
            trace=trace,
            display_result=build_display_result(trace, _trace_path(result)),
        ),
    )


def _run_with_timeout(
    app_config: AppConfig,
    start_url: str,
    task: str,
    planner: str,
    llm_provider: str,
    llm_model: str,
    openai_api_key: str,
):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        _run_once,
        app_config,
        start_url,
        task,
        planner,
        llm_provider,
        llm_model,
        openai_api_key,
    )
    try:
        return future.result(timeout=app_config.max_run_seconds)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        raise HTTPException(status_code=503, detail="Run timed out. Try a smaller task or stricter limits.") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _run_once(
    app_config: AppConfig,
    start_url: str,
    task: str,
    planner: str,
    llm_provider: str,
    llm_model: str,
    openai_api_key: str,
):
    planner = planner.lower()
    llm_provider = llm_provider.lower()
    request_key = openai_api_key.strip()
    if request_key and not app_config.allow_byok:
        raise HTTPException(status_code=403, detail="BYOK is disabled on this deployment.")

    if start_url.startswith(("http://", "https://")):
        _validate_public_http_url(start_url)
        result = run_readonly(start_url, task, max_extract_chars=app_config.max_extract_chars)
        trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        return result, trace

    if not start_url.startswith("simulator://"):
        raise HTTPException(status_code=400, detail="Only simulator:// or public http(s) URLs are supported.")

    config = PlannerConfig(
        planner=planner,
        llm_provider=llm_provider,
        llm_model=llm_model,
        max_llm_calls_per_run=_env_int("MAX_LLM_CALLS_PER_RUN", 1),
        max_steps=_env_int("MAX_STEPS", 3),
        max_output_tokens=_env_int("MAX_OUTPUT_TOKENS", 300),
        request_timeout_seconds=_env_float("REQUEST_TIMEOUT_SECONDS", 30.0),
    )
    llm_api_key: str | None | object = _USE_ENV_API_KEY
    if planner == "llm" and llm_provider == "openai":
        if request_key:
            llm_api_key = request_key
        elif app_config.allow_server_openai_key:
            llm_api_key = _USE_ENV_API_KEY
        else:
            llm_api_key = None

    result = BrowserAgent(config=config, llm_api_key=llm_api_key).run(start_url=start_url, task=task, max_steps=config.max_steps)
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    return result, trace


def _template_context(
    request: Request,
    start_url: str = "simulator://shopping",
    task: str = "Add Red Shoes to the cart",
    planner: str = "rule",
    llm_provider: str = "fake",
    llm_model: str = "gpt-4.1-nano",
    result=None,
    trace=None,
    display_result=None,
) -> dict:
    app_config = AppConfig.from_env()
    return {
        "request": request,
        "start_url": start_url,
        "task": task,
        "planner": planner,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "result": result,
        "trace": trace,
        "display_result": display_result,
        "demo_token_enabled": bool(app_config.demo_token),
        "allow_byok": app_config.allow_byok,
    }


def _check_demo_token(app_config: AppConfig, provided: str) -> None:
    if not app_config.demo_token:
        return
    if not provided:
        raise HTTPException(status_code=401, detail="Demo token is required.")
    if provided != app_config.demo_token:
        raise HTTPException(status_code=403, detail="Demo token is invalid.")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request, app_config: AppConfig) -> None:
    now = time.monotonic()
    window_start = now - app_config.rate_limit_window_seconds
    client = _client_ip(request)
    with _RUN_LOCK:
        recent = [stamp for stamp in _RATE_LIMITS.get(client, []) if stamp >= window_start]
        if len(recent) >= app_config.rate_limit_runs:
            _RATE_LIMITS[client] = recent
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        recent.append(now)
        _RATE_LIMITS[client] = recent


def _acquire_run_slot(app_config: AppConfig) -> None:
    global _ACTIVE_RUNS
    with _RUN_LOCK:
        if _ACTIVE_RUNS >= app_config.max_active_runs:
            raise HTTPException(status_code=503, detail="Server is busy. Please try again shortly.")
        _ACTIVE_RUNS += 1


def _release_run_slot() -> None:
    global _ACTIVE_RUNS
    with _RUN_LOCK:
        _ACTIVE_RUNS = max(0, _ACTIVE_RUNS - 1)


def _validate_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL hostname is required.")
    hostname = parsed.hostname.strip().lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
        raise HTTPException(status_code=400, detail="Internal hostnames are blocked.")
    addresses = _resolve_host(hostname)
    if not addresses:
        raise HTTPException(status_code=400, detail="Could not resolve URL hostname.")
    for address in addresses:
        if _is_blocked_ip(address):
            raise HTTPException(status_code=400, detail="Private, local, and metadata URLs are blocked.")


def _resolve_host(hostname: str) -> list[str]:
    try:
        ipaddress.ip_address(hostname)
        return [hostname]
    except ValueError:
        pass
    try:
        return list({item[4][0] for item in socket.getaddrinfo(hostname, None)})
    except socket.gaierror:
        return []


def _is_blocked_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    metadata = ipaddress.ip_address("169.254.169.254")
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip == metadata
    )


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def port() -> int:
    return int(os.environ.get("PORT", "8000"))


def _trace_path(result) -> str:
    if isinstance(result, dict):
        return str(result.get("trace_path", ""))
    return str(getattr(result, "trace_path", ""))
