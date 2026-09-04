from __future__ import annotations
from pathlib import Path
import yaml
from rebound.models import ActionRequest, SubscriptionState, Verdict


class PolicyGate:
    """The ONLY module permitted to authorise a call to a money API.
    Deterministic: same inputs always produce the same verdict."""

    def __init__(self, policy: dict) -> None:
        self.policy = policy

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyGate":
        with open(path) as f:
            return cls(yaml.safe_load(f))

    def evaluate(self, req: ActionRequest, state: SubscriptionState,
                 invoice_amount: int | None = None) -> Verdict:
        invoice_amount = invoice_amount if invoice_amount is not None else req.amount

        if state.dispute_open:
            return Verdict(decision="block", rule_id="hard_stop.dispute_open",
                            reason="a dispute is open on this subscription")

        if not state.consent and req.action.value == "nudge":
            return Verdict(decision="block", rule_id="hard_stop.no_consent",
                            reason="customer has not consented to contact")

        if req.amount != invoice_amount:
            return Verdict(decision="block", rule_id="hard_stop.amount_mismatch",
                            reason=f"requested amount {req.amount} != invoice amount {invoice_amount}")

        if state.status in ("cancelled", "completed"):
            return Verdict(decision="block", rule_id="hard_stop.subscription_terminal",
                            reason=f"subscription status is {state.status}")

        cause_key = req.cause.value
        attempts_rule = next(
            hs for hs in self.policy["hard_stops"] if hs["id"] == "hard_stop.attempts_exhausted"
        )
        max_attempts = attempts_rule["max_attempts_by_cause"].get(cause_key, 0)
        if req.attempt_no > max_attempts:
            return Verdict(decision="escalate", rule_id="hard_stop.attempts_exhausted",
                            reason=f"attempt {req.attempt_no} exceeds max {max_attempts} for {cause_key}")

        row = self.policy["causes"].get(cause_key)
        if row is None or req.action.value not in row["allow_actions"]:
            return Verdict(decision="escalate", rule_id=f"causes.{cause_key}.action_not_allowed",
                            reason=f"{req.action.value} is not a permitted action for {cause_key}")

        return Verdict(decision="allow", rule_id=f"causes.{cause_key}.allow",
                        reason=f"{req.action.value} permitted for {cause_key}, attempt {req.attempt_no}")
