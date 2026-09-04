import json
from rebound.sim.report import build_report, render_markdown
from rebound.sim.report_html import render_html


def _row(scenario_id, tags, truth, predicted, provenance, action, executed, error=None, mapped_from=None):
    return {
        "scenario_id": scenario_id, "tags": tags, "truth_cause": truth,
        "predicted_cause": predicted, "provenance": provenance, "mapped_from": mapped_from,
        "outcome": {"action": action, "executed": executed, "error": error},
        "policy_violation": False,
    }


def test_build_report_computes_confusion_matrix_and_per_cause_precision_recall():
    results = [
        _row("s1", ["synthetic", "heldout"], "insufficient_funds", "insufficient_funds", "rule",
             "charge_invoice", True, mapped_from="error_reason=insufficient_funds"),
        _row("s2", ["synthetic", "heldout"], "insufficient_funds", "bank_or_gateway_error", "llm",
             "charge_invoice", True),
        _row("s3", ["synthetic", "heldout"], "unknown", "unknown", "abstain", "escalate", False, "escalate"),
        {"scenario_id": "s1", "tags": ["replay_duplicate_check"], "truth_cause": "insufficient_funds",
         "predicted_cause": None, "provenance": None, "mapped_from": None, "outcome": None, "policy_violation": False},
    ]
    report = build_report(results)

    assert report["duplicates_rejected"] == 1
    assert report["double_charges"] == 0
    assert report["policy_violations"] == 0
    assert report["classifier"]["heldout_count"] == 3
    assert report["classifier"]["confusion_matrix"]["insufficient_funds->insufficient_funds"] == 1
    assert report["classifier"]["confusion_matrix"]["insufficient_funds->bank_or_gateway_error"] == 1
    citations = {c["scenario_id"]: c for c in report["classification_citations"]}
    assert citations["s1"]["mapped_from"] == "error_reason=insufficient_funds"
    assert "s3" not in citations
    json.dumps(report)
    pr = report["classifier"]["per_cause"]["insufficient_funds"]
    assert pr["recall"] == 0.5
    assert pr["precision"] == 1.0


def test_build_report_flags_double_charge_as_violation():
    results = [
        _row("s1", ["replay_duplicate_check"], "insufficient_funds", "insufficient_funds", "rule",
             "charge_invoice", True),
    ]
    report = build_report(results)
    assert report["double_charges"] == 1


def test_build_report_counts_false_escalations():
    results = [
        _row("s1", ["synthetic", "heldout"], "insufficient_funds", "insufficient_funds", "rule",
             "escalate", False, "escalate"),
    ]
    report = build_report(results, permitted_action_by_cause={"insufficient_funds": "charge_invoice"})
    assert report["false_escalations"] == 1


def test_render_html_is_self_contained_and_includes_key_sections():
    report = {
        "duplicates_rejected": 1, "double_charges": 0, "policy_violations": 0, "false_escalations": 0,
        "per_cause": {"insufficient_funds": {"allowed": 5, "blocked": 0, "escalated": 1}},
        "classifier": {"heldout_count": 20, "accuracy": 0.9, "abstain_rate": 0.1, "per_cause": {}},
        "exceptions": [{"scenario_id": "s1", "truth_cause": "unknown", "reason": "escalate"}],
        "classification_citations": [],
    }
    audit_records = [
        {"seq": 0, "stage": "event_received", "subscription_id": "sub_1", "hash": "aaaa1111" * 8},
        {"seq": 1, "stage": "duplicate_rejected", "subscription_id": "sub_1", "hash": "bbbb2222" * 8},
    ]
    html = render_html(report, audit_records=audit_records)
    assert "<style>" in html
    assert "<script" not in html.lower()
    assert "insufficient_funds" in html
    assert "Where AI was" in html
    assert "duplicate_rejected" in html
    assert "aaaa1111" in html


def test_render_html_works_with_no_audit_records():
    report = {
        "duplicates_rejected": 0, "double_charges": 0, "policy_violations": 0, "false_escalations": 0,
        "per_cause": {}, "classifier": {"heldout_count": 0, "accuracy": None, "abstain_rate": None, "per_cause": {}},
        "exceptions": [], "classification_citations": [],
    }
    html = render_html(report, audit_records=[])
    assert "<style>" in html
