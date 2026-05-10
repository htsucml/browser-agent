from pathlib import Path
import json

import pytest

from browser_agent.config import PlannerConfig
from browser_agent.display import build_display_result
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


def test_readonly_rule_mode_does_not_call_llm(tmp_path):
    _require_playwright_browser()
    page = tmp_path / "rule_readonly.html"
    page.write_text(
        "<!doctype html><html><head><title>Rule Readonly</title></head>"
        "<body><h1>Evidence Only</h1><p>Rule mode extracts without summarizing.</p></body></html>",
        encoding="utf-8",
    )

    result = run_readonly(
        page.resolve().as_uri(),
        "Return the page title.",
        config=PlannerConfig(planner="rule"),
    )
    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "success"
    assert trace["planner_type"] == "rule"
    assert trace["llm_call_count"] == 0
    assert "llm_answer" not in trace["final_evidence"]


def test_readonly_fake_llm_summarization_extracts_and_answers(tmp_path):
    _require_playwright_browser()
    page = tmp_path / "fake_llm_readonly.html"
    page.write_text(
        "<!doctype html><html><head><title>Fake LLM Readonly</title></head>"
        "<body><h1>Summarize Me</h1><p>The page has deterministic visible text.</p></body></html>",
        encoding="utf-8",
    )

    result = run_readonly(
        page.resolve().as_uri(),
        "Summarize this page.",
        config=PlannerConfig(planner="llm", llm_provider="fake", max_llm_calls_per_run=1),
    )
    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
    display = build_display_result(trace, result["trace_path"])

    assert result["status"] == "success"
    assert result["llm_answer"] == "Fake summary based on extracted page content."
    assert trace["planner_type"] == "llm"
    assert trace["llm_provider"] == "fake"
    assert trace["llm_call_count"] == 1
    assert display.answer == "Fake summary based on extracted page content."
    assert display.source_url == page.resolve().as_uri()
    assert display.page_title == "Fake LLM Readonly"


def test_readonly_extract_text_is_truncated(tmp_path):
    _require_playwright_browser()
    page = tmp_path / "truncated_readonly.html"
    visible = "0123456789" * 50
    page.write_text(
        f"<!doctype html><html><head><title>Truncate</title></head><body><p>{visible}</p></body></html>",
        encoding="utf-8",
    )

    result = run_readonly(
        page.resolve().as_uri(),
        "Extract a short snippet.",
        max_extract_chars=25,
        config=PlannerConfig(planner="rule"),
    )
    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))

    assert result["extract_chars"] <= 25
    assert len(trace["final_evidence"]["extracted_text"]) <= 25


def test_readonly_trace_and_display_do_not_include_request_key(tmp_path):
    _require_playwright_browser()
    secret = "sk-testReadonlySecret123456789"
    page = tmp_path / "secret_readonly.html"
    page.write_text(
        "<!doctype html><html><head><title>No Secret</title></head>"
        "<body><p>Visible content only.</p></body></html>",
        encoding="utf-8",
    )

    result = run_readonly(
        page.resolve().as_uri(),
        "Summarize without leaking keys.",
        config=PlannerConfig(planner="llm", llm_provider="fake"),
        llm_api_key=secret,
    )
    trace_text = Path(result["trace_path"]).read_text(encoding="utf-8")
    trace = json.loads(trace_text)
    display_text = json.dumps(build_display_result(trace, result["trace_path"]).to_dict())

    assert secret not in json.dumps(result)
    assert secret not in trace_text
    assert secret not in display_text
