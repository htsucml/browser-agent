"""Report writers for evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from browser_agent.schemas import EvalResult
from evals.failure_analysis import build_failure_analysis


def write_reports(results: list[EvalResult], output_dir: str | Path = "logs") -> tuple[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "eval_report.json"
    md_path = out / "eval_report.md"
    summary = _summary(results)
    payload = {
        "summary": summary,
        "results": [asdict(item) for item in results],
        "failure_analysis": build_failure_analysis(results),
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Eval Report",
        "",
        f"- Cases: {summary['total_cases']}",
        f"- Task passed: {summary['task_passed_count']} ({summary['task_passed_rate']:.2f})",
        f"- Verified successes: {summary['verified_success_count']}",
        f"- Correct refusals: {summary['correct_refusal_count']}",
        f"- False successes: {summary['false_success_count']}",
        f"- Unsafe actions: {summary['unsafe_action_count']}",
        "",
        "| Case | Expected | Actual | Verified Success | Correct Refusal | Task Passed | False Success | Unsafe Action | Steps | Browser SPL | Recovery Events | Maintenance Events |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item.case_id} | {item.expected_status} | {item.actual_status} | {item.verified_success} | "
            f"{item.correct_refusal} | {item.task_passed} | {item.false_success} | {item.unsafe_action} | "
            f"{item.num_steps} | {item.browser_spl} | {item.recovery_events_count} | {item.maintenance_events_count} |"
        )
    lines.extend(["", "## Failure Analysis", ""])
    for group, entries in payload["failure_analysis"]["groups"].items():
        lines.append(f"### {group}")
        for entry in entries:
            lines.append(f"- {entry['case_id']}: {entry['first_failure_category']} - {entry['first_failure_cause']} ({entry['suggested_owner_bucket']})")
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(json_path), str(md_path)


def _summary(results: list[EvalResult]) -> dict:
    spl_values = [item.browser_spl for item in results if item.browser_spl is not None]
    return {
        "total_cases": len(results),
        "num_cases": len(results),
        "task_passed_count": sum(1 for item in results if item.task_passed),
        "task_passed_rate": _rate(sum(1 for item in results if item.task_passed), len(results)),
        "verified_success_count": sum(1 for item in results if item.verified_success),
        "verified_successes": sum(1 for item in results if item.verified_success),
        "verified_success_rate": _rate(sum(1 for item in results if item.verified_success), len(results)),
        "false_success_count": sum(1 for item in results if item.false_success),
        "false_successes": sum(1 for item in results if item.false_success),
        "false_success_rate": _rate(sum(1 for item in results if item.false_success), len(results)),
        "unsafe_action_count": sum(1 for item in results if item.unsafe_action),
        "unsafe_action_rate": _rate(sum(1 for item in results if item.unsafe_action), len(results)),
        "correct_refusal_count": sum(1 for item in results if item.correct_refusal),
        "correct_refusal_rate": _rate(sum(1 for item in results if item.correct_refusal), len(results)),
        "average_steps": sum(item.num_steps for item in results) / len(results) if results else 0.0,
        "average_token_count": sum(item.token_count for item in results) / len(results) if results else 0.0,
        "average_browser_spl": sum(spl_values) / len(spl_values) if spl_values else None,
        "recovery_event_count": sum(item.recovery_events_count for item in results),
        "maintenance_event_count": sum(item.maintenance_events_count for item in results),
    }


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0
