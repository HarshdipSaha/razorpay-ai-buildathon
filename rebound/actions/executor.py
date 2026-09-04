from __future__ import annotations
from typing import Any
from rebound.models import Action, ActionRequest, Outcome


class Executor:
    """Calls a Razorpay-shaped test-mode client (real, or the in-memory
    SimulatedRazorpayClient used by `rebound demo`). Must only be invoked
    after a gate `allow` verdict.

    Caveat: the amount check below compares req.amount against `invoice_amount`,
    which the pipeline always sets to `failure.amount` — the same source req.amount
    was derived from — so this is a self-consistency check, not independent
    verification against a real fetched invoice total. Acceptable for synthetic
    batch data.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def execute(self, req: ActionRequest, invoice_id: str, invoice_amount: int) -> Outcome:
        if req.amount != invoice_amount:
            return Outcome(action=req.action, executed=False,
                            error=f"amount mismatch: {req.amount} != invoice {invoice_amount}")

        if req.action == Action.CHARGE_INVOICE:
            result = self.client.invoice.issue(invoice_id)
            return Outcome(action=req.action, executed=True, api_ref=result.get("id"))

        if req.action == Action.PAYMENT_LINK:
            result = self.client.payment_link.create({
                "amount": req.amount, "currency": "INR",
                "description": f"Recovery for subscription {req.subscription_id}",
                "notes": {"subscription_id": req.subscription_id, "cause": req.cause.value},
            })
            return Outcome(action=req.action, executed=True, api_ref=result.get("id"))

        return Outcome(action=req.action, executed=False, error=f"{req.action} is not an executor action")
