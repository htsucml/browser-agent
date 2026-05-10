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


def test_display_result_formats_list_answer_as_lines():
    trace = AgentTrace(
        run_id="readonly_list_answer",
        case_id=None,
        start_url="https://example.com",
        task="Summarize",
        status="success",
        verified=True,
        final_evidence={
            "reason": "Page loaded.",
            "url": "https://example.com",
            "title": "Example",
            "llm_answer": ["- First point", "- Second point"],
        },
    )

    display = build_display_result(trace, "trace.json")

    assert display.answer_lines == ["- First point", "- Second point"]
    assert display.answer == "- First point\n- Second point"


def test_display_result_formats_serialized_list_answer_as_lines():
    trace = AgentTrace(
        run_id="readonly_serialized_list_answer",
        case_id=None,
        start_url="https://example.com",
        task="Summarize",
        status="success",
        verified=True,
        final_evidence={
            "reason": "Page loaded.",
            "url": "https://example.com",
            "title": "Example",
            "llm_answer": "['- Alpha', '- Beta']",
        },
    )

    display = build_display_result(trace, "trace.json")

    assert display.answer_lines == ["- Alpha", "- Beta"]
    assert display.answer == "- Alpha\n- Beta"


def test_display_result_formats_markdown_bullets_as_lines():
    trace = AgentTrace(
        run_id="readonly_markdown_bullets",
        case_id=None,
        start_url="https://example.com",
        task="Summarize",
        status="success",
        verified=True,
        final_evidence={
            "reason": "Page loaded.",
            "url": "https://example.com",
            "title": "Example",
            "llm_answer": "- First complete point.\n- Second complete point.",
        },
    )

    display = build_display_result(trace, "trace.json")

    assert display.answer_lines == ["- First complete point.", "- Second complete point."]
    assert display.answer == "- First complete point.\n- Second complete point."


def test_display_result_splits_collapsed_inline_bullets():
    trace = AgentTrace(
        run_id="readonly_collapsed_bullets",
        case_id=None,
        start_url="https://example.com",
        task="Summarize",
        status="success",
        verified=True,
        final_evidence={
            "reason": "Page loaded.",
            "url": "https://example.com",
            "title": "Example",
            "llm_answer": "- item one - item two - item three",
        },
    )

    display = build_display_result(trace, "trace.json")

    assert display.answer_lines == ["- item one", "- item two", "- item three"]
    assert display.answer == "- item one\n- item two\n- item three"


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


def test_failure_analysis_excludes_correct_refusal(tmp_path):
    trace_path = tmp_path / "needs_user_trace.json"
    trace = AgentTrace(
        run_id="run_needs",
        case_id="support_validation_001",
        start_url="simulator://support",
        task="Need email",
        status="needs_user",
        verified=False,
    )
    trace_path.write_text(json.dumps(trace.to_dict()), encoding="utf-8")
    result = compute_result(
        "support_validation_001",
        trace,
        str(trace_path),
        checker_passed=True,
        expected_status="needs_user",
    )
    analysis = build_failure_analysis([result])
    assert result.task_passed is True
    assert analysis["total_failed_cases"] == 0
    assert analysis["groups"] == {}


def test_ablation_runner_runs_rule_and_fake_llm_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = run_ablation("evals/cases_llm_smoke.json", ["rule", "llm_fake"])
    assert [item["config"] for item in report["configs"]] == ["rule", "llm_fake"]
    assert all(item["status"] == "completed" for item in report["configs"])
    assert Path("logs/ablation_report.json").exists()
    assert Path("logs/ablation_report.md").exists()


def test_ablation_skips_openai_without_allow_paid(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = run_ablation("evals/cases_llm_smoke.json", ["llm_openai"], allow_paid=False)
    assert report["configs"][0]["status"] == "skipped"
    assert report["configs"][0]["skip_reason"] == "requires --allow-paid"


def test_ablation_skips_openai_without_key_when_paid_allowed(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = run_ablation("evals/cases_llm_smoke.json", ["llm_openai"], allow_paid=True)
    assert report["configs"][0]["status"] == "skipped"
    assert report["configs"][0]["skip_reason"] == "OPENAI_API_KEY is required"


def test_ablation_report_includes_metrics_and_case_comparison(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = run_ablation("evals/cases_llm_smoke.json", ["rule", "llm_fake", "llm_openai"])
    completed = [item for item in report["configs"] if item["status"] == "completed"]
    for config in completed:
        summary = config["summary"]
        for field in [
            "task_passed_count",
            "verified_success_count",
            "correct_refusal_count",
            "false_success_count",
            "unsafe_action_count",
            "total_token_count",
            "total_llm_call_count",
        ]:
            assert field in summary
    assert report["case_comparison"]
    report_text = Path("logs/ablation_report.md").read_text(encoding="utf-8")
    assert "Per-Case Comparison" in report_text
    assert "Task Passed" in report_text
    assert "skipped: requires --allow-paid" in report_text


def test_ablation_report_does_not_include_api_key_like_string(monkeypatch):
    secret = "sk-testAblationShouldNotAppear123456"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    report = run_ablation("evals/cases_llm_smoke.json", ["llm_openai"], allow_paid=False)
    payload = json.dumps(report) + Path("logs/ablation_report.md").read_text(encoding="utf-8")
    assert secret not in payload
