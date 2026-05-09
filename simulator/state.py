"""Resettable simulator state."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse
from typing import Any

from simulator.sites.dashboard import DashboardPage
from simulator.sites.settings import SettingsPage
from simulator.sites.shopping import ShoppingPage
from simulator.sites.support import SupportPage


@dataclass
class SimulatorState:
    url: str = "simulator://shopping"
    cart: list[str] = field(default_factory=list)
    wishlist: list[str] = field(default_factory=list)
    inputs: dict[str, str] = field(default_factory=dict)
    settings: dict[str, bool] = field(default_factory=dict)
    support_tickets: list[dict[str, str]] = field(default_factory=list)
    account_deleted: bool = False
    dashboard_rows: list[dict[str, Any]] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)

    def reset(self, url: str = "simulator://shopping") -> None:
        self.url = url
        self.cart = []
        self.wishlist = []
        self.inputs = {}
        self.settings = {
            "weekly_summary_emails": False,
            "email_notifications": True,
            "sms_notifications": False,
        }
        self.support_tickets = []
        self.account_deleted = False
        self.dashboard_rows = [
            {"id": "inv_100", "kind": "invoice", "status": "overdue", "amount": 1250, "review": False},
            {"id": "inv_101", "kind": "invoice", "status": "paid", "amount": 3100, "review": False},
            {"id": "inv_102", "kind": "invoice", "status": "overdue", "amount": 2750, "review": False},
            {
                "id": "req_200",
                "kind": "reimbursement",
                "person": "Morgan Lee",
                "status": "pending",
                "reviewed": False,
                "approved": False,
            },
            {
                "id": "req_201",
                "kind": "reimbursement",
                "person": "Dana Kim",
                "status": "pending",
                "reviewed": False,
                "approved": False,
            },
        ]

    @property
    def domain(self) -> str:
        return urlparse(self.url).netloc or "shopping"

    @property
    def variant(self) -> str:
        parsed = urlparse(self.url)
        return parse_qs(parsed.query).get("variant", ["normal"])[0]

    def current_page(self) -> ShoppingPage | SettingsPage | SupportPage | DashboardPage:
        if self.domain == "shopping":
            return ShoppingPage(self)
        if self.domain == "settings":
            return SettingsPage(self)
        if self.domain == "support":
            return SupportPage(self)
        if self.domain == "dashboard":
            return DashboardPage(self)
        raise ValueError(f"Unsupported simulator URL: {self.url}")

    def click(self, selector: str) -> dict[str, Any]:
        return self.current_page().click(selector)

    def fill(self, selector: str, value: str) -> dict[str, Any]:
        return self.current_page().fill(selector, value)

    def to_public_state(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "cart_count": len(self.cart),
            "cart_items": list(self.cart),
            "wishlist_items": list(self.wishlist),
            "catalog": ShoppingPage.catalog(),
            "inputs": dict(self.inputs),
            "settings": dict(self.settings),
            "support_tickets": list(self.support_tickets),
            "account_deleted": self.account_deleted,
            "dashboard_rows": [dict(row) for row in self.dashboard_rows],
            "actions_taken": list(self.actions_taken),
        }
