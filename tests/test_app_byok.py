import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.main as app_main
from browser_agent.config import AppConfig
from browser_agent.llm_clients import LLMResponse, OpenAICompatibleLLMClient


def _reset_app_guards():
    app_main._ACTIVE_RUNS = 0
    app_main._RATE_LIMITS.clear()


def _clear_env(monkeypatch):
    _reset_app_guards()
    for name in [
        "ALLOW_BYOK",
        "ALLOW_SERVER_OPENAI_KEY",
        "DEMO_TOKEN",
        "MAX_ACTIVE_RUNS",
        "RATE_LIMIT_RUNS",
        "RATE_LIMIT_WINDOW_SECONDS",
        "MAX_RUN_SECONDS",
        "MAX_STEPS",
        "MAX_LLM_CALLS_PER_RUN",
        "MAX_OUTPUT_TOKENS",
        "OPENAI_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


def _request(host: str = "testclient"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def test_byok_disabled_by_default(monkeypatch):
    _clear_env(monkeypatch)
    assert AppConfig.from_env().allow_byok is False
    assert AppConfig.from_env().allow_server_openai_key is False


def test_byok_disabled_rejects_request_key(monkeypatch):
    _clear_env(monkeypatch)
    secret = "sk-testBYOKdisabled123456"
    with pytest.raises(HTTPException) as exc:
        app_main._run_once(
            AppConfig(),
            "simulator://settings?variant=normal",
            "Turn on weekly summary emails.",
            "llm",
            "fake",
            "gpt-4.1-nano",
            secret,
        )
    assert exc.value.status_code == 403
    assert secret not in str(exc.value.detail)


def test_byok_enabled_fake_provider_accepts_key_without_echo(monkeypatch):
    _clear_env(monkeypatch)
    secret = "sk-testBYOKfake123456789"
    result, trace = app_main._run_once(
        AppConfig(allow_byok=True),
        "simulator://settings?variant=normal",
        "Turn on weekly summary emails.",
        "llm",
        "fake",
        "gpt-4.1-nano",
        secret,
    )
    assert result.status in {"success", "failed"}
    assert trace["llm_provider"] == "fake"
    assert trace["llm_call_count"] == 1
    assert secret not in json.dumps(trace)


def test_byok_enabled_openai_stub_accepts_request_key_without_external_call(monkeypatch):
    _clear_env(monkeypatch)

    def fake_generate(self, payload, max_output_tokens, timeout_seconds):
        return LLMResponse(
            content=json.dumps({"action_type": "select", "target": "toggle:weekly-summary-emails", "reason": "Enable it."}),
            model=self.model,
        )

    monkeypatch.setattr(OpenAICompatibleLLMClient, "generate_json", fake_generate)
    secret = "sk-testBYOKopenai123456789"
    result, trace = app_main._run_once(
        AppConfig(allow_byok=True),
        "simulator://settings?variant=normal",
        "Turn on weekly summary emails.",
        "llm",
        "openai",
        "gpt-4.1-nano",
        secret,
    )
    assert result.status in {"success", "failed"}
    assert trace["llm_provider"] == "openai"
    assert trace["llm_call_count"] == 1
    assert secret not in json.dumps(trace)


def test_openai_missing_allowed_key_fails_gracefully_without_server_fallback(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-serverShouldNotBeUsed123456")
    result, trace = app_main._run_once(
        AppConfig(allow_server_openai_key=False),
        "simulator://settings?variant=normal",
        "Turn on weekly summary emails.",
        "llm",
        "openai",
        "gpt-4.1-nano",
        "",
    )
    assert result.status == "failed"
    trace_text = json.dumps(trace)
    assert "OPENAI_API_KEY is required" in trace_text
    assert "sk-serverShouldNotBeUsed123456" not in trace_text


def test_key_like_string_is_redacted_from_trace(monkeypatch):
    _clear_env(monkeypatch)
    secret = "sk-testTraceSecret123456789"

    def fake_generate(self, payload, max_output_tokens, timeout_seconds):
        raise RuntimeError(f"provider rejected api_key={secret}")

    monkeypatch.setattr(OpenAICompatibleLLMClient, "generate_json", fake_generate)
    result, trace = app_main._run_once(
        AppConfig(allow_byok=True),
        "simulator://settings?variant=normal",
        "Turn on weekly summary emails.",
        "llm",
        "openai",
        "gpt-4.1-nano",
        secret,
    )
    assert result.status == "failed"
    assert secret not in json.dumps(trace)
    latest_trace = max(Path("logs/runs").glob("run_*.json"), key=lambda path: path.stat().st_mtime)
    assert secret not in latest_trace.read_text(encoding="utf-8")


def test_demo_token_required_when_set():
    with pytest.raises(HTTPException) as exc:
        app_main._check_demo_token(AppConfig(demo_token="demo-secret"), "")
    assert exc.value.status_code == 401


def test_wrong_demo_token_rejected():
    with pytest.raises(HTTPException) as exc:
        app_main._check_demo_token(AppConfig(demo_token="demo-secret"), "wrong")
    assert exc.value.status_code == 403
    assert "demo-secret" not in str(exc.value.detail)


def test_health_public_when_demo_token_set(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("DEMO_TOKEN", "demo-secret")
    assert app_main.health() == {"status": "ok"}


def test_rate_limit_rejects_excessive_requests():
    _reset_app_guards()
    config = AppConfig(rate_limit_runs=1, rate_limit_window_seconds=600)
    app_main._check_rate_limit(_request(), config)
    with pytest.raises(HTTPException) as exc:
        app_main._check_rate_limit(_request(), config)
    assert exc.value.status_code == 429


def test_max_active_runs_guard():
    _reset_app_guards()
    app_main._ACTIVE_RUNS = 1
    with pytest.raises(HTTPException) as exc:
        app_main._acquire_run_slot(AppConfig(max_active_runs=1))
    assert exc.value.status_code == 503
    _reset_app_guards()


def test_private_and_internal_urls_are_blocked():
    for url in [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://10.0.0.5",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
    ]:
        with pytest.raises(HTTPException) as exc:
            app_main._validate_public_http_url(url)
        assert exc.value.status_code == 400


def test_ui_key_inputs_are_password_and_not_prepopulated():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'id="openai_api_key"' in template
    assert 'name="openai_api_key" type="password" autocomplete="off" value=""' in template
    assert 'id="demo_token"' in template
    assert 'name="demo_token" type="password" autocomplete="off" value=""' in template
