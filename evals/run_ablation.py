"""Run deterministic evals across planner configurations."""

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from evals.report import _summary
from evals.run_eval import run_eval


CONFIG_ENVS = {
    "rule": {"PLANNER": "rule"},
    "llm_fake": {"PLANNER": "llm", "LLM_PROVIDER": "fake"},
}


def run_ablation(cases: str, configs: list[str], output_dir: str | Path = "logs") -> dict:
    reports = []
    for config_name in configs:
        if config_name not in CONFIG_ENVS:
            raise ValueError(f"Unsupported ablation config: {config_name}")
        with _patched_env(CONFIG_ENVS[config_name]):
            results = run_eval(cases)
        summary = _summary(results)
        reports.append(
            {
                "config": config_name,
                "summary": {
                    "total_cases": summary["total_cases"],
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
                },
                "results": [asdict(item) for item in results],
            }
        )
    payload = {"cases": cases, "configs": reports}
    _write_ablation_report(payload, output_dir)
    return payload


def _write_ablation_report(payload: dict, output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ablation_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Ablation Report",
        "",
        "| Config | Cases | Verified | Correct Refusals | False Successes | Unsafe Actions | Avg Steps | Avg Tokens | Avg SPL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for config in payload["configs"]:
        summary = config["summary"]
        lines.append(
            f"| {config['config']} | {summary['total_cases']} | {summary['verified_success_count']} "
            f"({summary['verified_success_rate']:.2f}) | {summary['correct_refusal_count']} "
            f"({summary['correct_refusal_rate']:.2f}) | {summary['false_success_count']} "
            f"({summary['false_success_rate']:.2f}) | {summary['unsafe_action_count']} "
            f"({summary['unsafe_action_rate']:.2f}) | {summary['average_steps']:.2f} | "
            f"{summary['average_token_count']:.2f} | {summary['average_browser_spl']} |"
        )
    (out / "ablation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    args = parser.parse_args()
    configs = [item.strip() for item in args.configs.split(",") if item.strip()]
    payload = run_ablation(args.cases, configs)
    print(json.dumps({"cases": args.cases, "configs": [item["config"] for item in payload["configs"]]}, indent=2))


if __name__ == "__main__":
    main()
