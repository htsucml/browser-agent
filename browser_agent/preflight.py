"""Preflight guards that prevent unsafe or impossible form actions."""

from __future__ import annotations

import re

from browser_agent.browser import BrowserSnapshot
from browser_agent.planner import Plan, PlannedAction
from browser_agent.schemas import ExpectedCheck


EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def missing_required_info_plan(task: str, snapshot: BrowserSnapshot, expected: list[ExpectedCheck] | None = None) -> Plan | None:
    lowered = task.lower()
    text = snapshot.text.lower()
    if "support ticket" in lowered and "email is required" in text and not EMAIL_RE.search(task):
        reason = "The support form requires an email address, but the user did not provide one."
        return Plan(actions=[PlannedAction(action_type="needs_user", target_hint="", value=reason)], expected=expected or [], reason=reason)
    return None
