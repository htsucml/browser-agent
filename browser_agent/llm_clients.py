"""LLM client interfaces and test-safe implementations."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

_USE_ENV_API_KEY = object()

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
        response = self.responses.pop(0) if self.responses else self._default_response(payload)
        content = response if isinstance(response, str) else json.dumps(response)
        return LLMResponse(content=content, model=self.model, prompt_tokens=0, completion_tokens=0, total_tokens=0)

    def _default_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        instruction = payload.get("input", {}).get("user_instruction", "").lower()
        if "weekly summary emails" in instruction and any(word in instruction for word in ("turn on", "enable")):
            return {
                "decision": "act",
                "action_id": "settings:set_weekly_summary_emails:true",
                "reason": "Enable the requested weekly summary emails setting.",
            }
        if "cheapest" in instruction and "usb-c hub" in instruction and "wishlist" in instruction:
            actions = payload.get("input", {}).get("available_actions", [])
            valid_actions = [
                action
                for action in actions
                if action.get("action") == "add_to_wishlist"
                and action.get("item", {}).get("category") == "usb-c hub"
                and float(action.get("item", {}).get("rating", 0)) >= 4.5
            ]
            if valid_actions:
                chosen = min(valid_actions, key=lambda action: float(action.get("item", {}).get("price", 0)))
                return {
                    "decision": "act",
                    "action_id": chosen["action_id"],
                    "reason": "Choose the cheapest USB-C hub meeting the rating constraint and save it to the wishlist.",
                }
        if "pending reimbursement" in instruction and "morgan lee" in instruction and "review" in instruction:
            actions = payload.get("input", {}).get("available_actions", [])
            for action in actions:
                row = action.get("row", {})
                if action.get("action") == "review" and row.get("person") == "Morgan Lee" and row.get("status") == "pending":
                    return {
                        "decision": "act",
                        "action_id": action["action_id"],
                        "reason": "Review only Morgan Lee's pending reimbursement request.",
                    }
        if "support ticket" in instruction and "alex@example.com" in instruction and "package arrived damaged" in instruction:
            return {
                "decision": "fill_and_submit",
                "fields": {
                    "support-email": "alex@example.com",
                    "support-message": "The package arrived damaged.",
                },
                "submit_action_id": "support:submit_ticket",
                "reason": "Fill the provided email and message, then submit the support ticket.",
            }
        if payload.get("input", {}).get("mode") == "read_only_summarization":
            return {
                "answer": "Fake summary based on extracted page content.",
                "reason": "Deterministic fake read-only summary.",
            }
        return {"action_type": "stop", "reason": "Fake LLM default stop."}


class OpenAICompatibleLLMClient:
    """Minimal OpenAI-compatible client wrapper.

    This is intentionally unused in tests. It reads the API key only from the environment.
    """

    provider = "openai"

    def __init__(self, model: str, api_key: str | None | object = _USE_ENV_API_KEY):
        self.model = model
        self._api_key = os.environ.get("OPENAI_API_KEY") if api_key is _USE_ENV_API_KEY else api_key

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


def make_llm_client(
    provider: str,
    model: str,
    responses: list[str | dict[str, Any]] | None = None,
    api_key: str | None | object = _USE_ENV_API_KEY,
) -> LLMClient:
    if provider == "fake":
        return FakeLLMClient(responses=list(responses or []))
    if provider == "openai":
        return OpenAICompatibleLLMClient(model=model, api_key=api_key)
    raise ValueError(f"Unsupported LLM provider: {provider}")
