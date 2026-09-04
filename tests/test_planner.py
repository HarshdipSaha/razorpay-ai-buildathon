from rebound.actions.planner import plan_action
from rebound.models import Cause, SubscriptionState, Action


def test_insufficient_funds_first_attempt_charges():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.INSUFFICIENT_FUNDS, state, amount=50000, sim_time=0.0)
    assert req.action == Action.CHARGE_INVOICE
    assert req.attempt_no == 1


def test_mandate_not_active_never_charges():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.MANDATE_NOT_ACTIVE, state, amount=50000, sim_time=0.0)
    assert req.action in (Action.PAYMENT_LINK, Action.NUDGE)


def test_unknown_always_escalates():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.UNKNOWN, state, amount=50000, sim_time=0.0)
    assert req.action == Action.ESCALATE
