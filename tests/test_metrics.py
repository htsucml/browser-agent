from browser_agent.schemas import ActionRecord, AgentTrace
from evals.metrics import compute_result


def test_metrics_for_verified_success():
    trace = AgentTrace(
        run_id="run_1",
        case_id="case_1",
        start_url="simulator://shopping",
        task="Add Red Shoes",
        status="success",
        verified=True,
    )
    trace.actions = [ActionRecord(step=1, action_type="click", target="button:add-red-shoes")]
    result = compute_result("case_1", trace, "logs/runs/run_1.json", checker_passed=True, reference_path=["add"])
    assert result.verified_success is True
    assert result.task_passed is True
    assert result.false_success is False
    assert result.browser_spl == 1.0


def test_action_counting_excludes_needs_user_from_browser_steps():
    trace = AgentTrace(
        run_id="run_2",
        case_id="case_2",
        start_url="simulator://support",
        task="Need missing info",
        status="needs_user",
        verified=False,
    )
    trace.actions = [ActionRecord(step=1, action_type="needs_user", target="user", status="skipped")]
    result = compute_result("case_2", trace, "logs/runs/run_2.json", checker_passed=True, expected_status="needs_user")
    assert result.num_steps == 0
    assert result.actual_steps == 0
    assert result.counts_for_spl == 0
    assert result.browser_spl is None
    assert result.correct_refusal is True
    assert result.task_passed is True


def test_failed_case_has_task_passed_false():
    trace = AgentTrace(
        run_id="run_3",
        case_id="case_3",
        start_url="simulator://shopping",
        task="Fail",
        status="failed",
        verified=False,
    )
    result = compute_result("case_3", trace, "logs/runs/run_3.json", checker_passed=False)
    assert result.task_passed is False


def test_false_success_visible_and_not_task_passed():
    trace = AgentTrace(
        run_id="run_4",
        case_id="case_4",
        start_url="simulator://shopping",
        task="False success",
        status="success",
        verified=False,
    )
    result = compute_result("case_4", trace, "logs/runs/run_4.json", checker_passed=False)
    assert result.false_success is True
    assert result.task_passed is False
