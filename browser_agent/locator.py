"""Locator strategy selection and maintenance hooks."""

from __future__ import annotations

from dataclasses import dataclass

from browser_agent.browser import BrowserSnapshot
from browser_agent.schemas import MaintenanceEvent


@dataclass
class LocatedTarget:
    selector: str
    strategy: str
    maintenance_event: MaintenanceEvent | None = None


class Locator:
    def locate(self, hint: str, snapshot: BrowserSnapshot) -> LocatedTarget | None:
        normalized = hint.lower()
        if hint in snapshot.elements:
            return LocatedTarget(selector=hint, strategy="stable_selector")
        for selector, meta in snapshot.elements.items():
            label = str(meta.get("label", "")).lower()
            aliases = [str(item).lower() for item in meta.get("aliases", [])]
            if normalized == label or normalized in aliases:
                return LocatedTarget(selector=selector, strategy="semantic_label")

        for selector, meta in snapshot.elements.items():
            label = str(meta.get("label", "")).lower()
            if all(part in label for part in normalized.split()):
                return LocatedTarget(
                    selector=selector,
                    strategy="fuzzy_label",
                    maintenance_event=MaintenanceEvent(
                        kind="locator_strategy_adjusted",
                        old_locator=hint,
                        new_locator=selector,
                        reason="Exact locator failed; fuzzy label match succeeded.",
                    ),
                )
        return None
