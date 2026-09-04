from rebound.models import Action, ActionRequest, Cause, SubscriptionState

_DEFAULT_ACTION: dict[Cause, Action] = {
    Cause.INSUFFICIENT_FUNDS: Action.CHARGE_INVOICE,
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: Action.PAYMENT_LINK,
    Cause.AUTHENTICATION_FAILED: Action.NUDGE,
    Cause.BANK_OR_GATEWAY_ERROR: Action.CHARGE_INVOICE,
    Cause.MANDATE_NOT_ACTIVE: Action.PAYMENT_LINK,
    Cause.LIMIT_EXCEEDED: Action.PAYMENT_LINK,
    Cause.UNKNOWN: Action.ESCALATE,
}


def plan_action(cause: Cause, state: SubscriptionState, amount: int, sim_time: float) -> ActionRequest:
    action = _DEFAULT_ACTION[cause]
    return ActionRequest(
        subscription_id=state.subscription_id, cause=cause, action=action,
        amount=amount, attempt_no=state.attempt_no + 1, sim_time=sim_time,
    )
