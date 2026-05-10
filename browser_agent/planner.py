"""Rule-based fake planner used to exercise the runtime flow."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from browser_agent.browser import BrowserSnapshot
from browser_agent.schemas import ExpectedCheck


@dataclass
class PlannedAction:
    action_type: str
    target_hint: str
    value: str | None = None


@dataclass
class Plan:
    actions: list[PlannedAction]
    expected: list[ExpectedCheck]
    reason: str


class RulePlanner:
    """Tiny deterministic stand-in for a future LLM planner."""

    def plan(self, task: str, snapshot: BrowserSnapshot, expected: list[ExpectedCheck] | None = None) -> Plan:
        lowered = task.lower()
        expected = expected or []
        if "weekly summary emails" in lowered and any(word in lowered for word in ("turn on", "enable")):
            return Plan(
                actions=[PlannedAction(action_type="click", target_hint="turn on weekly summary emails")],
                expected=expected,
                reason="Rule matched safe settings toggle task.",
            )

        if "support ticket" in lowered and "email" in lowered:
            email = self._extract_email(task)
            message = self._extract_support_message(task)
            if email and message:
                return Plan(
                    actions=[
                        PlannedAction(action_type="fill", target_hint="email", value=email),
                        PlannedAction(action_type="fill", target_hint="message", value=message),
                        PlannedAction(action_type="click", target_hint="submit support ticket"),
                    ],
                    expected=expected,
                    reason="Rule matched support ticket form task with explicit email and message.",
                )

        if "wishlist" in lowered and any(word in lowered for word in ("cheapest", "least expensive", "lowest price")):
            product = self._choose_wishlist_product(task, snapshot, expected)
            if product:
                return Plan(
                    actions=[PlannedAction(action_type="click", target_hint=f"save {product} to wishlist")],
                    expected=expected,
                    reason="Rule matched cheapest wishlist shopping task.",
                )

        if "add" in lowered and "cart" in lowered:
            product = self._choose_cart_product(task, snapshot, expected)
            return Plan(
                actions=[PlannedAction(action_type="click", target_hint=f"add {product} to cart")],
                expected=expected or [ExpectedCheck(type="simulator_state", target="cart_count", value=1)],
                reason="Rule matched add-to-cart shopping task.",
            )
        return Plan(actions=[], expected=expected, reason="No rule matched; safe failure.")

    def _choose_cart_product(self, task: str, snapshot: BrowserSnapshot, expected: list[ExpectedCheck]) -> str:
        for check in expected:
            if check.type == "cart_contains_item_matching" and isinstance(check.value, dict):
                item = self._first_catalog_match(snapshot.state.get("catalog", []), check.value)
                if item:
                    return str(item["name"])
        lowered = task.lower()
        for item in snapshot.state.get("catalog", []):
            if str(item.get("name", "")).lower() in lowered:
                return str(item["name"])
            if str(item.get("category", "")).lower() in lowered:
                return str(item["name"])
        return "Red Shoes"

    def _choose_wishlist_product(self, task: str, snapshot: BrowserSnapshot, expected: list[ExpectedCheck]) -> str | None:
        for check in expected:
            if check.type == "wishlist_contains_cheapest_matching" and isinstance(check.value, dict):
                item = self._first_catalog_match(snapshot.state.get("catalog", []), check.value)
                if item:
                    return str(item["name"])
        lowered = task.lower()
        for item in self._catalog_matches_task(snapshot.state.get("catalog", []), lowered):
            return str(item["name"])
        return None

    def _catalog_matches_task(self, catalog: list[dict[str, Any]], lowered_task: str) -> list[dict[str, Any]]:
        matches = []
        rating = self._extract_rating_floor(lowered_task)
        for item in catalog:
            category = str(item.get("category", "")).lower()
            if category in lowered_task and (rating is None or item.get("rating", 0) >= rating):
                matches.append(item)
        return sorted(matches, key=lambda item: (item.get("price", 0), item.get("name", "")))

    def _first_catalog_match(self, catalog: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any] | None:
        matches = [item for item in catalog if self._item_matches(item, spec)]
        if not matches:
            return None
        return sorted(matches, key=lambda item: (item.get("price", 0), item.get("name", "")))[0]

    def _item_matches(self, item: dict[str, Any], spec: dict[str, Any]) -> bool:
        if "name" in spec and item.get("name") != spec["name"]:
            return False
        if "category" in spec and item.get("category") != spec["category"]:
            return False
        if "price_lte" in spec and item.get("price", 0) > spec["price_lte"]:
            return False
        if "rating_gte" in spec and item.get("rating", 0) < spec["rating_gte"]:
            return False
        return True

    def _extract_email(self, task: str) -> str | None:
        match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", task)
        return match.group(0) if match else None

    def _extract_rating_floor(self, lowered_task: str) -> float | None:
        match = re.search(r"(?:at least|>=)\s*(\d+(?:\.\d+)?)\s*stars?", lowered_task)
        return float(match.group(1)) if match else None

    def _extract_support_message(self, task: str) -> str | None:
        match = re.search(r"saying:\s*(.*?)(?:\.\s*Use email|\s+Use email|$)", task, flags=re.IGNORECASE)
        if not match:
            return None
        message = match.group(1).strip()
        return message.rstrip(".") if message else None
