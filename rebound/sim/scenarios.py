from __future__ import annotations
import random
from pathlib import Path
from rebound.models import Cause, PaymentFailure, Scenario, SubscriptionState
from rebound.ingest.fixtures import iter_fixtures

_DECLINE_MIX: list[tuple[Cause, float]] = [
    (Cause.INSUFFICIENT_FUNDS, 0.30),
    (Cause.INSTRUMENT_EXPIRED_OR_BLOCKED, 0.15),
    (Cause.AUTHENTICATION_FAILED, 0.15),
    (Cause.BANK_OR_GATEWAY_ERROR, 0.15),
    (Cause.MANDATE_NOT_ACTIVE, 0.10),
    (Cause.LIMIT_EXCEEDED, 0.05),
    (Cause.UNKNOWN, 0.10),
]

_REASON_BY_CAUSE = {
    Cause.INSUFFICIENT_FUNDS: "insufficient_funds",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "card_expired",
    Cause.AUTHENTICATION_FAILED: "authentication_failed",
    Cause.BANK_OR_GATEWAY_ERROR: "bank_technical_error",
    Cause.MANDATE_NOT_ACTIVE: None,
    Cause.LIMIT_EXCEEDED: "transaction_limit_exceeded",
    Cause.UNKNOWN: "payment_failed",
}


def _synthetic_scenario(idx: int, rng: random.Random) -> Scenario:
    causes, weights = zip(*_DECLINE_MIX)
    cause = rng.choices(causes, weights=weights, k=1)[0]
    amount = rng.choice([49900, 99900, 149900, 299900])
    reason = _REASON_BY_CAUSE[cause]
    failure = PaymentFailure(
        payment_id=f"pay_synth_{idx}", subscription_id=f"sub_synth_{idx}",
        amount=amount, method=rng.choice(["card", "upi"]),
        error_reason=reason,
        token_status="paused" if cause == Cause.MANDATE_NOT_ACTIVE else None,
        error_description="customer support ticket text unclear about cause" if cause == Cause.UNKNOWN else None,
    )
    state = SubscriptionState(subscription_id=failure.subscription_id, status="halted", attempt_no=0)
    return Scenario(id=f"scn_{idx}", tags=["synthetic"], failure=failure, state=state, truth_cause=cause)


def _scenario_from_recorded_envelope(envelope: dict, idx: int) -> Scenario | None:
    from rebound.ingest.adapter import event_to_pipeline_inputs
    from rebound.classify.rules import classify_by_rules

    parsed = event_to_pipeline_inputs(envelope)
    if parsed is None:
        return None
    failure, state, _invoice_id = parsed
    classification = classify_by_rules(failure)
    truth_cause = classification.cause if classification is not None else Cause.UNKNOWN
    return Scenario(id=f"scn_recorded_{idx}", tags=["recorded"], failure=failure,
                     state=state, truth_cause=truth_cause)


def generate_scenarios(seed: int, n: int = 60, recorded_dir: Path | None = None) -> list[Scenario]:
    rng = random.Random(seed)
    scenarios: list[Scenario] = []

    recorded_count = 0
    if recorded_dir is not None and Path(recorded_dir).exists():
        for i, envelope in enumerate(iter_fixtures(Path(recorded_dir))):
            scenario = _scenario_from_recorded_envelope(envelope, i)
            if scenario is not None:
                scenarios.append(scenario)
                recorded_count += 1

    remaining = n - recorded_count
    for i in range(remaining):
        scenarios.append(_synthetic_scenario(i, rng))

    heldout_target = max(20, n // 3)
    heldout_idx = set(rng.sample(range(len(scenarios)), min(heldout_target, len(scenarios))))
    for i in heldout_idx:
        scenarios[i] = scenarios[i].model_copy(update={"tags": scenarios[i].tags + ["heldout"]})

    dup_target = 5
    dup_idx = rng.sample(range(len(scenarios)), min(dup_target, len(scenarios)))
    for i in dup_idx:
        scenarios[i] = scenarios[i].model_copy(update={"tags": scenarios[i].tags + ["replay_duplicate"]})

    return scenarios
