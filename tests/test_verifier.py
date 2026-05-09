from browser_agent.browser import SimulatorBrowser
from browser_agent.schemas import ExpectedCheck
from browser_agent.verifier import Verifier
from simulator.state import SimulatorState


def test_verifier_passes_visible_text_and_state():
    state = SimulatorState()
    browser = SimulatorBrowser(state)
    browser.reset("simulator://shopping")
    browser.click("button:add-red-shoes")
    checks = [
        ExpectedCheck(type="visible_text", target="page", value="Cart: 1"),
        ExpectedCheck(type="simulator_state", target="cart_count", value=1),
    ]
    passed, results = Verifier().verify_all(checks, browser)
    assert passed is True
    assert all(item.passed for item in results)


def test_verifier_fails_wrong_state():
    state = SimulatorState()
    browser = SimulatorBrowser(state)
    browser.reset("simulator://shopping")
    check = ExpectedCheck(type="simulator_state", target="cart_count", value=1)
    result = Verifier().verify_one(check, browser)
    assert result.passed is False
    assert "observed 0" in result.reason
