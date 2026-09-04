from __future__ import annotations
from collections import defaultdict

_DEFAULT_PERMITTED_ACTION = {
    "insufficient_funds": "charge_invoice",
    "instrument_expired_or_blocked": "payment_link",
    "authentication_failed": "nudge",
    "bank_or_gateway_error": "charge_invoice",
    "mandate_not_active": "payment_link",
    "limit_exceeded": "payment_link",
    "unknown": "escalate",
}


def build_report(results: list[dict], permitted_action_by_cause: dict | None = None) -> dict:
    permitted = permitted_action_by_cause or _DEFAULT_PERMITTED_ACTION

    duplicates_rejected = sum(
        1 for r in results if "replay_duplicate_check" in r["tags"] and r["outcome"] is None
    )
    double_charges = sum(
        1 for r in results
        if "replay_duplicate_check" in r["tags"] and r["outcome"] is not None and r["outcome"].get("executed")
    )
    policy_violations = sum(1 for r in results if r.get("policy_violation"))

    per_cause_outcomes: dict[str, dict] = defaultdict(lambda: {"allowed": 0, "blocked": 0, "escalated": 0})
    false_escalations = 0
    exceptions = []
    for r in results:
        if "replay_duplicate_check" in r["tags"]:
            continue
        cause = r["truth_cause"]
        outcome = r["outcome"]
        if outcome is None:
            continue
        if outcome.get("executed"):
            per_cause_outcomes[cause]["allowed"] += 1
        elif outcome.get("action") == "escalate":
            per_cause_outcomes[cause]["escalated"] += 1
            exceptions.append({"scenario_id": r["scenario_id"], "truth_cause": cause, "reason": outcome["error"]})
            if permitted.get(cause) not in (None, "escalate"):
                false_escalations += 1
        else:
            per_cause_outcomes[cause]["blocked"] += 1

    heldout = [r for r in results if "heldout" in r["tags"]]
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    for r in heldout:
        if r["predicted_cause"] is not None:
            confusion[(r["truth_cause"], r["predicted_cause"])] += 1

    causes = sorted({r["truth_cause"] for r in heldout} | {r["predicted_cause"] for r in heldout if r["predicted_cause"]})
    per_cause_pr: dict[str, dict] = {}
    for cause in causes:
        tp = confusion.get((cause, cause), 0)
        actual_total = sum(v for (t, _p), v in confusion.items() if t == cause)
        predicted_total = sum(v for (_t, p), v in confusion.items() if p == cause)
        per_cause_pr[cause] = {
            "precision": (tp / predicted_total) if predicted_total else None,
            "recall": (tp / actual_total) if actual_total else None,
        }

    correct = sum(1 for r in heldout if r.get("predicted_cause") == r["truth_cause"])
    abstained = sum(1 for r in heldout if r.get("provenance") == "abstain")

    classification_citations = [
        {"scenario_id": r["scenario_id"], "cause": r["predicted_cause"],
         "provenance": r["provenance"], "mapped_from": r.get("mapped_from")}
        for r in results
        if "replay_duplicate_check" not in r["tags"]
        and r.get("predicted_cause") not in (None, "unknown")
    ]

    return {
        "duplicates_rejected": duplicates_rejected,
        "double_charges": double_charges,
        "policy_violations": policy_violations,
        "false_escalations": false_escalations,
        "per_cause": dict(per_cause_outcomes),
        "classifier": {
            "heldout_count": len(heldout),
            "accuracy": (correct / len(heldout)) if heldout else None,
            "abstain_rate": (abstained / len(heldout)) if heldout else None,
            "confusion_matrix": {f"{t}->{p}": v for (t, p), v in confusion.items()},
            "per_cause": per_cause_pr,
        },
        "exceptions": exceptions,
        "classification_citations": classification_citations,
    }


def render_markdown(report: dict) -> str:
    lines = ["# Rebound batch report", ""]
    lines.append(f"- Duplicates rejected: **{report['duplicates_rejected']}**")
    lines.append(f"- Double charges: **{report['double_charges']}** (must be 0)")
    lines.append(f"- Policy violations: **{report['policy_violations']}** (must be 0)")
    lines.append(f"- False escalations: **{report['false_escalations']}**")
    lines.append("")
    lines.append("## Per-cause outcomes (policy outcome, not money recovered)")
    lines.append("| Cause | Allowed | Blocked | Escalated |")
    lines.append("|---|---|---|---|")
    for cause, counts in report["per_cause"].items():
        lines.append(f"| {cause} | {counts['allowed']} | {counts['blocked']} | {counts['escalated']} |")
    lines.append("")
    c = report["classifier"]
    lines.append(f"## Classifier (held-out set, n={c['heldout_count']})")
    lines.append(f"- Overall accuracy: {c['accuracy']} · Abstain rate: {c['abstain_rate']}")
    lines.append("")
    lines.append("| Cause | Precision | Recall |")
    lines.append("|---|---|---|")
    for cause, pr in c["per_cause"].items():
        lines.append(f"| {cause} | {pr['precision']} | {pr['recall']} |")
    lines.append("")
    lines.append("### Confusion matrix (truth → predicted : count)")
    for key, count in sorted(c["confusion_matrix"].items()):
        lines.append(f"- {key.replace('->', ' → ')}: {count}")
    lines.append("")
    lines.append("## Exceptions")
    for e in report["exceptions"]:
        lines.append(f"- `{e['scenario_id']}` ({e['truth_cause']}): {e['reason']}")
    lines.append("")
    lines.append("## Classification citations (every non-unknown cause traced to its source field)")
    for cite in report["classification_citations"]:
        source = cite["mapped_from"] or f"LLM ({cite['provenance']})"
        lines.append(f"- `{cite['scenario_id']}` → {cite['cause']}: {source}")
    return "\n".join(lines)
