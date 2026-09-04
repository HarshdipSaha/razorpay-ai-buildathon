from rebound.ingest.adapter import event_to_pipeline_inputs


def test_payment_failed_extracts_failure_and_state():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {"entity": {
                "id": "pay_abc", "amount": 50000, "method": "card",
                "error_code": "BAD_REQUEST_ERROR", "error_reason": "insufficient_funds",
                "error_source": "issuer_bank", "error_step": "payment_authorization",
                "description": "", "notes": {"subscription_id": "sub_abc"},
            }},
        },
    }
    result = event_to_pipeline_inputs(payload)
    assert result is not None
    failure, state, invoice_id = result
    assert failure.subscription_id == "sub_abc"
    assert failure.error_reason == "insufficient_funds"
    assert state.status == "active"


def test_subscription_halted_extracts_state():
    payload = {
        "event": "subscription.halted",
        "payload": {
            "subscription": {"entity": {
                "id": "sub_xyz", "status": "halted",
                "notes": {},
            }},
        },
    }
    result = event_to_pipeline_inputs(payload)
    assert result is not None
    failure, state, invoice_id = result
    assert state.status == "halted"
    assert state.subscription_id == "sub_xyz"


def test_unhandled_event_type_returns_none():
    payload = {"event": "subscription.charged", "payload": {}}
    assert event_to_pipeline_inputs(payload) is None
