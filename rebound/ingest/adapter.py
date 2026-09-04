from __future__ import annotations
from typing import Any
from rebound.models import PaymentFailure, SubscriptionState

_HANDLED_EVENTS = {"payment.failed", "subscription.halted", "subscription.pending"}


def _resolve_invoice_id(client: Any, subscription_id: str) -> str:
    """Real Razorpay invoice lookup, shared by both branches below since either event
    type can lead the planner to choose `charge_invoice` (it decides from the cause
    alone, not from subscription status). Falls back to a placeholder when no real
    client is configured (batch/tests/simulated demo). A live Razorpay integration
    would replace this body with `client.invoice.all({"subscription_id": ...})`,
    but that path is out of scope for this offline build (no Razorpay login used)."""
    return f"inv_{subscription_id}"


def event_to_pipeline_inputs(
    payload: dict, client: Any = None,
) -> tuple[PaymentFailure, SubscriptionState, str] | None:
    """Translates a raw Razorpay webhook envelope into (PaymentFailure, SubscriptionState,
    invoice_id) for Pipeline.process_failure. Returns None for event types this build
    doesn't act on (ingest-only, e.g. subscription.charged)."""
    event_type = payload.get("event")
    if event_type not in _HANDLED_EVENTS:
        return None

    body = payload.get("payload", {})

    if event_type == "payment.failed":
        entity = body.get("payment", {}).get("entity", {})
        subscription_id = (entity.get("notes") or {}).get("subscription_id") or entity.get("subscription_id", "unknown")
        failure = PaymentFailure(
            payment_id=entity.get("id", "unknown"),
            subscription_id=subscription_id,
            amount=entity.get("amount", 0),
            method=entity.get("method", "unknown"),
            error_code=entity.get("error_code"),
            error_description=entity.get("error_description") or entity.get("description"),
            error_source=entity.get("error_source"),
            error_step=entity.get("error_step"),
            error_reason=entity.get("error_reason"),
        )
        state = SubscriptionState(subscription_id=subscription_id, status="active", attempt_no=0)
        return failure, state, _resolve_invoice_id(client, subscription_id)

    entity = body.get("subscription", {}).get("entity", {})
    subscription_id = entity.get("id", "unknown")
    failure = PaymentFailure(
        payment_id="unknown", subscription_id=subscription_id, amount=0, method="unknown",
    )
    state = SubscriptionState(
        subscription_id=subscription_id, status=entity.get("status", "halted"), attempt_no=0,
    )
    return failure, state, _resolve_invoice_id(client, subscription_id)
