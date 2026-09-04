from rebound.policy.gate import PolicyGate
from rebound.models import ActionRequest, Action, Cause, SubscriptionState

POLICY_PATH = "rebound/policy/policy.yaml"


def make_state(**overrides):
    base = dict(subscription_id="sub_1", status="halted", attempt_no=0,
                consent=True, dispute_open=False, token_status=None)
    base.update(overrides)
    return SubscriptionState(**base)


def test_allows_charge_invoice_for_insufficient_funds_first_attempt():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision == "allow"


def test_blocks_when_dispute_open():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(dispute_open=True))
    assert verdict.decision == "block"
    assert "dispute" in verdict.rule_id


def test_blocks_when_no_consent():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.AUTHENTICATION_FAILED,
                         action=Action.NUDGE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(consent=False))
    assert verdict.decision == "block"
    assert "consent" in verdict.rule_id


def test_blocks_when_attempts_exhausted():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=4, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision in ("block", "escalate")


def test_blocks_when_amount_mismatch():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=99999999, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(), invoice_amount=50000)
    assert verdict.decision == "block"
    assert "amount" in verdict.rule_id


def test_mandate_not_active_never_allows_charge():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(token_status="paused"))
    assert verdict.decision != "allow"


def test_mandate_not_active_allows_payment_link_on_first_attempt():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(token_status="paused"))
    assert verdict.decision == "allow"
    assert verdict.rule_id == "causes.mandate_not_active.allow"


def test_instrument_expired_allows_payment_link_on_first_attempt_only():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    allowed = gate.evaluate(
        ActionRequest(subscription_id="sub_1", cause=Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
                      action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0),
        make_state(),
    )
    assert allowed.decision == "allow"
    second = gate.evaluate(
        ActionRequest(subscription_id="sub_1", cause=Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
                      action=Action.PAYMENT_LINK, amount=50000, attempt_no=2, sim_time=0.0),
        make_state(),
    )
    assert second.decision == "escalate"


def test_unknown_cause_always_escalates():
    gate = PolicyGate.from_yaml(POLICY_PATH)
    req = ActionRequest(subscription_id="sub_1", cause=Cause.UNKNOWN,
                         action=Action.ESCALATE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision == "escalate"
