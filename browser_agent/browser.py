"""Browser backend interfaces and implementations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from simulator.state import SimulatorState


@dataclass
class BrowserSnapshot:
    url: str
    text: str
    inputs: dict[str, str]
    state: dict[str, Any]
    elements: dict[str, dict[str, Any]]
    title: str = ""
    headings: list[str] | None = None
    links_count: int = 0


class BrowserBackend(Protocol):
    """Minimal backend contract shared by simulator and real browser backends."""

    def goto(self, url: str) -> None:
        """Navigate or reset the backend to a URL."""

    def observe(self) -> BrowserSnapshot:
        """Return a read-only snapshot of the current page/state."""

    def close(self) -> None:
        """Release backend resources."""


class SimulatorBrowserBackend:
    """Small browser facade over deterministic simulator state."""

    def __init__(self, state: SimulatorState):
        self.state = state

    def goto(self, url: str) -> None:
        self.reset(url)

    def reset(self, url: str) -> None:
        self.state.reset(url)

    def observe(self) -> BrowserSnapshot:
        return self.snapshot()

    def snapshot(self) -> BrowserSnapshot:
        page = self.state.current_page()
        return BrowserSnapshot(
            url=self.state.url,
            text=page.text(),
            inputs=dict(page.inputs),
            state=self.state.to_public_state(),
            elements=page.elements(),
        )

    def click(self, target: str) -> dict[str, Any]:
        return self.state.click(target)

    def fill(self, target: str, value: str) -> dict[str, Any]:
        return self.state.fill(target, value)

    def close(self) -> None:
        return None


class PlaywrightBrowserBackend:
    """Read-only Playwright backend for real webpages."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Playwright is not installed. Run `python3 -m pip install -r requirements.txt`.") from exc

        self.timeout_ms = timeout_ms
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()

    def goto(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        try:
            self._page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            # Many real pages never become fully idle. DOM content plus extracted text is enough for read-only mode.
            pass

    def observe(self) -> BrowserSnapshot:
        title = self._page.title()
        url = self._page.url
        text = self._page.locator("body").inner_text(timeout=self.timeout_ms).strip()
        headings = self._page.locator("h1, h2, h3").evaluate_all(
            "(nodes) => nodes.map((node) => node.innerText.trim()).filter(Boolean)"
        )
        links_count = self._page.locator("a").count()
        return BrowserSnapshot(
            url=url,
            text=text,
            inputs={},
            state={},
            elements={},
            title=title,
            headings=headings,
            links_count=links_count,
        )

    def screenshot(self, path: str | Path) -> str:
        output = str(path)
        self._page.screenshot(path=output, full_page=True)
        return output

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()


# Backward-compatible name used by the simulator-backed agent.
SimulatorBrowser = SimulatorBrowserBackend
