"""Optional simulator HTTP server for manual inspection."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from simulator.state import SimulatorState

simulator_app = FastAPI(title="Browser Agent Simulator")
state = SimulatorState()


@simulator_app.get("/", response_class=HTMLResponse)
def shopping_page() -> str:
    page = state.current_page()
    return page.html()


@simulator_app.post("/reset")
def reset() -> dict:
    state.reset()
    return state.to_public_state()


@simulator_app.post("/click/{selector}")
def click(selector: str) -> dict:
    return state.click(selector)
