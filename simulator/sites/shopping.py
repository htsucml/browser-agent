"""Fake shopping site with deterministic state."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.state import SimulatorState


class ShoppingPage:
    def __init__(self, state: "SimulatorState"):
        self.state = state
        self.inputs = state.inputs

    def text(self) -> str:
        cart_text = f"Cart: {len(self.state.cart)}"
        items = ", ".join(self.state.cart) if self.state.cart else "empty"
        products = " ".join(
            f"{item['name']} {item['category']} ${item['price']} {item['rating']} stars" for item in self.catalog()
        )
        trap = " Success! Eco notebook added. " if self.state.variant == "fake_success" else " "
        modal = " Newsletter modal: sign up and save. " if self.state.variant == "modal_blocking" else " "
        return f"Demo Shop {products}{trap}{modal}{cart_text} Items: {items}"

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        return [
            {"name": "Red Shoes", "category": "shoes", "price": 42, "rating": 4.2},
            {"name": "Budget Wireless Mouse", "category": "wireless mouse", "price": 24, "rating": 4.1},
            {"name": "Premium Wireless Mouse", "category": "wireless mouse", "price": 45, "rating": 4.8},
            {"name": "Everyday Keyboard", "category": "keyboard", "price": 39, "rating": 4.3},
            {"name": "Ergo Laptop Stand", "category": "laptop stand", "price": 34, "rating": 4.6},
            {"name": "Compact USB-C Hub", "category": "usb-c hub", "price": 29, "rating": 4.5},
            {"name": "Pro USB-C Hub", "category": "usb-c hub", "price": 44, "rating": 4.8},
            {"name": "Eco Notebook", "category": "notebook", "price": 8, "rating": 4.4},
            {"name": "Quiet ANC Headphones", "category": "noise cancelling headphones", "price": 89, "rating": 4.5},
        ]

    def elements(self) -> dict[str, dict[str, Any]]:
        add_stand_selector = "button:add-laptop-stand"
        if self.state.variant == "selector_drift":
            add_stand_selector = "button:semantic-buy-stand"
        elements = {
            "button:add-red-shoes": {
                "role": "button",
                "label": "Add Red Shoes to cart",
                "aliases": ["add red shoes to cart"],
            },
            "input:search": {
                "role": "textbox",
                "label": "Search products",
                "aliases": ["search"],
            },
        }
        for item in self.catalog():
            slug = item["name"].lower().replace(" ", "-")
            selector = f"button:add-{slug}"
            if item["name"] == "Ergo Laptop Stand":
                selector = add_stand_selector
            elements[selector] = {
                "role": "button",
                "label": f"Add {item['name']} to cart",
                "aliases": [f"add {item['name'].lower()} to cart", f"add {item['category']} to cart"],
            }
            elements[f"button:wishlist-{slug}"] = {
                "role": "button",
                "label": f"Save {item['name']} to wishlist",
                "aliases": [f"save {item['name'].lower()} to wishlist", f"wishlist {item['category']}"],
            }
        if self.state.variant == "modal_blocking":
            elements["button:close-modal"] = {"role": "button", "label": "Close modal", "aliases": ["close modal"]}
        return elements

    def click(self, selector: str) -> dict[str, Any]:
        if selector == "button:add-red-shoes":
            self.state.cart.append("Red Shoes")
            return {"ok": True, "effect": "cart_item_added", "cart_count": len(self.state.cart)}
        if selector == "button:close-modal":
            self.state.url = "simulator://shopping"
            self.state.actions_taken.append("close_modal")
            return {"ok": True, "effect": "modal_closed"}
        if self.state.variant == "modal_blocking" and selector != "button:close-modal":
            self.state.actions_taken.append(f"blocked:{selector}")
            return {"ok": False, "reason": "modal_or_overlay_blocking"}
        if self.state.variant == "fake_success" and selector == "button:add-eco-notebook":
            self.state.actions_taken.append("fake_success_add_eco_notebook")
            return {"ok": True, "effect": "fake_success_message_only"}
        for item in self.catalog():
            slug = item["name"].lower().replace(" ", "-")
            add_selector = f"button:add-{slug}"
            if item["name"] == "Ergo Laptop Stand" and self.state.variant == "selector_drift":
                add_selector = "button:semantic-buy-stand"
            if selector == add_selector:
                self.state.cart.append(item["name"])
                self.state.actions_taken.append(f"add:{item['name']}")
                return {"ok": True, "effect": "cart_item_added", "cart_count": len(self.state.cart)}
            if selector == f"button:wishlist-{slug}":
                self.state.wishlist.append(item["name"])
                self.state.actions_taken.append(f"wishlist:{item['name']}")
                return {"ok": True, "effect": "wishlist_item_added", "wishlist_count": len(self.state.wishlist)}
        return {"ok": False, "reason": f"Unknown clickable selector {selector}"}

    def fill(self, selector: str, value: str) -> dict[str, Any]:
        if selector == "input:search":
            self.state.inputs[selector] = value
            return {"ok": True, "effect": "input_filled", "value": value}
        return {"ok": False, "reason": f"Unknown input selector {selector}"}

    def html(self) -> str:
        return f"""
        <!doctype html>
        <html>
          <head><title>Demo Shop</title></head>
          <body>
            <h1>Demo Shop</h1>
            <p>Cart: {len(self.state.cart)}</p>
            <article>
              <h2>Red Shoes</h2>
              <button id="add-red-shoes">Add Red Shoes to cart</button>
            </article>
          </body>
        </html>
        """
