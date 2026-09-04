from pathlib import Path
from rebound.pipeline import Pipeline, PipelineContext
from rebound.models import PaymentFailure, SubscriptionState
from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.policy.gate import PolicyGate
from rebound.sim.clock import SimClock
from rebound.sim.fake_razorpay import SimulatedRazorpayClient
from rebound.sim.batch import run_batch
from rebound.sim.scenarios import generate_scenarios

POLICY_PATH = "rebound/policy/policy.yaml"


def build_context(tmp_path) -> PipelineContext:
    return PipelineContext(
        store=EventStore(tmp_path / "events.db"),
        audit=AuditLog(tmp_path / "audit.jsonl"),
        gate=PolicyGate.from_yaml(POLICY_PATH),
        executor_client=SimulatedRazorpayClient(),
        llm_client=None,
        clock=SimClock(0.0),
        llm_cache_dir=str(tmp_path / "llm_cache"),
    )


def test_pipeline_processes_one_documented_failure_end_to_end(tmp_path):
    ctx = build_context(tmp_path)
    pl = Pipeline(ctx)
    failure = PaymentFailure(payment_id="pay_1", subscription_id="sub_1", amount=50000,
                              method="card", error_reason="insufficient_funds")
    state = SubscriptionState(subscription_id="sub_1", status="halted", attempt_no=0)
    result = pl.process_failure(event_id="evt_1", failure=failure, state=state, invoice_id="inv_1")
    assert result is not None
    assert result.classification.cause.value == "insufficient_funds"
    assert result.classification.provenance == "rule"
    assert result.outcome.executed is True
    assert ctx.audit.verify() is True


def test_duplicate_event_id_produces_no_second_action(tmp_path):
    ctx = build_context(tmp_path)
    pl = Pipeline(ctx)
    failure = PaymentFailure(payment_id="pay_1", subscription_id="sub_1", amount=50000,
                              method="card", error_reason="insufficient_funds")
    state = SubscriptionState(subscription_id="sub_1", status="halted", attempt_no=0)
    pl.process_failure(event_id="evt_dup", failure=failure, state=state, invoice_id="inv_1")
    second = pl.process_failure(event_id="evt_dup", failure=failure, state=state, invoice_id="inv_1")
    assert second is None


def test_run_batch_produces_one_result_per_scenario_plus_duplicates(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    assert len(results) >= len(scenarios)


def test_run_batch_records_predicted_cause_from_classification(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    primary = [r for r in results if "replay_duplicate_check" not in r["tags"]]
    for r in primary:
        assert r["predicted_cause"] is not None
        assert r["provenance"] in ("rule", "llm", "abstain")
        if r["provenance"] == "rule":
            assert r["mapped_from"] is not None and "=" in r["mapped_from"]


def test_run_batch_has_zero_policy_violations(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    violations = [r for r in results if r.get("policy_violation")]
    assert violations == []
