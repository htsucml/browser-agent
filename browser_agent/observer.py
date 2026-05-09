"""Observation layer for collecting current browser state."""

from __future__ import annotations

from browser_agent.browser import BrowserSnapshot, SimulatorBrowser


class Observer:
    def observe(self, browser: SimulatorBrowser) -> BrowserSnapshot:
        return browser.snapshot()
