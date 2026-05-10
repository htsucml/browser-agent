"""Run deterministic evals across planner configurations."""

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from browser_agent.redaction import redact_secrets
from evals.failure_analysis import build_failure_analysis
from evals.report import _summary
from evals.run_eval import run_eval


CONFIG_ENVS = {
    "rule": {"PLANNER": "rule"},
    "llm_fake": {"PLANNER": "llm", "LLM_PROVIDER": "fake"},
    "llm_openai": {
        "PLANNER": "llm",
        "LLM_PROVIDER": "openai",
        "MAX_LLM_CALLS_PER_RUN": "1",
        "MAX_STEPS": "3",
        "MAX_OUTPUT_TOKENS": "300",
        "REQUEST_TIMEOUT_SECONDS": "30",
    },
}


def run_ablation(cases: str, configs: list[str], output_dir: str | Path = "logs", allow_paid: bool = False) -> dict:
    reports = []
    for config_name in configs:
        if config_name not in CONFIG_ENVS:
            raise ValueError(f"Unsupported ablation config: {config_name}")
        skip_reason = _skip_reason(config_name, allow_paid)
        if skip_reason:
            reports.append(_skipped_config(config_name, skip_reason))
            continue
        updates = dict(CONFIG_ENVS[config_name])
        if config_name == "llm_openai":
            updates["LLM_MODEL"] = os.environ.get("LLM_MODEL", "gpt-4.1-nano")
        with _patched_env(updates):
            results = run_eval(cases)
        summary = _summary(results)
        reports.append(
            {
                "config": config_name,
                "status": "completed",
                "summary": {
                    "total_cases": summary["total_cases"],
                    "task_passed_count": summary["task_passed_count"],
                    "task_passed_rate": summary["task_passed_rate"],
                    "verified_success_count": summary["verified_success_count"],
                    "verified_success_rate": summary["verified_success_rate"],
                    "correct_refusal_count": summary["correct_refusal_count"],
                    "correct_refusal_rate": summary["correct_refusal_rate"],
                    "false_success_count": summary["false_success_count"],
                    "false_success_rate": summary["false_success_rate"],
                    "unsafe_action_count": summary["unsafe_action_count"],
                    "unsafe_action_rate": summary["unsafe_action_rate"],
                    "average_steps": summary["average_steps"],
                    "average_token_count": summary["average_token_count"],
                    "average_browser_spl": summary["average_browser_spl"],
                    "total_token_count": sum(item.token_count for item in results),
                    "total_llm_call_count": _total_llm_calls(results),
                },
                "results": [asdict(item) for item in results],
                "failure_analysis": build_failure_analysis(results),
            }
        )
    payload = {"cases": cases, "configs": reports, "case_comparison": _case_comparison(reports)}
    _write_ablation_report(payload, output_dir)
    return payload


def _write_ablation_report(payload: dict, output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ablation_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Ablation Report",
        "",
        "| Config | Status | Cases | Task Passed | Verified Success | Correct Refusals | False Successes | Unsafe Actions | Avg Steps | Avg Tokens | Total Tokens | LLM Calls | Avg SPL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for config in payload["configs"]:
        if config["status"] == "skipped":
            lines.append(f"| {config['config']} | skipped: {config['skip_reason']} | 0 | - | - | - | - | - | - | - | - | - | - |")
            continue
        summary = config["summary"]
        lines.append(
            f"| {config['config']} | completed | {summary['total_cases']} | {summary['task_passed_count']} "
            f"({summary['task_passed_rate']:.2f}) | {summary['verified_success_count']} "
            f"({summary['verified_success_rate']:.2f}) | {summary['correct_refusal_count']} "
            f"({summary['correct_refusal_rate']:.2f}) | {summary['false_success_count']} "
            f"({summary['false_success_rate']:.2f}) | {summary['unsafe_action_count']} "
            f"({summary['unsafe_action_rate']:.2f}) | {summary['average_steps']:.2f} | "
            f"{summary['average_token_count']:.2f} | {summary['total_token_count']} | {summary['total_llm_call_count']} | "
            f"{summary['average_browser_spl']} |"
        )
    lines.extend(["", "## Per-Case Comparison", ""])
    configs = [config["config"] for config in payload["configs"]]
    header = "| Case | Expected | " + " | ".join(f"{config} status/pass" for config in configs) + " |"
    separator = "| --- | --- | " + " | ".join("---" for _ in configs) + " |"
    lines.extend([header, separator])
    for row in payload["case_comparison"]:
        cells = [row["case_id"], row["expected_status"]]
        for config in configs:
            item = row.get(config)
            cells.append("-" if item is None else f"{item['actual_status']} / {item['task_passed']}")
        lines.append("| " + " | ".join(cells) + " |")
    (out / "ablation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _skip_reason(config_name: str, allow_paid: bool) -> str | None:
    if config_name != "llm_openai":
        return None
    if not allow_paid:
        return "requires --allow-paid"
    if not os.environ.get("OPENAI_API_KEY"):
        return "OPENAI_API_KEY is required"
    return None


def _skipped_config(config_name: str, reason: str) -> dict:
    return {
        "config": config_name,
        "status": "skipped",
        "skip_reason": redact_secrets(reason),
        "summary": {},
        "results": [],
        "failure_analysis": {"total_failed_cases": 0, "groups": {}},
    }


def _total_llm_calls(results) -> int:
    total = 0
    for result in results:
        try:
            data = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        except OSError:
            continue
        total += int(data.get("llm_call_count", 0))
    return total


def _case_comparison(reports: list[dict]) -> list[dict]:
    order: list[str] = []
    rows: dict[str, dict] = {}
    for report in reports:
        config_name = report["config"]
        for result in report.get("results", []):
            case_id = result["case_id"]
            if case_id not in rows:
                order.append(case_id)
                rows[case_id] = {"case_id": case_id, "expected_status": result["expected_status"]}
            rows[case_id][config_name] = {
                "actual_status": result["actual_status"],
                "task_passed": result["task_passed"],
                "verified_success": result["verified_success"],
                "correct_refusal": result["correct_refusal"],
            }
    return [rows[case_id] for case_id in order]


@contextmanager
def _patched_env(updates: dict[str, str]):
    old = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--configs", default="rule,llm_fake")
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    configs = [item.strip() for item in args.configs.split(",") if item.strip()]
    payload = run_ablation(args.cases, configs, allow_paid=args.allow_paid)
    print(
        json.dumps(
            {"cases": args.cases, "configs": [{"name": item["config"], "status": item["status"]} for item in payload["configs"]]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
