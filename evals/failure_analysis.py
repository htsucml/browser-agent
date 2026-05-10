"""Deterministic failure grouping for eval reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from browser_agent.schemas import EvalResult


def build_failure_analysis(results: list[EvalResult]) -> dict[str, Any]:
    failures = [result for result in results if not (result.verified_success or result.correct_refusal)]
    groups: dict[str, list[dict[str, Any]]] = {}
    for result in failures:
        trace = _load_trace(result.trace_path)
        category, cause = _first_failure(trace)
        group = _normalize_category(category, result)
        entry = {
            "case_id": result.case_id,
            "expected_status": result.expected_status,
            "actual_status": result.actual_status,
            "failed_checks": _failed_checks(trace),
            "first_failure_category": category,
            "first_failure_cause": cause,
            "trace_path": result.trace_path,
            "suggested_owner_bucket": _owner_bucket(group, trace),
        }
        groups.setdefault(group, []).append(entry)
    return {
        "total_failed_cases": len(failures),
        "groups": {key: sorted(value, key=lambda item: item["case_id"]) for key, value in sorted(groups.items())},
    }


def _load_trace(path: str) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}


def _first_failure(trace: dict[str, Any]) -> tuple[str, str]:
    failures = trace.get("failures", []) or []
    if failures:
        failure = failures[0]
        return str(failure.get("category", "unknown")), str(failure.get("cause", ""))
    if trace.get("status") in {"needs_user", "refused"}:
        return "safety/refusal mismatch", str((trace.get("final_evidence") or {}).get("reason", ""))
    return "verification_error", "No explicit failure event recorded."


def _failed_checks(trace: dict[str, Any]) -> list[str]:
    checks = []
    for verification in trace.get("verifications", []) or []:
        if not verification.get("passed", False):
            checks.append(str(verification.get("reason", "")))
    return checks


def _normalize_category(category: str, result: EvalResult) -> str:
    if result.false_success:
        return "false_success"
    if result.unsafe_action:
        return "unsafe_action"
    if result.expected_status == "needs_user" and result.actual_status not in {"needs_user", "refused"}:
        return "safety/refusal mismatch"
    if category in {"action_error", "planning_error", "verification_error", "locator_error"}:
        return category
    cause = category.lower()
    if "unsupported" in cause:
        return "unsupported_action"
    if "destination" in cause:
        return "wrong_destination"
    if "item" in cause or "target" in cause:
        return "wrong_item"
    return category or "unknown"


def _owner_bucket(group: str, trace: dict[str, Any]) -> str:
    if group == "planning_error":
        return "planner"
    if group in {"wrong_destination", "wrong_item"}:
        return "action_candidates"
    if group in {"action_error", "unsupported_action"}:
        return "executor"
    if group == "locator_error":
        return "recovery"
    if group == "verification_error":
        return "verifier"
    if group == "safety/refusal mismatch":
        return "prompt"
    if group in {"unsafe_action", "false_success"}:
        return "verifier"
    if trace.get("planner_type") == "llm":
        return "prompt"
    return "planner"
