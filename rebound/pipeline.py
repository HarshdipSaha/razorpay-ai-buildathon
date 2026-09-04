from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from rebound.models import Action, Cause, Classification, Outcome, PaymentFailure, ProcessResult, SubscriptionState
from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.classify.rules import classify_by_rules
from rebound.classify.llm import LLMClassifier
from rebound.actions.planner import plan_action
from rebound.policy.gate import PolicyGate
from rebound.actions.executor import Executor
from rebound.actions.nudge import draft_nudge
from rebound.sim.clock import Clock


@dataclass
class PipelineContext:
    store: EventStore
    audit: AuditLog
    gate: PolicyGate
    executor_client: Any
    llm_client: Any
    clock: Clock
    llm_cache_dir: str = ".rebound_data/llm_cache"


class Pipeline:
    def __init__(self, ctx: PipelineContext) -> None:
        self.ctx = ctx
        self.executor = Executor(ctx.executor_client)

    def process_failure(self, event_id: str, failure: PaymentFailure,
                         state: SubscriptionState, invoice_id: str) -> Optional[ProcessResult]:
        """Returns None only when the event_id is a duplicate (no action taken).
        Otherwise returns both the Classification and the Outcome."""
        sim_time = self.ctx.clock.now()
        is_new = self.ctx.store.insert_if_new(event_id, "payment.failed", failure.model_dump())
        self.ctx.audit.append("event_received", failure.model_dump(mode="json"), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)
        if not is_new:
            self.ctx.audit.append("duplicate_rejected", {"event_id": event_id}, sim_time,
                                   event_id=event_id, subscription_id=failure.subscription_id)
            return None

        classification = classify_by_rules(failure)
        if classification is None:
            if self.ctx.llm_client is None:
                classification = Classification(cause=Cause.UNKNOWN, provenance="abstain",
                                                  rationale="no LLM client configured")
            else:
                classifier = LLMClassifier(self.ctx.llm_client, cache_dir=self.ctx.llm_cache_dir)
                classification = classifier.classify(failure)
        self.ctx.audit.append("classified", classification.model_dump(mode="json"), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        req = plan_action(classification.cause, state, amount=failure.amount, sim_time=sim_time)
        self.ctx.audit.append("action_proposed", req.model_dump(mode="json"), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        verdict = self.ctx.gate.evaluate(req, state, invoice_amount=failure.amount)
        self.ctx.audit.append("policy_verdict", verdict.model_dump(mode="json"), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        if verdict.decision != "allow":
            self.ctx.audit.append("action_blocked", {"verdict": verdict.model_dump(mode="json")}, sim_time,
                                   event_id=event_id, subscription_id=failure.subscription_id)
            # verdict.decision "escalate" (e.g. hard_stop.attempts_exhausted on a
            # charge_invoice/payment_link/nudge request) must surface as an escalated
            # outcome, not a blocked one — override the outcome's action to reflect
            # what actually happened, not what was originally requested.
            outcome_action = Action.ESCALATE if verdict.decision == "escalate" else req.action
            outcome = Outcome(action=outcome_action, executed=False, error=verdict.reason)
            return ProcessResult(classification=classification, outcome=outcome)

        if req.action == Action.NUDGE:
            text = draft_nudge(self.ctx.llm_client, classification.cause)
            outcome = Outcome(action=req.action, executed=True, api_ref=None, error=None)
            self.ctx.audit.append("action_executed", {**outcome.model_dump(mode="json"), "nudge_text": text},
                                   sim_time, event_id=event_id, subscription_id=failure.subscription_id)
            return ProcessResult(classification=classification, outcome=outcome)

        if req.action == Action.ESCALATE:
            outcome = Outcome(action=req.action, executed=False, error="escalate")
            self.ctx.audit.append("action_executed", outcome.model_dump(mode="json"), sim_time,
                                   event_id=event_id, subscription_id=failure.subscription_id)
            return ProcessResult(classification=classification, outcome=outcome)

        outcome = self.executor.execute(req, invoice_id=invoice_id, invoice_amount=failure.amount)
        self.ctx.audit.append("action_executed" if outcome.executed else "action_failed",
                               outcome.model_dump(mode="json"), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)
        return ProcessResult(classification=classification, outcome=outcome)
