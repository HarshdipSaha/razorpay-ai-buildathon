def render_html(report: dict, audit_records: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{cause}</td><td>{c['allowed']}</td><td>{c['blocked']}</td><td>{c['escalated']}</td></tr>"
        for cause, c in report["per_cause"].items()
    )
    exceptions = "".join(
        f"<li><code>{e['scenario_id']}</code> ({e['truth_cause']}): {e['reason']}</li>"
        for e in report["exceptions"]
    )
    audit_rows = "".join(
        f"<tr><td>{r['seq']}</td><td>{r['stage']}</td><td>{r.get('subscription_id', '') or ''}</td>"
        f"<td><code>{r['hash'][:12]}…</code></td></tr>"
        for r in audit_records
    )

    def _citation_line(cite: dict) -> str:
        source = cite["mapped_from"] or f"LLM ({cite['provenance']})"
        return f"<li><code>{cite['scenario_id']}</code> → {cite['cause']}: {source}</li>"

    citations = "".join(_citation_line(cite) for cite in report.get("classification_citations", []))
    pr_rows = "".join(
        f"<tr><td>{cause}</td><td>{pr['precision']}</td><td>{pr['recall']}</td></tr>"
        for cause, pr in report["classifier"].get("per_cause", {}).items()
    )
    c = report["classifier"]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Rebound batch report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; color: #1a1a1a; background:#fafafa; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; background: white; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }}
.metric {{ font-size: 1.6rem; font-weight: bold; }}
.zero-required {{ color: #0a7d2c; }}
section {{ margin-bottom: 2rem; padding: 1rem 1.5rem; background: white; border-radius: 8px; border: 1px solid #e5e5e5; }}
h1 {{ color: #1a1a2e; }}
h2 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }}
code {{ background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px; }}
</style></head>
<body>
<h1>Rebound — batch report</h1>
<section>
  <p>Duplicates rejected: <span class="metric">{report['duplicates_rejected']}</span></p>
  <p>Double charges (must be 0): <span class="metric zero-required">{report['double_charges']}</span></p>
  <p>Policy violations (must be 0): <span class="metric zero-required">{report['policy_violations']}</span></p>
  <p>False escalations: <span class="metric">{report['false_escalations']}</span></p>
</section>
<section>
  <h2>Per-cause outcomes (policy outcome, not money recovered)</h2>
  <table><tr><th>Cause</th><th>Allowed</th><th>Blocked</th><th>Escalated</th></tr>{rows}</table>
</section>
<section>
  <h2>Classifier (held-out, n={c['heldout_count']})</h2>
  <p>Overall accuracy: {c['accuracy']} · Abstain rate: {c['abstain_rate']}</p>
  <table><tr><th>Cause</th><th>Precision</th><th>Recall</th></tr>{pr_rows}</table>
</section>
<section>
  <h2>Exceptions</h2>
  <ul>{exceptions}</ul>
</section>
<section>
  <h2>Classification citations (every non-unknown cause traced to its source field)</h2>
  <ul>{citations}</ul>
</section>
<section>
  <h2>Audit chain (tamper-evident — run <code>rebound verify-audit</code> to check)</h2>
  <table><tr><th>Seq</th><th>Stage</th><th>Subscription</th><th>Hash</th></tr>{audit_rows}</table>
</section>
<section>
  <h2>Where AI was and was not used</h2>
  <p>Documented-field classification: rules only. Ambiguous-text classification: LLM, with confidence + abstain.
     Choosing and authorising every action: deterministic code only. Nudge text: LLM (or static template offline), logged, never sent.</p>
</section>
</body></html>"""
