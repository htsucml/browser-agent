"""Fake support form site with deterministic validation."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.state import SimulatorState


class SupportPage:
    def __init__(self, state: "SimulatorState"):
        self.state = state
        self.inputs = state.inputs

    def text(self) -> str:
        validation = " Email is required. " if self.state.variant == "validation_required" else " "
        return f"Support Ticket Email Message Submit{validation}"

    def elements(self) -> dict[str, dict[str, Any]]:
        return {
            "input:support-email": {"role": "textbox", "label": "Email", "aliases": ["email"]},
            "textarea:support-message": {"role": "textbox", "label": "Message", "aliases": ["message"]},
            "button:submit-ticket": {"role": "button", "label": "Submit ticket", "aliases": ["submit support ticket"]},
        }

    def click(self, selector: str) -> dict[str, Any]:
        if selector != "button:submit-ticket":
            return {"ok": False, "reason": f"Unknown clickable selector {selector}"}
        email = self.state.inputs.get("input:support-email", "")
        message = self.state.inputs.get("textarea:support-message", "")
        self.state.actions_taken.append("support:submit_attempt")
        if not email:
            return {"ok": False, "reason": "validation_error: email_required"}
        self.state.support_tickets.append({"email": email, "message": message})
        return {"ok": True, "effect": "support_ticket_created"}

    def fill(self, selector: str, value: str) -> dict[str, Any]:
        if selector in {"input:support-email", "textarea:support-message"}:
            self.state.inputs[selector] = value
            return {"ok": True, "effect": "input_filled", "value": value}
        return {"ok": False, "reason": f"Unknown input selector {selector}"}
