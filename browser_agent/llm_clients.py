"""LLM client interfaces and test-safe implementations."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class LLMResponse:
    content: str
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMClient(Protocol):
    provider: str
    model: str | None

    def generate_json(self, payload: dict[str, Any], max_output_tokens: int, timeout_seconds: float) -> LLMResponse:
        """Return a JSON string response."""


@dataclass
class FakeLLMClient:
    """Scriptable fake client for tests and dry runs."""

    responses: list[str | dict[str, Any]] = field(default_factory=list)
    provider: str = "fake"
    model: str = "fake-llm"
    call_count: int = 0
    last_payload: dict[str, Any] | None = None

    def generate_json(self, payload: dict[str, Any], max_output_tokens: int, timeout_seconds: float) -> LLMResponse:
        self.call_count += 1
        self.last_payload = payload
        response = self.responses.pop(0) if self.responses else {"action_type": "stop", "reason": "Fake LLM default stop."}
        content = response if isinstance(response, str) else json.dumps(response)
        return LLMResponse(content=content, model=self.model, prompt_tokens=0, completion_tokens=0, total_tokens=0)


class OpenAICompatibleLLMClient:
    """Minimal OpenAI-compatible client wrapper.

    This is intentionally unused in tests. It reads the API key only from the environment.
    """

    provider = "openai"

    def __init__(self, model: str):
        self.model = model
        self._api_key = os.environ.get("OPENAI_API_KEY")

    def generate_json(self, payload: dict[str, Any], max_output_tokens: int, timeout_seconds: float) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required when PLANNER=llm and LLM_PROVIDER=openai.")

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": payload["system_prompt"]},
                {"role": "user", "content": json.dumps(payload["input"], sort_keys=True)},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_output_tokens,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # pragma: no cover - external API
            data = json.loads(response.read().decode("utf-8"))
        message = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=message,
            model=self.model,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        )


def make_llm_client(provider: str, model: str, responses: list[str | dict[str, Any]] | None = None) -> LLMClient:
    if provider == "fake":
        return FakeLLMClient(responses=list(responses or []))
    if provider == "openai":
        return OpenAICompatibleLLMClient(model=model)
    raise ValueError(f"Unsupported LLM provider: {provider}")
