from pathlib import Path

import pytest

from browser_agent.run_readonly import run_readonly


def _require_playwright_browser():
    pytest.importorskip("playwright.sync_api")
    from browser_agent.browser import PlaywrightBrowserBackend

    backend = None
    try:
        backend = PlaywrightBrowserBackend()
    except Exception as exc:
        pytest.skip(f"Playwright browser is not available: {exc}")
    finally:
        if backend is not None:
            backend.close()


def test_playwright_readonly_backend_extracts_local_static_page(tmp_path):
    _require_playwright_browser()
    page = tmp_path / "readonly.html"
    page.write_text(
        "<!doctype html><html><head><title>Readonly Test Page</title></head>"
        "<body><h1>Local Fixture</h1><p>Hello from a deterministic page.</p>"
        "<a href='https://example.com'>Example</a></body></html>",
        encoding="utf-8",
    )

    result = run_readonly(page.resolve().as_uri(), "Return the page title and main visible text.")

    assert result["status"] == "success"
    assert result["verified"] is True
    assert result["title"] == "Readonly Test Page"
    assert "Hello from a deterministic page." in result["visible_text_snippet"]
    assert result["links_count"] == 1
    assert Path(result["trace_path"]).exists()
