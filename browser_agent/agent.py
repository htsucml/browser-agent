"""Agent orchestration for the scaffold flow."""

from __future__ import annotations

from browser_agent.browser import SimulatorBrowser
from browser_agent.controller import Controller
from browser_agent.locator import Locator
from browser_agent.logger import TraceLogger
from browser_agent.observer import Observer
from browser_agent.planner import RulePlanner
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
from browser_agent.verifier import Verifier
from simulator.state import SimulatorState


class BrowserAgent:
    def __init__(self, state: SimulatorState | None = None, logger: TraceLogger | None = None):
        self.state = state or SimulatorState()
        self.browser = SimulatorBrowser(self.state)
        self.observer = Observer()
        self.planner = RulePlanner()
        self.locator = Locator()
        self.controller = Controller()
        self.verifier = Verifier()
        self.recovery = Recovery()
        self.safety = SafetyPolicy()
        self.logger = logger or TraceLogger()

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
        trace = AgentTrace(run_id=run_id, case_id=case_id, start_url=start_url, task=task, status="failed", verified=False)

        safety_event = self.safety.check(task)
        trace.safety_events.append(safety_event)
        if safety_event.decision == "refused":
            trace.status = "refused"
            trace.final_evidence = {"reason": safety_event.reason}
            path = self.logger.write(trace)
            return AgentRunResult(run_id, "refused", False, safety_event.reason, path, trace.actions)

        try:
            snapshot = self.observer.observe(self.browser)
            plan = self.planner.plan(task, snapshot, expected)
            if not plan.actions:
                trace.failures.append(FailureEvent(category="planning_error", cause=plan.reason, evidence={"task": task}))
                trace.recoveries.append(self.recovery.record_noop("No scaffold recovery available for unmatched task."))
            for step, planned in enumerate(plan.actions[:max_steps], start=1):
                snapshot = self.observer.observe(self.browser)
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
            trace.status = "failed"
            trace.failures.append(FailureEvent(category="unknown_error", cause=str(exc)))
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
