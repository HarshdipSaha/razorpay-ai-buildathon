from typing import Any
from rebound.models import Cause

_TEMPLATES = {
    Cause.INSUFFICIENT_FUNDS: "the customer's last payment attempt showed insufficient funds",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "the customer's card appears expired or blocked",
    Cause.AUTHENTICATION_FAILED: "the customer needs to re-approve/re-authenticate the payment (e.g. UPI AutoPay mandate re-authorisation)",
    Cause.MANDATE_NOT_ACTIVE: "the customer's payment mandate is no longer active and needs re-approval",
    Cause.LIMIT_EXCEEDED: "the transaction exceeded a limit; a different payment method may be needed",
}

_STATIC_FALLBACK = {
    Cause.INSUFFICIENT_FUNDS: "It looks like your last payment didn't go through due to insufficient funds. We'll retry shortly, or you can update your balance.",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "Your saved card appears to be expired or blocked. Please update your payment method to keep your subscription active.",
    Cause.AUTHENTICATION_FAILED: "Please re-approve your payment authorization (e.g. your UPI AutoPay mandate) to continue your subscription.",
    Cause.MANDATE_NOT_ACTIVE: "Your payment mandate is no longer active. Please re-approve it to continue your subscription.",
    Cause.LIMIT_EXCEEDED: "Your last payment exceeded a transaction limit. Please try a different payment method.",
}


def draft_nudge(client: Any, cause: Cause) -> str:
    """Drafts a short customer-facing message. NEVER sent — logged to the audit trail
    and the exceptions/report output for a human operator to review and send manually.
    If no LLM client is configured (no ANTHROPIC_API_KEY), falls back to a static
    template per cause — this keeps the pipeline fully offline-runnable."""
    if client is None:
        return _STATIC_FALLBACK.get(cause, "There was an issue with your recent payment. Please check your account.")

    context = _TEMPLATES.get(cause, "there was an issue with the recent payment")
    prompt = (
        f"Write a single short, polite message (max 2 sentences, plain English) to a customer "
        f"whose recurring payment failed because {context}. Ask them to take the appropriate action. "
        f"Do not mention internal system details."
    )
    response = client.messages.create(
        model="claude-sonnet-5", max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
