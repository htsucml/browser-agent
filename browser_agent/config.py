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
    max_steps: int = 10
    max_output_tokens: int = 300
    request_timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> "PlannerConfig":
        return cls(
            planner=os.environ.get("PLANNER", "rule").lower(),
            llm_provider=os.environ.get("LLM_PROVIDER", "fake").lower(),
            llm_model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
            max_llm_calls_per_run=_int_env("MAX_LLM_CALLS_PER_RUN", 1),
            max_steps=_int_env("MAX_STEPS", 10),
            max_output_tokens=_int_env("MAX_OUTPUT_TOKENS", 300),
            request_timeout_seconds=_float_env("REQUEST_TIMEOUT_SECONDS", 15.0),
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
