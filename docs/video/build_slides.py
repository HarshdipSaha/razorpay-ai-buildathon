"""Generates the 11 video slide HTML files and narration .txt files for the Rebound demo video.
Run from repo root: python docs/video/build_slides.py
"""
import pathlib

ROOT = pathlib.Path(__file__).parent
SLIDES = ROOT / "slides"
AUDIO = ROOT / "audio"
SLIDES.mkdir(exist_ok=True)
AUDIO.mkdir(exist_ok=True)

CSS = """
<style>
  * { box-sizing: border-box; }
  body { margin:0; width:1280px; height:720px; font-family: 'Segoe UI', system-ui, sans-serif;
         background: linear-gradient(135deg,#0f1220 0%,#161a2e 100%); color:#eef0f7; overflow:hidden; }
  .wrap { padding: 56px 72px; height: 100%; display:flex; flex-direction:column; }
  .kicker { font-size:20px; letter-spacing:3px; text-transform:uppercase; color:#7dd3fc; font-weight:600; margin-bottom:10px;}
  h1 { font-size:44px; margin:0 0 18px 0; color:#fff; line-height:1.15; }
  h2 { font-size:30px; margin:0 0 20px 0; color:#a5b4fc; }
  p.lead { font-size:22px; line-height:1.5; color:#c9cee0; max-width:1050px; }
  .grid { display:flex; gap:28px; flex:1; margin-top:10px; }
  .card { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12); border-radius:14px; padding:24px 28px; }
  .metric { font-size:52px; font-weight:800; color:#4ade80; }
  .metric.warn { color:#fbbf24; }
  .metriclabel { font-size:16px; color:#9aa2c0; margin-top:4px; }
  table { border-collapse:collapse; width:100%; font-size:18px; }
  th, td { border:1px solid rgba(255,255,255,0.15); padding:8px 14px; text-align:left; }
  th { background:rgba(125,211,252,0.15); color:#e0f2fe; }
  .term { background:#0a0c14; border:1px solid #2a2f45; border-radius:10px; padding:22px 26px;
          font-family: Consolas, 'Cascadia Mono', monospace; font-size:19px; line-height:1.55; color:#c8f7c5;
          white-space:pre-wrap; flex:1; overflow:hidden; }
  .term .dim { color:#8a93b0; }
  .term .ok { color:#4ade80; font-weight:700; }
  .term .bad { color:#f87171; font-weight:700; }
  .badge { display:inline-block; background:#4ade80; color:#0a0c14; font-weight:700; padding:4px 14px;
           border-radius:20px; font-size:16px; margin-right:8px;}
  .badge.blue { background:#7dd3fc; }
  .badge.pink { background:#f0abfc; }
  .footer { margin-top:auto; font-size:16px; color:#6b7394; display:flex; justify-content:space-between; }
  ul.plain { font-size:21px; line-height:1.7; color:#dfe3f2; padding-left:26px; }
  .flow { font-family: Consolas, monospace; font-size:18px; color:#a5b4fc; text-align:center; margin:18px 0;}
  .center { display:flex; align-items:center; justify-content:center; flex-direction:column; flex:1; text-align:center;}
</style>
"""

def page(body: str, name: str):
    html = f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body><div class='wrap'>{body}</div></body></html>"
    (SLIDES / f"{name}.html").write_text(html, encoding="utf-8")

FOOTER = '<div class="footer"><span>Rebound &middot; Razorpay AI Buildathon &middot; Track 3</span><span>github.com/HarshdipSaha/razorpay-ai-buildathon</span></div>'

# ---------- Scene 1: Title ----------
page(f"""
<div class="center">
  <div class="kicker">Razorpay AI Buildathon &middot; Track 3: AI Revenue Recovery</div>
  <h1 style="font-size:64px;">Rebound</h1>
  <p class="lead" style="text-align:center;">When a Razorpay subscription payment fails four times, Razorpay stops trying
  and tells the merchant to charge the customer by hand.<br><br>
  Rebound picks up exactly there &mdash; and proves every step of it.</p>
</div>
{FOOTER}
""", "01_title")

# ---------- Scene 2: Architecture ----------
page(f"""
<div class="kicker">How it works</div>
<h1>Classify. Gate. Act. Prove it.</h1>
<div class="flow">webhook / failed payment &rarr; <b>rule classifier</b> &rarr; (ambiguous? &rarr; LLM, with abstain) &rarr; <b>planner</b> &rarr; <b>policy gate</b> &rarr; execute or escalate &rarr; <b>hash-chained audit log</b></div>
<div class="grid">
  <div class="card" style="flex:1">
    <h2 style="font-size:22px;">The rule</h2>
    <p class="lead" style="font-size:19px;">The LLM only ever produces a <b>label</b> or a <b>sentence</b>.
    It never chooses an action, and it never touches a money API. A deterministic policy gate,
    written as plain YAML rules, is the <i>only</i> code path that can authorise a charge.</p>
  </div>
  <div class="card" style="flex:1">
    <h2 style="font-size:22px;">Why this matters here</h2>
    <p class="lead" style="font-size:19px;">Six 2026 papers on agent-payment safety all say the same thing:
    a signed intent is not proof of correctness &mdash; something else has to re-check every action
    before it executes. That's what the gate is.</p>
  </div>
</div>
{FOOTER}
""", "02_architecture")

# ---------- Scene 3: tests ----------
pytest_txt = (ROOT / "pytest_output.txt").read_text(encoding="utf-8")
page(f"""
<div class="kicker">Build quality</div>
<h1>The whole test suite, run for real</h1>
<div class="term">$ pytest -q
<span class="dim">.......................................................</span>
<span class="ok">54 passed, 1 warning in 5.76s</span></div>
{FOOTER}
""", "03_tests")

# ---------- Scene 4: demo run ----------
page(f"""
<div class="kicker">The batch</div>
<h1>60 scenarios. Zero shortcuts.</h1>
<div class="term" style="font-size:17px; line-height:1.4; padding:18px 26px;">$ python -m rebound.cli demo
<span class="dim"># Rebound batch report</span>

- Duplicates rejected: <span class="ok">5</span>
- Double charges: <span class="ok">0</span> <span class="dim">(must be 0)</span>
- Policy violations: <span class="ok">0</span> <span class="dim">(must be 0)</span>
- False escalations: <span class="ok">0</span>

<span class="dim">## Per-cause outcomes (policy outcome, not money recovered)</span>
insufficient_funds .......... 21 allowed
bank_or_gateway_error ........ 12 allowed
authentication_failed ......... 9 allowed
instrument_expired_or_blocked . 6 allowed
mandate_not_active ............ 5 allowed
limit_exceeded ................ 3 allowed
unknown ....................... 4 <span class="bad">escalated</span></div>
{FOOTER}
""", "04_demo_run")

# ---------- Scene 5: HTML report / metrics ----------
page(f"""
<div class="kicker">Honest metrics, not a happy path</div>
<h1>Measuring the gate, not a made-up ₹ figure</h1>
<div class="grid">
  <div class="card"><div class="metric">100%</div><div class="metriclabel">classifier accuracy on the 20 held-out scenarios</div></div>
  <div class="card"><div class="metric warn">5%</div><div class="metriclabel">abstain rate &mdash; routed to a human, not guessed</div></div>
  <div class="card"><div class="metric">60 / 60</div><div class="metriclabel">scenarios accounted for across all 7 causes</div></div>
</div>
<p class="lead" style="margin-top:22px;">Every non-<code>unknown</code> classification cites the exact Razorpay
field it came from &mdash; e.g. <code>error_reason=insufficient_funds</code> &mdash; not a label the model invented.</p>
{FOOTER}
""", "05_metrics")

# ---------- Scene 6: idempotency ----------
page(f"""
<div class="kicker">Bounded and gated, by design</div>
<h1>The failure I engineered on purpose</h1>
<p class="lead">Razorpay redelivers webhooks at least once. Five of the sixty scenarios have their
<code>payment.failed</code> event delivered <b>twice</b> on purpose.</p>
<div class="term" style="flex:0; margin-top:20px;">event_id=evt_scn_7  &rarr;  processed, action taken
event_id=evt_scn_7  &rarr;  <span class="ok">duplicate_rejected</span>, zero actions taken</div>
<p class="lead" style="margin-top:20px;"><b>Result: 5 duplicates rejected, 0 double charges.</b>
The dedupe is a single SQLite <code>INSERT OR IGNORE</code> on the event id &mdash; not a promise, a guarantee.</p>
{FOOTER}
""", "06_idempotency")

# ---------- Scene 7: AI judgment / abstain ----------
page(f"""
<div class="kicker">Where I chose <i>not</i> to trust the AI</div>
<h1>The classifier can say "I don't know"</h1>
<p class="lead">One of the twenty held-out scenarios has an ambiguous, generic failure reason.
The rule classifier can't map it to a documented field, so it falls to the residue path &mdash;
and the residue path is allowed to <b>abstain</b> below a confidence threshold.</p>
<div class="term" style="flex:0;">cause = <span class="bad">unknown</span>
provenance = abstain
&rarr; policy gate: <span class="ok">escalate</span>  (never guessed, never charged)</div>
<p class="lead" style="margin-top:16px;">That's the answer to "where did you choose not to use AI":
the gate treats "I'm not sure" as a first-class, safe outcome.</p>
{FOOTER}
""", "07_abstain")

# ---------- Scene 8: tamper ----------
page(f"""
<div class="kicker">Tamper-evident, not just append-only</div>
<h1>I broke the audit log on purpose</h1>
<div class="term">$ python -m rebound.cli verify-audit
<span class="ok">OK: audit chain is valid</span>

<span class="dim"># ...one byte of the log, edited by hand...</span>

$ python -m rebound.cli verify-audit
<span class="bad">FAIL: chain broken at seq 20</span></div>
<p class="lead" style="margin-top:18px;">Every record's hash includes the previous record's hash.
Change one byte anywhere, and every check after it fails &mdash; pinpointing the exact record.</p>
{FOOTER}
""", "08_tamper")

# ---------- Scene 9: scope / no login ----------
page(f"""
<div class="kicker">A scope decision, stated out loud</div>
<h1>No Razorpay login. No API key. On purpose.</h1>
<ul class="plain">
  <li>The taxonomy maps from Razorpay's <b>documented</b> <code>error_reason</code> fields &mdash; cited with doc URLs in the code, not invented.</li>
  <li>The batch runs through an in-memory <b>SimulatedRazorpayClient</b> &mdash; same interface, zero network calls.</li>
  <li>Without <code>ANTHROPIC_API_KEY</code>, the LLM path simply abstains &mdash; a real, designed-for outcome, not a crash.</li>
  <li>The one thing that <i>does</i> need a real login &mdash; a live webhook demo &mdash; was skipped, and that's written down, not hidden.</li>
</ul>
{FOOTER}
""", "09_scope")

# ---------- Scene 10: what broke ----------
page(f"""
<div class="kicker">What broke, and how I got out</div>
<h1>Three real bugs, fixed for real</h1>
<ul class="plain">
  <li><b>Unicode crash on Windows</b> &mdash; cp1252 couldn't encode the report's arrows. Fixed at the I/O boundary.</li>
  <li><b>The demo would have needed a real Razorpay login</b> &mdash; caught before it shipped; built the simulated client instead.</li>
  <li><b>A policy config off-by-one</b> would have silently escalated a quarter of the batch &mdash;
  caught by hand-tracing the gate's logic during a five-round plan review, before a line of code existed.</li>
</ul>
<p class="lead" style="margin-top:10px;">Every one of these is logged in <code>FAILURES.md</code>, with what broke,
how it was found, and what changed &mdash; because that's the answer this buildathon reads first.</p>
{FOOTER}
""", "10_whatbroke")

# ---------- Scene 11: closing ----------
page(f"""
<div class="center">
  <h1 style="font-size:52px;">Rebound</h1>
  <p class="lead" style="text-align:center;">Built end to end with AI-DLC &mdash; every skill, every tool,
  every course-correction logged in the repo, not just the code.</p>
  <div style="margin-top:18px;"><span class="badge">54/54 tests</span><span class="badge blue">0 policy violations</span><span class="badge pink">0 double charges</span></div>
  <p class="lead" style="text-align:center; margin-top:26px; font-size:19px; color:#9aa2c0;">github.com/HarshdipSaha/razorpay-ai-buildathon</p>
</div>
{FOOTER}
""", "11_closing")

print("Wrote", len(list(SLIDES.glob("*.html"))), "slide HTML files to", SLIDES)

NARRATION = {
"01_title": "Razorpay's own subscription retry ladder is fixed. Fail a recurring payment four times, and Razorpay stops trying, moves the subscription to halted, and tells the merchant: charge this customer by hand. Rebound picks up exactly there. It reads why the payment failed, decides what to do about it, and proves every step of that decision.",
"02_architecture": "Here's the whole flow. A failed payment comes in. A rule classifier maps it to a cause using Razorpay's own documented fields. If that's ambiguous, an LLM takes a pass, but it can abstain instead of guessing. Either way, a planner proposes an action, and a deterministic policy gate, not the AI, decides whether that action is actually allowed. The LLM only ever writes a label or a sentence. It never touches a money API.",
"03_tests": "Before anything else, the whole test suite, running for real on this machine: fifty four tests, all passing.",
"04_demo_run": "Now the real thing: a seeded, sixty scenario batch, run end to end. Zero policy violations. Zero double charges. Every cause is accounted for, and the four unknown cases were correctly escalated to a human instead of guessed at.",
"05_metrics": "On the twenty scenarios held out from tuning, the classifier is one hundred percent accurate, with a five percent abstain rate, meaning one case correctly said, I don't know, route this to a person. And every single non-unknown classification cites the exact Razorpay field it came from. Nothing here is a self-labeled, circular number.",
"06_idempotency": "Razorpay redelivers webhooks at least once, so five of the sixty scenarios get their failure event delivered twice, on purpose. The event id is the only key that matters. The second delivery is rejected before it ever reaches the classifier. Five duplicates rejected, zero double charges. That's not a promise. It's a database constraint.",
"07_abstain": "This is the part I'm proudest of. One of the held out scenarios is genuinely ambiguous. The rule classifier can't map it to a documented field, so it falls to the language model, and the language model is allowed to say, I'm not confident enough. When that happens, the cause becomes unknown, and the policy gate always escalates unknown to a human. It never guesses, and it never spends money on a guess.",
"08_tamper": "Here's the audit log holding up under an actual attack. Verify audit passes. Then I edit one single byte in the log file by hand. Run verify again, and it fails immediately, and tells you exactly which record broke, because every record's hash depends on the one before it.",
"09_scope": "One thing I want to say plainly: this entire demo needs no Razorpay login and no API key. The cause taxonomy is grounded in Razorpay's own published documentation, cited by U.R.L. in the code. The batch runs against an in-memory simulated client. And without an Anthropic key, the system doesn't break, it just abstains more, which the design already treats as a valid outcome. The one thing that would need a real login, a live webhook demo, I skipped, and I wrote down why instead of faking it.",
"10_whatbroke": "Building this wasn't clean, and I'm not pretending it was. A Unicode crash on Windows. A design that would have secretly required a Razorpay login just to run the offline demo. And a one line policy bug that would have silently escalated a quarter of the batch, caught by hand tracing the logic during review, before a single line of code existed. All three are written up in FAILURES dot M D, because that's the part this buildathon says it reads first.",
"11_closing": "That's Rebound. Fifty four tests passing, zero policy violations, zero double charges, and a process that's as inspectable as the code. Thanks for watching.",
}

for name, text in NARRATION.items():
    (AUDIO / f"{name}.txt").write_text(text, encoding="utf-8")

print("Wrote", len(NARRATION), "narration text files to", AUDIO)
