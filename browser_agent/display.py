"""User-facing result summaries for app output."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from browser_agent.schemas import AgentTrace


@dataclass
class AgentDisplayResult:
    status: str
    verified: bool
    user_message: str
    answer: str | None
    source_url: str | None
    page_title: str | None
    evidence_summary: str
    actions_summary: list[str]
    safety_summary: str
    metrics: dict[str, Any]
    trace_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_display_result(trace: AgentTrace | dict[str, Any], trace_path: str = "") -> AgentDisplayResult:
    data = trace if isinstance(trace, dict) else trace.to_dict()
    status = str(data.get("status", "failed"))
    verified = bool(data.get("verified", False))
    final_evidence = data.get("final_evidence", {}) or {}
    reason = str(final_evidence.get("reason") or "")
    answer = final_evidence.get("llm_answer")
    source_url = final_evidence.get("url")
    page_title = final_evidence.get("title")
    if status == "success" and verified:
        user_message = "Read-only answer generated from page evidence." if answer else "Task completed and verified."
    elif status == "needs_user":
        user_message = "More information or confirmation is needed."
    elif status == "refused":
        user_message = "The task was refused for safety."
    else:
        user_message = "Task did not complete successfully."

    actions = data.get("actions", []) or []
    safety_events = data.get("safety_events", []) or []
    return AgentDisplayResult(
        status=status,
        verified=verified,
        user_message=user_message,
        answer=str(answer) if answer is not None else None,
        source_url=str(source_url) if source_url is not None else None,
        page_title=str(page_title) if page_title is not None else None,
        evidence_summary=reason or _summarize_evidence(final_evidence),
        actions_summary=[_summarize_action(action) for action in actions],
        safety_summary=_summarize_safety(safety_events),
        metrics={
            "steps": sum(1 for action in actions if action.get("action_type") not in {"needs_user", "stop"} and action.get("status") != "skipped"),
            "llm_call_count": data.get("llm_call_count", 0),
            "token_count": data.get("token_count", 0),
            "model": data.get("llm_model"),
            "planner_type": data.get("planner_type", "rule"),
        },
        trace_path=trace_path,
    )


def _summarize_action(action: dict[str, Any]) -> str:
    return f"{action.get('action_type')} -> {action.get('target')} ({action.get('status')})"


def _summarize_safety(events: list[dict[str, Any]]) -> str:
    if not events:
        return "No safety events recorded."
    refused = [event for event in events if event.get("decision") == "refused"]
    if refused:
        return str(refused[0].get("reason") or "Safety policy refused the task.")
    return "Safety checks passed."


def _summarize_evidence(evidence: dict[str, Any]) -> str:
    if "title" in evidence:
        return f"Read page: {evidence.get('title')}"
    if "url" in evidence:
        return f"Final URL: {evidence.get('url')}"
    return "No evidence summary available."
