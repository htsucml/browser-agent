"""Read-only real-browser runner for online smoke checks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from browser_agent.browser import PlaywrightBrowserBackend
from browser_agent.config import PlannerConfig
from browser_agent.llm_clients import _USE_ENV_API_KEY, make_llm_client
from browser_agent.logger import TraceLogger
from browser_agent.redaction import redact_secrets
from browser_agent.schemas import AgentTrace, new_id


def run_readonly(
    url: str,
    task: str,
    screenshot: str | None = None,
    max_extract_chars: int = 10000,
    config: PlannerConfig | None = None,
    llm_api_key: str | None | object = _USE_ENV_API_KEY,
) -> dict[str, Any]:
    run_id = new_id("readonly")
    trace = AgentTrace(run_id=run_id, case_id=None, start_url=url, task=task, status="failed", verified=False)
    config = config or PlannerConfig.from_env()
    trace.planner_type = config.planner
    if config.planner == "llm":
        trace.llm_provider = config.llm_provider
        trace.llm_model = config.llm_model
    backend = None
    screenshot_path = None
    try:
        backend = PlaywrightBrowserBackend()
        backend.goto(url)
        snapshot = backend.observe()
        if screenshot:
            screenshot_path = backend.screenshot(screenshot)
        extracted_text = snapshot.text[:max_extract_chars]
        llm_answer = None
        if config.planner == "llm" and config.max_llm_calls_per_run > 0:
            llm_response = _summarize_with_llm(config, llm_api_key, task, snapshot.url, snapshot.title, snapshot.headings or [], extracted_text, snapshot.links_count)
            llm_answer = llm_response["answer"]
            trace.llm_call_count = 1
            trace.llm_model = llm_response.get("model") or trace.llm_model
            trace.prompt_tokens = int(llm_response.get("prompt_tokens", 0))
            trace.completion_tokens = int(llm_response.get("completion_tokens", 0))
            trace.total_tokens = int(llm_response.get("total_tokens", 0))
            trace.token_count = trace.total_tokens
        loaded = bool(snapshot.title.strip() or snapshot.text.strip())
        trace.verified = loaded
        trace.status = "success" if loaded else "failed"
        trace.final_evidence = {
            "reason": "Page loaded and readable content was extracted." if loaded else "No readable title or visible text extracted.",
            "url": snapshot.url,
            "title": snapshot.title,
            "headings": snapshot.headings or [],
            "visible_text_snippet": extracted_text[:1000],
            "extracted_text": extracted_text,
            "extract_chars": len(extracted_text),
            "links_count": snapshot.links_count,
            "screenshot_path": screenshot_path,
        }
        if llm_answer is not None:
            trace.final_evidence["llm_answer"] = llm_answer
    except Exception as exc:
        trace.status = "failed"
        trace.verified = False
        trace.final_evidence = {"reason": redact_secrets(str(exc)), "url": url}
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass

    trace_path = TraceLogger().write(trace)
    safe_evidence = redact_secrets(trace.final_evidence)
    return {
        "run_id": run_id,
        "status": trace.status,
        "verified": trace.verified,
        "trace_path": trace_path,
        **safe_evidence,
    }


def _summarize_with_llm(
    config: PlannerConfig,
    api_key: str | None | object,
    task: str,
    url: str,
    title: str,
    headings: list[str],
    visible_text: str,
    links_count: int,
) -> dict[str, Any]:
    client = make_llm_client(config.llm_provider, config.llm_model, api_key=api_key)
    payload = {
        "system_prompt": (
            "You answer read-only browser tasks from extracted page evidence. "
            "Do not claim to click, fill forms, navigate, or verify anything beyond the provided evidence. "
            "Return only valid JSON with an answer field."
        ),
        "input": {
            "mode": "read_only_summarization",
            "task": task,
            "page": {
                "url": url,
                "title": title,
                "headings": headings,
                "visible_text": visible_text,
                "links_count": links_count,
            },
        },
    }
    response = client.generate_json(
        payload,
        max_output_tokens=config.max_output_tokens,
        timeout_seconds=config.request_timeout_seconds,
    )
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        data = {"answer": response.content}
    answer = str(data.get("answer") or data.get("summary") or data.get("result") or "")
    return {
        "answer": answer,
        "model": response.model,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "total_tokens": response.total_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--screenshot")
    parser.add_argument("--planner", default=None)
    parser.add_argument("--llm-provider", default=None)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--max-extract-chars", type=int, default=int(os.environ.get("MAX_EXTRACT_CHARS", "10000")))
    args = parser.parse_args()
    config = PlannerConfig.from_env()
    if args.planner or args.llm_provider or args.llm_model:
        config = PlannerConfig(
            planner=(args.planner or config.planner).lower(),
            llm_provider=(args.llm_provider or config.llm_provider).lower(),
            llm_model=args.llm_model or config.llm_model,
            max_llm_calls_per_run=config.max_llm_calls_per_run,
            max_steps=config.max_steps,
            max_output_tokens=config.max_output_tokens,
            request_timeout_seconds=config.request_timeout_seconds,
        )
    result = run_readonly(args.url, args.task, args.screenshot, max_extract_chars=args.max_extract_chars, config=config)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
