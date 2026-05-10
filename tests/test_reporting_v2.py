import json
from pathlib import Path

from browser_agent.agent import BrowserAgent
from browser_agent.display import build_display_result
from browser_agent.schemas import AgentTrace, FailureEvent
from evals.failure_analysis import build_failure_analysis
from evals.metrics import compute_result
from evals.run_ablation import run_ablation


def test_display_result_for_success():
    run = BrowserAgent().run("simulator://shopping", "Add Red Shoes to the cart")
    trace = json.loads(Path(run.trace_path).read_text(encoding="utf-8"))
    display = build_display_result(trace, run.trace_path)
    assert display.status == "success"
    assert display.verified is True
    assert "completed" in display.user_message.lower()
    assert display.metrics["planner_type"] == "rule"
    assert display.actions_summary


def test_display_result_for_needs_user():
    trace = AgentTrace(
        run_id="run_needs_user",
        case_id="support_validation_001",
        start_url="simulator://support",
        task="Submit ticket",
        status="needs_user",
        verified=False,
        final_evidence={"reason": "Email is required."},
    )
    display = build_display_result(trace, "trace.json")
    assert display.status == "needs_user"
    assert "needed" in display.user_message.lower()
    assert display.evidence_summary == "Email is required."


def test_failure_analysis_groups_failed_cases_deterministically(tmp_path):
    trace_path = tmp_path / "trace.json"
    trace = AgentTrace(
        run_id="run_failed",
        case_id="case_failed",
        start_url="simulator://shopping",
        task="Do thing",
        status="failed",
        verified=False,
    )
    trace.failures = [FailureEvent(category="locator_error", cause="Target not found.")]
    trace_path.write_text(json.dumps(trace.to_dict()), encoding="utf-8")
    result = compute_result("case_failed", trace, str(trace_path), checker_passed=False, expected_status="success")
    analysis = build_failure_analysis([result])
    assert analysis["total_failed_cases"] == 1
    assert "locator_error" in analysis["groups"]
    assert analysis["groups"]["locator_error"][0]["suggested_owner_bucket"] == "recovery"


def test_ablation_runner_runs_rule_and_fake_llm_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = run_ablation("evals/cases_llm_smoke.json", ["rule", "llm_fake"])
    assert [item["config"] for item in report["configs"]] == ["rule", "llm_fake"]
    assert Path("logs/ablation_report.json").exists()
    assert Path("logs/ablation_report.md").exists()
