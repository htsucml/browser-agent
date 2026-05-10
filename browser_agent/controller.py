"""Action execution layer."""

from __future__ import annotations

from browser_agent.browser import SimulatorBrowser


class Controller:
    def act(self, browser: SimulatorBrowser, action_type: str, selector: str, value: str | None = None) -> dict:
        if action_type == "select":
            action_type = "click"
        if action_type == "click":
            return browser.click(selector)
        if action_type == "fill":
            return browser.fill(selector, value or "")
        return {"ok": False, "reason": f"Unsupported action: {action_type}"}
