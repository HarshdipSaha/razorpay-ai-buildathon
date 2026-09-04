from rebound.classify.taxonomy import REASON_TO_CAUSE, DOC_URLS
from rebound.classify.rules import classify_by_rules
from rebound.models import Cause, PaymentFailure


def test_insufficient_funds_maps_correctly():
    assert REASON_TO_CAUSE["insufficient_funds"] == Cause.INSUFFICIENT_FUNDS


def test_every_cause_has_a_doc_url():
    for cause in Cause:
        assert cause in DOC_URLS, f"{cause} missing a source doc URL"


def test_classifies_insufficient_funds_from_error_reason():
    pf = PaymentFailure(
        payment_id="pay_1", subscription_id="sub_1", amount=50000, method="card",
        error_reason="insufficient_funds", error_source="issuer_bank", error_step="payment_authorization",
    )
    result = classify_by_rules(pf)
    assert result is not None
    assert result.cause == Cause.INSUFFICIENT_FUNDS
    assert result.provenance == "rule"
    assert result.mapped_from == "error_reason=insufficient_funds"


def test_returns_none_on_generic_reason():
    pf = PaymentFailure(
        payment_id="pay_2", subscription_id="sub_2", amount=50000, method="upi",
        error_reason="payment_failed",
    )
    assert classify_by_rules(pf) is None


def test_token_status_maps_to_mandate_not_active():
    pf = PaymentFailure(
        payment_id="pay_3", subscription_id="sub_3", amount=50000, method="upi",
        token_status="paused",
    )
    result = classify_by_rules(pf)
    assert result is not None
    assert result.cause == Cause.MANDATE_NOT_ACTIVE
    assert result.mapped_from == "token_status=paused"
