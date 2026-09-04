"""Renders the batch report as a self-contained "audit dossier" HTML page.

Direction: forensic evidence-board / audit-dossier (surface brief:
.impeccable/surfaces/rebound-sim-report-html-py.md, seed 9f883699, assigned
index 4 — raised with Kraftwerk's traffic-signal state vocabulary and the
design-annual plate section's registration-mark/hairline precision). Every
claim in the report is either an invariant that must read as zero, or a
citation back to a real field or hash — nothing decorative stands in for
data, per PRODUCT.md's product principles.

No external requests: system font stacks only, no CDN, no fetched assets.
Case number is derived deterministically from the report's own content.
"""
from __future__ import annotations
import hashlib
import html
import json


def _case_id(report: dict) -> str:
    digest = hashlib.sha256(json.dumps(report, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:8].upper()


def _esc(value) -> str:
    return html.escape(str(value))


_CAUSE_LABEL = {
    "insufficient_funds": "Insufficient funds",
    "instrument_expired_or_blocked": "Instrument expired / blocked",
    "authentication_failed": "Authentication failed",
    "bank_or_gateway_error": "Bank / gateway error",
    "mandate_not_active": "Mandate not active",
    "limit_exceeded": "Limit exceeded",
    "unknown": "Unknown (ambiguous)",
}


def _label(cause: str) -> str:
    return _CAUSE_LABEL.get(cause, cause)


def _verdict_block(label: str, value: int, id_letter: str) -> str:
    ok = value == 0
    cls = "ok" if ok else "bad"
    stamp = "CLEAR" if ok else "FLAGGED"
    return f"""<div class="verdict-item {cls}">
  <div class="verdict-id">{id_letter}</div>
  <div class="verdict-value">{value:02d}</div>
  <div class="verdict-label">{_esc(label)}</div>
  <div class="verdict-stamp">{stamp}</div>
</div>"""


def _exhibit_open(letter: str, title: str) -> str:
    return f"""<section class="exhibit">
  <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
  <header class="exhibit-head"><span class="exhibit-tag">EXHIBIT {letter}</span><h2>{_esc(title)}</h2></header>
  <div class="exhibit-body">"""


_EXHIBIT_CLOSE = "</div></section>"


def render_html(report: dict, audit_records: list[dict]) -> str:
    case_id = _case_id(report)
    total_scenarios = sum(sum(v.values()) for v in report["per_cause"].values())
    c = report["classifier"]

    # --- EXHIBIT A: the verdict ---
    verdict = "".join([
        _verdict_block("Double charges", report["double_charges"], "A1"),
        _verdict_block("Policy violations", report["policy_violations"], "A2"),
        _verdict_block("False escalations", report["false_escalations"], "A3"),
    ])

    # --- EXHIBIT B: disposition by cause ---
    cause_rows = "".join(
        f"""<tr data-cause="{_esc(cause)}">
  <td class="mono cause-name" title="{_esc(cause)}">{_esc(_label(cause))}</td>
  <td class="num"><span class="chip ok">{counts['allowed']}</span></td>
  <td class="num"><span class="chip bad">{counts['blocked']}</span></td>
  <td class="num"><span class="chip warn">{counts['escalated']}</span></td>
  <td class="num mono dim">{sum(counts.values())}</td>
</tr>"""
        for cause, counts in report["per_cause"].items()
    )

    # --- EXHIBIT C: classifier findings ---
    pr_rows = "".join(
        f"""<tr>
  <td class="mono cause-name">{_esc(_label(cause))}</td>
  <td class="num mono">{'%.2f' % pr['precision'] if pr['precision'] is not None else '—'}</td>
  <td class="num mono">{'%.2f' % pr['recall'] if pr['recall'] is not None else '—'}</td>
</tr>"""
        for cause, pr in c.get("per_cause", {}).items()
    )
    confusion_rows = "".join(
        f'<div class="confusion-row"><span class="mono">{_esc(k.split("->")[0])}</span>'
        f'<span class="arrow">&rarr;</span><span class="mono">{_esc(k.split("->")[1])}</span>'
        f'<span class="chip dim">&times;{v}</span></div>'
        for k, v in sorted(c.get("confusion_matrix", {}).items())
    )
    accuracy_pct = f"{c['accuracy']*100:.0f}%" if c.get("accuracy") is not None else "—"
    abstain_pct = f"{c['abstain_rate']*100:.0f}%" if c.get("abstain_rate") is not None else "—"

    # --- EXHIBIT D: chain of evidence (citations) ---
    citation_rows = "".join(
        f"""<div class="citation-row">
  <span class="mono citation-id">{_esc(cite['scenario_id'])}</span>
  <span class="arrow">&rarr;</span>
  <span class="mono">{_esc(_label(cite['cause']))}</span>
  <span class="citation-source">{_esc(cite['mapped_from'] or f"LLM ({cite['provenance']})")}</span>
</div>"""
        for cite in report.get("classification_citations", [])
    )

    # --- EXHIBIT E: custody ledger (audit chain) ---
    ledger_rows = "".join(
        f"""<div class="ledger-row">
  <span class="mono ledger-seq">{r['seq']:04d}</span>
  <span class="ledger-stage">{_esc(r['stage'])}</span>
  <span class="mono ledger-sub dim">{_esc(r.get('subscription_id') or '—')}</span>
  <span class="mono ledger-hash">{_esc(r['hash'][:16])}&hellip;</span>
</div>"""
        for r in audit_records
    )
    ledger_count = len(audit_records)

    # --- EXHIBIT F: flagged items (exceptions) ---
    exception_rows = "".join(
        f"""<div class="flag-row">
  <span class="mono flag-id">{_esc(e['scenario_id'])}</span>
  <span class="mono">{_esc(_label(e['truth_cause']))}</span>
  <span class="flag-reason">{_esc(e['reason'])}</span>
</div>"""
        for e in report["exceptions"]
    ) or '<div class="flag-empty">No unresolved items in this batch.</div>'

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rebound — Batch Audit Report {case_id}</title>
<style>
:root {{
  --ground:#0a0b0d; --panel:#0f1114; --ink:#e8e6df; --dim:#8a8d94; --hair:#26282d;
  --amber:#e8a33d; --ok:#7fae6c; --warn:#e8a33d; --bad:#c06a5f;
  --mono: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
  --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}
* {{ box-sizing:border-box; }}
::selection {{ background:var(--amber); color:#0a0b0d; }}
body {{
  margin:0; background:var(--ground); color:var(--ink); font-family:var(--sans);
  font-size:16px; line-height:1.5; -webkit-font-smoothing:antialiased;
}}
a {{ color:var(--amber); }}
.mono {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.dim {{ color:var(--dim); }}
.wrap {{ max-width:960px; margin:0 auto; padding:0 28px 80px; }}

/* ---- case header ---- */
.case-head {{
  display:flex; justify-content:space-between; align-items:flex-end;
  padding:36px 0 20px; border-bottom:1px solid var(--hair);
}}
.case-head h1 {{ margin:0; font-size:27px; font-weight:600; letter-spacing:-0.01em; }}
.case-head h1 .dim-part {{ color:var(--dim); font-weight:500; }}
.case-meta {{ text-align:right; font-family:var(--mono); font-size:12px; color:var(--dim); letter-spacing:.03em; line-height:1.8; }}
.case-meta .case-no {{ color:var(--amber); font-size:14px; }}

/* ---- verdict (exhibit A) ---- */
.verdict-strip {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--hair); margin:24px 0 0; border:1px solid var(--hair); }}
.verdict-item {{ background:var(--panel); padding:22px 20px; position:relative; }}
.verdict-id {{ font-family:var(--mono); font-size:11px; color:var(--dim); letter-spacing:.1em; }}
.verdict-value {{ font-family:var(--mono); font-size:56px; font-weight:600; margin:4px 0; font-variant-numeric:tabular-nums; }}
.verdict-item.ok .verdict-value {{ color:var(--ok); }}
.verdict-item.bad .verdict-value {{ color:var(--bad); }}
.verdict-label {{ font-size:14px; color:var(--ink); }}
.verdict-stamp {{
  position:absolute; top:18px; right:18px; font-family:var(--mono); font-size:11px;
  letter-spacing:.1em; padding:3px 8px; border:1px solid currentColor;
}}
.verdict-item.ok .verdict-stamp {{ color:var(--ok); }}
.verdict-item.bad .verdict-stamp {{ color:var(--bad); }}
.verdict-footnote {{ font-size:13px; color:var(--dim); margin:14px 2px 0; }}
.verdict-footnote b {{ color:var(--ink); font-weight:600; }}

/* ---- exhibits ---- */
.exhibit {{ position:relative; margin-top:52px; padding:0 2px; }}
.tick {{ position:absolute; width:10px; height:10px; border:1px solid var(--amber); opacity:.55; }}
.tick.tl {{ top:-1px; left:-1px; border-right:none; border-bottom:none; }}
.tick.tr {{ top:-1px; right:-1px; border-left:none; border-bottom:none; }}
.tick.bl {{ bottom:-1px; left:-1px; border-right:none; border-top:none; }}
.tick.br {{ bottom:-1px; right:-1px; border-left:none; border-top:none; }}
.exhibit-head {{ display:flex; align-items:baseline; gap:14px; padding:14px 4px; border-bottom:1px solid var(--hair); }}
.exhibit-tag {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em; color:var(--amber); flex-shrink:0; }}
.exhibit-head h2 {{ margin:0; font-size:16px; font-weight:600; color:var(--ink); }}
.exhibit-body {{ padding:20px 4px 4px; }}

/* ---- tables ---- */
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; font-family:var(--mono); font-size:11px; letter-spacing:.08em; color:var(--dim); text-transform:uppercase; font-weight:500; padding:0 12px 10px 0; border-bottom:1px solid var(--hair); }}
td {{ padding:11px 12px 11px 0; border-bottom:1px solid var(--hair); font-size:14px; }}
tr:last-child td {{ border-bottom:none; }}
.num {{ text-align:right; }}
.cause-name {{ color:var(--ink); }}
.chip {{ display:inline-block; min-width:28px; padding:2px 8px; font-family:var(--mono); font-size:13px; text-align:center; border:1px solid currentColor; }}
.chip.ok {{ color:var(--ok); }} .chip.warn {{ color:var(--warn); }} .chip.bad {{ color:var(--bad); }} .chip.dim {{ color:var(--dim); border-color:var(--hair); }}

/* ---- classifier summary ---- */
.stat-row {{ display:flex; gap:40px; margin-bottom:22px; }}
.stat {{ }}
.stat .n {{ font-family:var(--mono); font-size:32px; font-weight:600; color:var(--ink); }}
.stat .l {{ font-size:12px; color:var(--dim); margin-top:2px; }}
.confusion {{ margin-top:22px; border-top:1px solid var(--hair); padding-top:16px; }}
.confusion-label {{ font-family:var(--mono); font-size:12px; letter-spacing:.02em; color:var(--dim); margin-bottom:10px; }}
.confusion-row {{ display:flex; align-items:center; flex-wrap:wrap; gap:6px 10px; font-size:13px; padding:4px 0; overflow-wrap:anywhere; }}
.arrow {{ color:var(--dim); }}

/* ---- citations / ledger / flags: monospace evidence lists ---- */
.citation-row, .ledger-row, .flag-row {{
  display:grid; align-items:center; gap:14px; padding:8px 0; border-bottom:1px solid var(--hair); font-size:13px;
}}
.citation-row {{ grid-template-columns:110px 20px 190px 1fr; }}
.ledger-row {{ grid-template-columns:56px 150px 140px 1fr; }}
.flag-row {{ grid-template-columns:110px 190px 1fr; }}
.citation-row:last-child, .ledger-row:last-child, .flag-row:last-child {{ border-bottom:none; }}
.citation-source {{ color:var(--dim); }}
.ledger-stage {{ text-transform:uppercase; font-size:12px; letter-spacing:.03em; color:var(--dim); }}
.ledger-hash {{ color:var(--amber); }}
.flag-reason {{ color:var(--dim); }}
.flag-empty {{ font-size:13px; color:var(--dim); padding:10px 0; }}
.ledger-scroll {{ max-height:340px; overflow-y:auto; }}
.ledger-scroll::-webkit-scrollbar {{ width:8px; }}
.ledger-scroll::-webkit-scrollbar-track {{ background:var(--panel); }}
.ledger-scroll::-webkit-scrollbar-thumb {{ background:var(--hair); }}
.ledger-note {{ font-size:12px; color:var(--dim); margin-top:12px; }}

/* ---- signed statement ---- */
.statement {{
  margin-top:52px; border:1px solid var(--hair); padding:26px 28px; background:var(--panel); position:relative;
}}
.statement p {{ margin:0 0 10px; font-size:14px; color:var(--ink); }}
.statement p:last-of-type {{ margin-bottom:0; }}
.statement .sign {{ margin-top:18px; padding-top:16px; border-top:1px solid var(--hair); font-family:var(--mono); font-size:12px; letter-spacing:.04em; color:var(--dim); display:flex; justify-content:space-between; }}

footer {{ text-align:center; font-family:var(--mono); font-size:12px; color:var(--dim); letter-spacing:.04em; margin-top:60px; padding-top:24px; border-top:1px solid var(--hair); }}

@media (max-width:640px) {{
  .wrap {{ padding:0 16px 60px; }}
  .case-head {{ flex-direction:column; align-items:flex-start; gap:10px; }}
  .case-meta {{ text-align:left; }}
  .verdict-strip {{ grid-template-columns:1fr; }}
  .stat-row {{ gap:24px; flex-wrap:wrap; }}
  .citation-row {{ grid-template-columns:1fr; gap:2px; }}
  .ledger-row {{ grid-template-columns:1fr; gap:2px; }}
  .flag-row {{ grid-template-columns:1fr; gap:2px; }}
  th:nth-child(4), td:nth-child(4) {{ display:none; }}
}}
</style>
</head>
<body>
<div class="wrap">

  <div class="case-head">
    <div>
      <h1>Rebound <span class="dim-part">— Batch Audit Report</span></h1>
    </div>
    <div class="case-meta">
      <div class="case-no">CASE No. {case_id}</div>
      <div>Razorpay AI Buildathon &middot; Track 3</div>
      <div>{total_scenarios} scenarios &middot; {ledger_count} ledger entries</div>
    </div>
  </div>

  {_exhibit_open("A", "The Verdict")}
    <div class="verdict-strip">{verdict}</div>
    <p class="verdict-footnote"><b>{report['duplicates_rejected']}</b> duplicate webhook redeliveries were injected on purpose during this run and rejected before reaching any classifier or executor — see Exhibit E.</p>
  {_EXHIBIT_CLOSE}

  {_exhibit_open("B", "Disposition by Cause")}
    <table>
      <thead><tr><th>Cause</th><th class="num">Allowed</th><th class="num">Blocked</th><th class="num">Escalated</th><th class="num">Total</th></tr></thead>
      <tbody>{cause_rows}</tbody>
    </table>
  {_EXHIBIT_CLOSE}

  {_exhibit_open("C", "Classifier Findings")}
    <div class="stat-row">
      <div class="stat"><div class="n">{accuracy_pct}</div><div class="l">Accuracy &middot; held-out (n={c['heldout_count']})</div></div>
      <div class="stat"><div class="n">{abstain_pct}</div><div class="l">Abstain rate</div></div>
    </div>
    <table>
      <thead><tr><th>Cause</th><th class="num">Precision</th><th class="num">Recall</th></tr></thead>
      <tbody>{pr_rows}</tbody>
    </table>
    <div class="confusion">
      <div class="confusion-label">Confusion matrix &middot; truth &rarr; predicted</div>
      {confusion_rows}
    </div>
  {_EXHIBIT_CLOSE}

  {_exhibit_open("D", "Chain of Evidence")}
    {citation_rows}
    <p class="ledger-note">Every non-<code class="mono">unknown</code> classification above is traced to the documented Razorpay field it was read from — never a label the model invented.</p>
  {_EXHIBIT_CLOSE}

  {_exhibit_open("E", "Custody Ledger")}
    <div class="ledger-scroll">{ledger_rows}</div>
    <p class="ledger-note">Each entry's hash is derived from the entry before it. Altering any single record breaks every hash after it — run <code class="mono">rebound verify-audit</code> to check.</p>
  {_EXHIBIT_CLOSE}

  {_exhibit_open("F", "Flagged Items")}
    {exception_rows}
  {_EXHIBIT_CLOSE}

  <div class="statement">
    <p><b>Where AI was used:</b> classifying ambiguous free-text failure reasons (with a confidence threshold and an abstain path), and drafting — never sending — customer nudge text.</p>
    <p><b>Where AI was not used:</b> mapping documented Razorpay fields to a cause, choosing an action, authorising an action, or touching a money API. Those are deterministic code, by design, for every record in this dossier.</p>
    <div class="sign"><span>SIGNED &middot; REBOUND POLICY GATE</span><span>CASE {case_id}</span></div>
  </div>

  <footer>REBOUND &middot; github.com/HarshdipSaha/razorpay-ai-buildathon</footer>
</div>
</body></html>"""
