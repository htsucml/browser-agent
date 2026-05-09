from browser_agent.schemas import AgentTrace
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
    result = compute_result("case_1", trace, "logs/runs/run_1.json", checker_passed=True)
    assert result.verified_success is True
    assert result.false_success is False
    assert result.browser_spl == 1.0
