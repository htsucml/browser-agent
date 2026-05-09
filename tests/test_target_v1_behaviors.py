import json
from pathlib import Path

from browser_agent.agent import BrowserAgent
from browser_agent.schemas import EvalCase
from evals.checkers import evaluate_expected


def _case(case_id: str) -> EvalCase:
    data = json.loads(Path("evals/cases_v1.json").read_text(encoding="utf-8"))
    return EvalCase.from_dict(next(item for item in data if item["id"] == case_id))


def test_settings_safe_weekly_summary_passes_runtime_verification():
    case = _case("settings_safe_001")
    agent = BrowserAgent()
    result = agent.run_case(case)
    assert result.status == "success"
    assert result.verified is True
    assert evaluate_expected(case, agent.state) is True


def test_support_form_with_explicit_email_passes_runtime_verification():
    case = _case("support_form_001")
    agent = BrowserAgent()
    result = agent.run_case(case)
    assert result.status == "success"
    assert result.verified is True
    assert evaluate_expected(case, agent.state) is True


def test_shopping_normal_constraint_item_passes_runtime_verification():
    case = _case("shopping_normal_001")
    agent = BrowserAgent()
    result = agent.run_case(case)
    assert result.status == "success"
    assert result.verified is True
    assert evaluate_expected(case, agent.state) is True
