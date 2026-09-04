import json
from rebound.sim.scenarios import generate_scenarios
from rebound.models import Cause


def test_same_seed_produces_identical_batch():
    a = generate_scenarios(seed=42, n=60)
    b = generate_scenarios(seed=42, n=60)
    assert [s.id for s in a] == [s.id for s in b]
    assert [s.truth_cause for s in a] == [s.truth_cause for s in b]


def test_batch_has_at_least_20_heldout():
    scenarios = generate_scenarios(seed=42, n=60)
    heldout = [s for s in scenarios if "heldout" in s.tags]
    assert len(heldout) >= 20


def test_batch_has_at_least_5_duplicate_replays():
    scenarios = generate_scenarios(seed=42, n=60)
    dupes = [s for s in scenarios if "replay_duplicate" in s.tags]
    assert len(dupes) >= 5


def test_batch_declares_recorded_vs_synthetic():
    scenarios = generate_scenarios(seed=42, n=60, recorded_dir=None)
    for s in scenarios:
        assert "recorded" in s.tags or "synthetic" in s.tags


def test_recorded_envelope_is_converted_not_validated_as_scenario(tmp_path):
    envelope = {
        "event_id": "evt_captured_1", "event": "payment.failed",
        "payload": {"payment": {"entity": {
            "id": "pay_captured", "amount": 49900, "method": "card",
            "error_reason": "insufficient_funds", "error_source": "issuer_bank",
            "error_step": "payment_authorization", "notes": {"subscription_id": "sub_captured"},
        }}},
    }
    (tmp_path / "card_insufficient_funds.json").write_text(json.dumps(envelope))

    scenarios = generate_scenarios(seed=1, n=1, recorded_dir=tmp_path)
    recorded = [s for s in scenarios if "recorded" in s.tags]
    assert len(recorded) == 1
    assert recorded[0].truth_cause == Cause.INSUFFICIENT_FUNDS
    assert recorded[0].failure.subscription_id == "sub_captured"
