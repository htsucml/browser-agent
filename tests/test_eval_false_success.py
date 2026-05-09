from browser_agent.schemas import AgentTrace
from evals.metrics import compute_result


def test_evaluator_detects_false_success_when_claim_is_unverified():
    trace = AgentTrace(
        run_id="run_false",
        case_id="case_false",
        start_url="simulator://shopping",
        task="Add Blue Hat",
        status="success",
        verified=False,
    )
    result = compute_result("case_false", trace, "logs/runs/run_false.json", checker_passed=False)
    assert result.verified_success is False
    assert result.false_success is True


def test_agent_does_not_claim_success_without_verification():
    from browser_agent.agent import BrowserAgent
    from browser_agent.schemas import ExpectedCheck

    result = BrowserAgent().run(
        "simulator://shopping",
        "Add Blue Hat to the cart",
        expected=[ExpectedCheck(type="simulator_state", target="cart_items", value=["Blue Hat"])],
    )
    assert result.verified is False
    assert result.status == "failed"
