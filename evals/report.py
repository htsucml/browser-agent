"""Report writers for evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from browser_agent.schemas import EvalResult


def write_reports(results: list[EvalResult], output_dir: str | Path = "logs") -> tuple[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "eval_report.json"
    md_path = out / "eval_report.md"
    payload = {
        "summary": {
            "total_cases": len(results),
            "num_cases": len(results),
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
            "recovery_event_count": sum(item.recovery_events_count for item in results),
            "maintenance_event_count": sum(item.maintenance_events_count for item in results),
        },
        "results": [asdict(item) for item in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Eval Report",
        "",
        f"- Cases: {payload['summary']['total_cases']}",
        f"- Verified successes: {payload['summary']['verified_success_count']}",
        f"- False successes: {payload['summary']['false_success_count']}",
        "",
        "| Case | Expected | Actual | Verified Success | False Success | Steps | Recovery Events | Maintenance Events |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item.case_id} | {item.expected_status} | {item.actual_status} | {item.verified_success} | "
            f"{item.false_success} | {item.num_steps} | {item.recovery_events_count} | {item.maintenance_events_count} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(json_path), str(md_path)


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0
