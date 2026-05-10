"""Shared typed models for agent runtime, traces, and eval results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class ExpectedCheck:
    type: str
    target: str
    value: Any


@dataclass
class EvalCase:
    id: str
    domain: str
    start_url: str
    task: str
    expected: list[ExpectedCheck]
    expected_status: str = "success"
    max_steps: int = 10
    tags: list[str] = field(default_factory=list)
    reference_path: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalCase":
        return cls(
            id=data["id"],
            domain=data["domain"],
            start_url=data["start_url"],
            task=data["task"],
            expected=[ExpectedCheck(**item) for item in data.get("expected", [])],
            expected_status=str(data.get("expected_status", "success")),
            max_steps=int(data.get("max_steps", 10)),
            tags=list(data.get("tags", [])),
            reference_path=data.get("reference_path"),
        )


@dataclass
class ActionRecord:
    step: int
    action_type: str
    target: str
    value: Any | None = None
    status: Literal["success", "failed", "skipped"] = "success"
    locator_strategy: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)


@dataclass
class VerificationResult:
    passed: bool
    check_type: str
    target: str
    expected: Any
    observed: Any
    reason: str
    timestamp: str = field(default_factory=utc_now)


@dataclass
class FailureEvent:
    category: str
    cause: str
    evidence: dict[str, Any] = field(default_factory=dict)
    step: int | None = None
    recovered: bool = False
    timestamp: str = field(default_factory=utc_now)


@dataclass
class RecoveryEvent:
    strategy: str
    status: Literal["attempted", "succeeded", "failed"]
    reason: str
    step: int | None = None
    timestamp: str = field(default_factory=utc_now)


@dataclass
class MaintenanceEvent:
    kind: str
    old_locator: str | None
    new_locator: str | None
    reason: str
    timestamp: str = field(default_factory=utc_now)


@dataclass
class SafetyEvent:
    kind: str
    decision: Literal["allowed", "refused"]
    reason: str
    timestamp: str = field(default_factory=utc_now)


@dataclass
class AgentTrace:
    run_id: str
    case_id: str | None
    start_url: str
    task: str
    status: Literal["success", "failed", "refused", "needs_user"]
    verified: bool
    actions: list[ActionRecord] = field(default_factory=list)
    verifications: list[VerificationResult] = field(default_factory=list)
    failures: list[FailureEvent] = field(default_factory=list)
    recoveries: list[RecoveryEvent] = field(default_factory=list)
    maintenance_events: list[MaintenanceEvent] = field(default_factory=list)
    safety_events: list[SafetyEvent] = field(default_factory=list)
    final_evidence: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    cost_usd: float = 0.0
    planner_type: str = "rule"
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_call_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRunResult:
    run_id: str
    status: Literal["success", "failed", "refused", "needs_user"]
    verified: bool
    final_reason: str
    trace_path: str
    actions: list[ActionRecord]


@dataclass
class EvalResult:
    case_id: str
    run_id: str
    expected_status: str
    actual_status: str
    status: str
    trace_path: str
    verified_success: bool
    false_success: bool
    unsafe_action: bool
    correct_refusal: bool
    browser_spl: float
    num_steps: int
    recovery_success: bool
    selector_drift_recovery: bool
    token_count: int
    recovery_events_count: int = 0
    maintenance_events_count: int = 0
