"""Basic deterministic safety gate."""

from __future__ import annotations

from browser_agent.schemas import SafetyEvent


class SafetyPolicy:
    BLOCKED_TERMS = ("password", "payment", "credit card", "delete account", "delete my account")

    def check(self, task: str) -> SafetyEvent:
        lowered = task.lower()
        for term in self.BLOCKED_TERMS:
            if term in lowered:
                return SafetyEvent(kind="task_screen", decision="refused", reason=f"Blocked term: {term}")
        return SafetyEvent(kind="task_screen", decision="allowed", reason="No blocked terms detected.")
