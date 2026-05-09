"""Read-only real-browser runner for online smoke checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from browser_agent.browser import PlaywrightBrowserBackend
from browser_agent.logger import TraceLogger
from browser_agent.schemas import AgentTrace, new_id


def run_readonly(url: str, task: str, screenshot: str | None = None) -> dict[str, Any]:
    run_id = new_id("readonly")
    trace = AgentTrace(run_id=run_id, case_id=None, start_url=url, task=task, status="failed", verified=False)
    backend = None
    screenshot_path = None
    try:
        backend = PlaywrightBrowserBackend()
        backend.goto(url)
        snapshot = backend.observe()
        if screenshot:
            screenshot_path = backend.screenshot(screenshot)
        loaded = bool(snapshot.title.strip() or snapshot.text.strip())
        trace.verified = loaded
        trace.status = "success" if loaded else "failed"
        trace.final_evidence = {
            "reason": "Page loaded and readable content was extracted." if loaded else "No readable title or visible text extracted.",
            "url": snapshot.url,
            "title": snapshot.title,
            "headings": snapshot.headings or [],
            "visible_text_snippet": snapshot.text[:1000],
            "links_count": snapshot.links_count,
            "screenshot_path": screenshot_path,
        }
    except Exception as exc:
        trace.status = "failed"
        trace.verified = False
        trace.final_evidence = {"reason": str(exc), "url": url}
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass

    trace_path = TraceLogger().write(trace)
    return {
        "run_id": run_id,
        "status": trace.status,
        "verified": trace.verified,
        "trace_path": trace_path,
        **trace.final_evidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    result = run_readonly(args.url, args.task, args.screenshot)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
