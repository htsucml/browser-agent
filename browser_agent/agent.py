"""Agent orchestration for the scaffold flow."""

from __future__ import annotations

from browser_agent.browser import SimulatorBrowser
from browser_agent.config import PlannerConfig
from browser_agent.controller import Controller
from browser_agent.llm_clients import make_llm_client
from browser_agent.llm_planner import LLMPlanner
from browser_agent.locator import Locator
from browser_agent.logger import TraceLogger
from browser_agent.observer import Observer
from browser_agent.planner import RulePlanner
from browser_agent.preflight import missing_required_info_plan
from browser_agent.recovery import Recovery
from browser_agent.safety import SafetyPolicy
from browser_agent.schemas import (
    ActionRecord,
    AgentRunResult,
    AgentTrace,
    EvalCase,
    FailureEvent,
    ExpectedCheck,
    new_id,
)
from browser_agent.redaction import redact_secrets
from browser_agent.verifier import Verifier
from simulator.state import SimulatorState


class BrowserAgent:
    def __init__(
        self,
        state: SimulatorState | None = None,
        logger: TraceLogger | None = None,
        config: PlannerConfig | None = None,
        fake_llm_responses: list | None = None,
    ):
        self.state = state or SimulatorState()
        self.browser = SimulatorBrowser(self.state)
        self.observer = Observer()
        self.config = config or PlannerConfig.from_env()
        self.planner = self._make_planner(fake_llm_responses)
        self.locator = Locator()
        self.controller = Controller()
        self.verifier = Verifier()
        self.recovery = Recovery()
        self.safety = SafetyPolicy()
        self.logger = logger or TraceLogger()

    def _make_planner(self, fake_llm_responses: list | None = None):
        if self.config.planner == "llm":
            client = make_llm_client(self.config.llm_provider, self.config.llm_model, fake_llm_responses)
            return LLMPlanner(client, self.config)
        return RulePlanner()

    def run(
        self,
        start_url: str,
        task: str,
        expected: list[ExpectedCheck] | None = None,
        case_id: str | None = None,
        max_steps: int = 10,
    ) -> AgentRunResult:
        run_id = new_id("run")
        self.browser.reset(start_url)
        max_steps = min(max_steps, self.config.max_steps)
        trace = AgentTrace(run_id=run_id, case_id=case_id, start_url=start_url, task=task, status="failed", verified=False)
        self._apply_planner_metadata(trace)

        safety_event = self.safety.check(task)
        trace.safety_events.append(safety_event)
        if safety_event.decision == "refused":
            trace.status = "refused"
            trace.final_evidence = {"reason": safety_event.reason}
            path = self.logger.write(trace)
            return AgentRunResult(run_id, "refused", False, safety_event.reason, path, trace.actions)

        try:
            snapshot = self.observer.observe(self.browser)
            plan = missing_required_info_plan(task, snapshot, expected)
            if plan is None:
                plan = self.planner.plan(task, snapshot, expected)
            self._apply_planner_metadata(trace)
            if not plan.actions:
                trace.failures.append(FailureEvent(category="planning_error", cause=plan.reason, evidence={"task": task}))
                trace.recoveries.append(self.recovery.record_noop("No scaffold recovery available for unmatched task."))
            for step, planned in enumerate(plan.actions[:max_steps], start=1):
                if planned.action_type == "needs_user":
                    trace.actions.append(
                        ActionRecord(
                            step=step,
                            action_type="needs_user",
                            target="user",
                            value=planned.value,
                            status="skipped",
                            evidence={"reason": planned.value or plan.reason},
                        )
                    )
                    trace.status = "needs_user"
                    trace.verified = False
                    trace.final_evidence = {
                        "reason": planned.value or plan.reason,
                        "state": self.browser.snapshot().state,
                        "url": self.browser.snapshot().url,
                    }
                    path = self.logger.write(trace)
                    return AgentRunResult(run_id, "needs_user", False, str(trace.final_evidence.get("reason", "")), path, trace.actions)
                if planned.action_type == "stop":
                    break
                snapshot = self.observer.observe(self.browser)
                validation_error = self._validate_llm_action(planned, snapshot)
                if validation_error:
                    trace.actions.append(
                        ActionRecord(
                            step=step,
                            action_type=planned.action_type,
                            target=planned.target_hint,
                            value=planned.value,
                            status="failed",
                            evidence={"reason": validation_error},
                        )
                    )
                    trace.failures.append(FailureEvent(category="action_validation_error", cause=validation_error, step=step))
                    trace.recoveries.append(self.recovery.record_noop("Rejected invalid LLM action before execution.", step=step))
                    continue
                located = self.locator.locate(planned.target_hint, snapshot)
                if located is None:
                    trace.actions.append(
                        ActionRecord(
                            step=step,
                            action_type=planned.action_type,
                            target=planned.target_hint,
                            value=planned.value,
                            status="failed",
                            evidence={"reason": "locator not found"},
                        )
                    )
                    trace.failures.append(FailureEvent(category="locator_error", cause="Target not found.", step=step))
                    trace.recoveries.append(self.recovery.record_noop("No alternate locator found.", step=step))
                    continue
                if located.maintenance_event:
                    trace.maintenance_events.append(located.maintenance_event)
                result = self.controller.act(self.browser, planned.action_type, located.selector, planned.value)
                status = "success" if result.get("ok") else "failed"
                trace.actions.append(
                    ActionRecord(
                        step=step,
                        action_type=planned.action_type,
                        target=located.selector,
                        value=planned.value,
                        status=status,
                        locator_strategy=located.strategy,
                        evidence=result,
                    )
                )
                if status == "failed":
                    trace.failures.append(
                        FailureEvent(category="action_error", cause=str(result.get("reason", "action failed")), step=step)
                    )

            checks = plan.expected
            verified, verification_results = self.verifier.verify_all(checks, self.browser)
            trace.verifications.extend(verification_results)
            trace.verified = verified
            trace.status = "success" if verified else "failed"
            if not verified:
                trace.failures.append(
                    FailureEvent(
                        category="verification_error",
                        cause="Final verification did not pass.",
                        evidence={"checks": [item.reason for item in verification_results]},
                    )
                )
            trace.final_evidence = {
                "reason": "Verification passed." if verified else "Verification failed; success was not claimed.",
                "state": self.browser.snapshot().state,
                "url": self.browser.snapshot().url,
            }
        except Exception as exc:  # pragma: no cover - defensive trace preservation
            self._apply_planner_metadata(trace)
            trace.status = "failed"
            category = "planning_error" if self.config.planner == "llm" else "unknown_error"
            trace.failures.append(FailureEvent(category=category, cause=str(redact_secrets(str(exc)))))
            trace.final_evidence = {"reason": "Unhandled runtime error."}

        path = self.logger.write(trace)
        return AgentRunResult(
            run_id=run_id,
            status=trace.status,
            verified=trace.verified,
            final_reason=str(trace.final_evidence.get("reason", "")),
            trace_path=path,
            actions=trace.actions,
        )

    def run_case(self, case: EvalCase) -> AgentRunResult:
        return self.run(case.start_url, case.task, expected=case.expected, case_id=case.id, max_steps=case.max_steps)

    def _apply_planner_metadata(self, trace: AgentTrace) -> None:
        trace.planner_type = self.config.planner
        if isinstance(self.planner, LLMPlanner):
            trace.llm_provider = self.planner.metadata.provider
            trace.llm_model = self.planner.metadata.model
            trace.llm_call_count = self.planner.metadata.call_count
            trace.prompt_tokens = self.planner.metadata.prompt_tokens
            trace.completion_tokens = self.planner.metadata.completion_tokens
            trace.total_tokens = self.planner.metadata.total_tokens
            trace.token_count = self.planner.metadata.total_tokens

    def _validate_llm_action(self, planned, snapshot) -> str | None:
        if not isinstance(self.planner, LLMPlanner):
            return None
        if not (snapshot.url.startswith("simulator://shopping") or snapshot.url.startswith("simulator://dashboard")):
            return None
        payload = self.planner.metadata.last_payload or {}
        available_actions = payload.get("input", {}).get("available_actions", [])
        if not available_actions:
            return None
        action_id = (planned.metadata or {}).get("action_id")
        allowed_by_id = {str(action.get("action_id")): action for action in available_actions if action.get("action_id")}
        allowed_ids = set(allowed_by_id)
        if not action_id:
            return "LLM action must use an available action_id; fuzzy targets are not executable in guarded mode."
        if str(action_id) not in allowed_ids:
            return f"Unknown or disallowed action_id: {action_id}"
        if snapshot.url.startswith("simulator://dashboard"):
            return self._validate_dashboard_llm_action(str(action_id), allowed_by_id[str(action_id)], payload)
        return None

    def _validate_dashboard_llm_action(self, action_id: str, action: dict, payload: dict) -> str | None:
        constraints = payload.get("input", {}).get("observation", {}).get("parsed_user_constraints", {})
        row = action.get("row", {})
        requested_action = constraints.get("action")
        if requested_action and action.get("action") != requested_action:
            return f"Dashboard action {action_id} does not match requested action {requested_action}."
        if constraints.get("person") and row.get("person") != constraints["person"]:
            return f"Dashboard action {action_id} targets the wrong person."
        if constraints.get("kind") and row.get("kind") != constraints["kind"]:
            return f"Dashboard action {action_id} targets the wrong row kind."
        if constraints.get("status") and row.get("status") != constraints["status"]:
            return f"Dashboard action {action_id} targets the wrong row status."
        if action.get("action") == "approve" and requested_action != "approve":
            return f"Dashboard approve action {action_id} is not allowed without an explicit approve request."
        return None
