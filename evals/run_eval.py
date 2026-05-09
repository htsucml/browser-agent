"""Offline evaluator entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from browser_agent.agent import BrowserAgent
from browser_agent.schemas import (
    ActionRecord,
    AgentTrace,
    EvalCase,
    FailureEvent,
    MaintenanceEvent,
    RecoveryEvent,
    SafetyEvent,
    VerificationResult,
)
from evals.checkers import evaluate_expected
from evals.metrics import compute_result
from evals.report import write_reports


def load_cases(path: str | Path) -> list[EvalCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvalCase.from_dict(item) for item in data]


def load_trace(path: str | Path) -> AgentTrace:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    trace = AgentTrace(
        run_id=data["run_id"],
        case_id=data.get("case_id"),
        start_url=data["start_url"],
        task=data["task"],
        status=data["status"],
        verified=data["verified"],
        final_evidence=data.get("final_evidence", {}),
        token_count=data.get("token_count", 0),
        cost_usd=data.get("cost_usd", 0.0),
        started_at=data.get("started_at"),
        finished_at=data.get("finished_at"),
    )
    trace.actions = [ActionRecord(**item) for item in data.get("actions", [])]
    trace.verifications = [VerificationResult(**item) for item in data.get("verifications", [])]
    trace.failures = [FailureEvent(**item) for item in data.get("failures", [])]
    trace.recoveries = [RecoveryEvent(**item) for item in data.get("recoveries", [])]
    trace.maintenance_events = [MaintenanceEvent(**item) for item in data.get("maintenance_events", [])]
    trace.safety_events = [SafetyEvent(**item) for item in data.get("safety_events", [])]
    return trace


def run_eval(cases_path: str | Path) -> list:
    cases = load_cases(cases_path)
    results = []
    for case in cases:
        agent = BrowserAgent()
        run = agent.run_case(case)
        trace = load_trace(run.trace_path)
        checker_passed = evaluate_expected(case, agent.state, trace)
        results.append(
            compute_result(
                case.id,
                trace,
                run.trace_path,
                checker_passed,
                expected_status=case.expected_status,
                reference_path=case.reference_path,
            )
        )
    write_reports(results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="evals/cases.json")
    args = parser.parse_args()
    results = run_eval(args.cases)
    print(json.dumps({"cases": len(results), "verified_successes": sum(item.verified_success for item in results)}, indent=2))


if __name__ == "__main__":
    main()
