"""Recovery hooks for failed planning, locating, acting, or verification."""

from __future__ import annotations

from browser_agent.schemas import RecoveryEvent


class Recovery:
    def record_noop(self, reason: str, step: int | None = None) -> RecoveryEvent:
        return RecoveryEvent(strategy="noop_placeholder", status="failed", reason=reason, step=step)
