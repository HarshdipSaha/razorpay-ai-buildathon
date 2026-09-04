from __future__ import annotations
from rebound.models import Scenario
from rebound.pipeline import Pipeline, PipelineContext


def run_batch(ctx: PipelineContext, scenarios: list[Scenario]) -> list[dict]:
    pipeline = Pipeline(ctx)
    results: list[dict] = []

    for scenario in scenarios:
        event_id = f"evt_{scenario.id}"
        result = pipeline.process_failure(
            event_id=event_id, failure=scenario.failure, state=scenario.state,
            invoice_id=f"inv_{scenario.id}",
        )
        outcome = result.outcome if result else None
        results.append({
            "scenario_id": scenario.id,
            "tags": scenario.tags,
            "truth_cause": scenario.truth_cause.value,
            "predicted_cause": result.classification.cause.value if result else None,
            "provenance": result.classification.provenance if result else None,
            "mapped_from": result.classification.mapped_from if result else None,
            "outcome": outcome.model_dump(mode="json") if outcome else None,
            "policy_violation": bool(outcome and outcome.executed and outcome.error),
        })

        if "replay_duplicate" in scenario.tags:
            if hasattr(ctx.clock, "advance"):
                ctx.clock.advance(1)
            dup_result = pipeline.process_failure(
                event_id=event_id,
                failure=scenario.failure, state=scenario.state, invoice_id=f"inv_{scenario.id}",
            )
            results.append({
                "scenario_id": scenario.id, "tags": ["replay_duplicate_check"],
                "truth_cause": scenario.truth_cause.value,
                "predicted_cause": None, "provenance": None, "mapped_from": None,
                "outcome": dup_result.outcome.model_dump(mode="json") if dup_result else None,
                "policy_violation": dup_result is not None,
            })

    return results
