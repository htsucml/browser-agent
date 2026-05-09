"""Deterministic runtime verification checks."""

from __future__ import annotations

from typing import Any

from browser_agent.browser import BrowserSnapshot, SimulatorBrowser
from browser_agent.schemas import ExpectedCheck, VerificationResult


class Verifier:
    def verify_one(self, check: ExpectedCheck, browser: SimulatorBrowser) -> VerificationResult:
        snapshot = browser.snapshot()
        observed: Any = None
        passed = False

        if check.type == "visible_text":
            observed = snapshot.text
            passed = str(check.value) in snapshot.text
        elif check.type == "url_contains":
            observed = snapshot.url
            passed = str(check.value) in snapshot.url
        elif check.type == "input_value":
            observed = snapshot.inputs.get(check.target)
            passed = observed == check.value
        elif check.type == "simulator_state":
            observed = snapshot.state.get(check.target)
            passed = observed == check.value
        elif check.type == "cart_contains_item_matching":
            observed = snapshot.state.get("cart_items", [])
            passed = _collection_contains_matching(observed, snapshot.state.get("catalog", []), check.value)
        elif check.type == "settings_state_equals":
            observed = snapshot.state.get("settings", {}).get(check.target)
            passed = observed == check.value
        elif check.type == "support_ticket_contains":
            observed = snapshot.state.get("support_tickets", [])
            passed = any(_ticket_matches(ticket, check.value) for ticket in observed)

        reason = "Verification passed." if passed else f"Expected {check.value!r}, observed {observed!r}."
        return VerificationResult(
            passed=passed,
            check_type=check.type,
            target=check.target,
            expected=check.value,
            observed=observed,
            reason=reason,
        )

    def verify_all(self, checks: list[ExpectedCheck], browser: SimulatorBrowser) -> tuple[bool, list[VerificationResult]]:
        results = [self.verify_one(check, browser) for check in checks]
        return bool(results) and all(result.passed for result in results), results


def check_snapshot(check: ExpectedCheck, snapshot: BrowserSnapshot) -> bool:
    if check.type == "visible_text":
        return str(check.value) in snapshot.text
    if check.type == "url_contains":
        return str(check.value) in snapshot.url
    if check.type == "input_value":
        return snapshot.inputs.get(check.target) == check.value
    if check.type == "simulator_state":
        return snapshot.state.get(check.target) == check.value
    if check.type == "cart_contains_item_matching":
        return _collection_contains_matching(snapshot.state.get("cart_items", []), snapshot.state.get("catalog", []), check.value)
    if check.type == "settings_state_equals":
        return snapshot.state.get("settings", {}).get(check.target) == check.value
    if check.type == "support_ticket_contains":
        return any(_ticket_matches(ticket, check.value) for ticket in snapshot.state.get("support_tickets", []))
    return False


def _item_matches(item: dict[str, Any], spec: dict[str, Any]) -> bool:
    if not isinstance(spec, dict):
        return False
    if "name" in spec and item.get("name") != spec["name"]:
        return False
    if "category" in spec and item.get("category") != spec["category"]:
        return False
    if "price_lte" in spec and item.get("price", 0) > spec["price_lte"]:
        return False
    if "rating_gte" in spec and item.get("rating", 0) < spec["rating_gte"]:
        return False
    return True


def _collection_contains_matching(names: list[str], catalog: list[dict[str, Any]], spec: dict[str, Any]) -> bool:
    selected = [item for item in catalog if item.get("name") in names]
    return any(_item_matches(item, spec) for item in selected)


def _ticket_matches(ticket: dict[str, str], spec: dict[str, str]) -> bool:
    if not isinstance(spec, dict):
        return False
    if "email" in spec and ticket.get("email") != spec["email"]:
        return False
    if "message_contains" in spec and spec["message_contains"].lower() not in ticket.get("message", "").lower():
        return False
    return True
