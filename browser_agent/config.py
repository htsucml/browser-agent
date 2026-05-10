"""Runtime configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PlannerConfig:
    planner: str = "rule"
    llm_provider: str = "fake"
    llm_model: str = "gpt-4.1-mini"
    max_llm_calls_per_run: int = 1
    max_steps: int = 3
    max_output_tokens: int = 300
    request_timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "PlannerConfig":
        return cls(
            planner=os.environ.get("PLANNER", "rule").lower(),
            llm_provider=os.environ.get("LLM_PROVIDER", "fake").lower(),
            llm_model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
            max_llm_calls_per_run=_int_env("MAX_LLM_CALLS_PER_RUN", 1),
            max_steps=_int_env("MAX_STEPS", 3),
            max_output_tokens=_int_env("MAX_OUTPUT_TOKENS", 300),
            request_timeout_seconds=_float_env("REQUEST_TIMEOUT_SECONDS", 30.0),
        )


@dataclass(frozen=True)
class AppConfig:
    allow_byok: bool = False
    allow_server_openai_key: bool = False
    demo_token: str | None = None
    max_active_runs: int = 1
    rate_limit_runs: int = 5
    rate_limit_window_seconds: int = 600
    max_run_seconds: float = 30.0
    max_extract_chars: int = 10000

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            allow_byok=_bool_env("ALLOW_BYOK", False),
            allow_server_openai_key=_bool_env("ALLOW_SERVER_OPENAI_KEY", False),
            demo_token=os.environ.get("DEMO_TOKEN") or None,
            max_active_runs=_int_env("MAX_ACTIVE_RUNS", 1),
            rate_limit_runs=_int_env("RATE_LIMIT_RUNS", 5),
            rate_limit_window_seconds=_int_env("RATE_LIMIT_WINDOW_SECONDS", 600),
            max_run_seconds=_float_env("MAX_RUN_SECONDS", 30.0),
            max_extract_chars=_int_env("MAX_EXTRACT_CHARS", 10000),
        )


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
