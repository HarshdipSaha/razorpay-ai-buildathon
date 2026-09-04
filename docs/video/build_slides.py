"""Generates the 11 video slide HTML files and narration .txt files for the Rebound demo video.

Design language borrows directly from the product's own real UI
(rebound/sim/report_html.py — the "audit dossier" report page): near-black
ground, bone ink, amber accent, sage/red for ok/bad, mono for data and
labels, hairline 1px rules, no cards, no shadows, no rounded corners,
corner "crosshair" ticks reserved for literal exhibit/case-file moments.

Every scene has a deliberately different composition — no repeated
kicker-plus-heading-plus-card template. On-screen headline/support text is
taken verbatim from _copydesk_final.md; layout composing that text is free.

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
  :root {
    --ground:#0a0b0d; --ink:#e8e6df; --dim:#8a8d94; --hair:#24262b;
    --amber:#e8a33d; --ok:#7fae6c; --bad:#c06a5f;
    --mono: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }
  * { box-sizing:border-box; }
  html, body { margin:0; padding:0; }
  ::selection { background:var(--amber); color:#0a0b0d; }
  .stage {
    width:1280px; height:720px; position:relative; overflow:hidden;
    background:var(--ground); color:var(--ink); font-family:var(--sans);
    -webkit-font-smoothing:antialiased;
  }
  .mono { font-family:var(--mono); font-variant-numeric:tabular-nums; }
  .dim { color:var(--dim); }
  .amber { color:var(--amber); }
  .ok { color:var(--ok); }
  .bad { color:var(--bad); }

  h1.headline {
    font-size:46px; font-weight:600; letter-spacing:-0.01em; line-height:1.2;
    margin:0; color:var(--ink); max-width:1020px; text-wrap:balance;
  }
  p.support {
    font-size:22px; line-height:1.55; color:var(--dim); margin:0; max-width:840px;
    font-weight:400;
  }
  .tag {
    display:inline-block; font-family:var(--mono); font-size:13px; letter-spacing:.12em;
    text-transform:uppercase; color:var(--amber); border:1px solid var(--amber);
    padding:5px 12px; line-height:1;
  }
  .tag.dim { color:var(--dim); border-color:var(--hair); }

  .tick { position:absolute; width:16px; height:16px; border:1px solid var(--amber); opacity:.55; }
  .tick.tl { top:0; left:0; border-right:none; border-bottom:none; }
  .tick.tr { top:0; right:0; border-left:none; border-bottom:none; }
  .tick.bl { bottom:0; left:0; border-right:none; border-top:none; }
  .tick.br { bottom:0; right:0; border-left:none; border-top:none; }

  .meta { font-family:var(--mono); font-size:14px; letter-spacing:.08em; color:var(--dim); }
</style>
"""

def page(body: str, name: str):
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"{CSS}</head><body><div class='stage'>{body}</div></body></html>"
    )
    (SLIDES / f"{name}.html").write_text(html, encoding="utf-8")

# ---------- Scene 1: Title (cover / bookend with scene 11) ----------
page("""
<span class="tick tl" style="top:40px;left:40px;"></span>
<span class="tick tr" style="top:40px;right:40px;"></span>
<span class="tick bl" style="bottom:40px;left:40px;"></span>
<span class="tick br" style="bottom:40px;right:40px;"></span>
<div class="meta" style="position:absolute; top:56px; right:64px; text-align:right;">Razorpay AI Buildathon &middot; Track 3</div>
<div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 120px;">
  <h1 style="font-size:92px; font-weight:600; letter-spacing:-0.02em; margin:0 0 30px; color:var(--ink);">Rebound</h1>
  <p class="support" style="font-size:25px; text-align:center;">Razorpay gives up after four failed charges.<br>Rebound picks it up from there.</p>
</div>
""", "01_title")

# ---------- Scene 2: Architecture (single diagram, minimal text) ----------
page("""
<div style="padding:64px 80px; height:100%; display:flex; flex-direction:column;">
  <h1 class="headline" style="font-size:48px;">Words, not wallets.</h1>
  <div style="flex:1; display:flex; align-items:center; justify-content:center;">
    <div class="mono" style="font-size:27px; letter-spacing:.01em; text-align:center; color:var(--ink);">
      classify <span class="dim">&rarr;</span> <span class="amber" style="font-weight:600;">gate</span> <span class="dim">&rarr;</span> act,
      <span class="dim">in that order, every time.</span>
    </div>
  </div>
  <div style="display:grid; grid-template-columns:1fr 1px 1fr; column-gap:56px; border-top:1px solid var(--hair); padding-top:32px; margin-bottom:8px;">
    <div>
      <div class="tag dim">Model</div>
      <p class="support" style="margin-top:16px; font-size:19px;">Writes a label or a sentence. Never an action, never a money API.</p>
    </div>
    <div style="background:var(--hair);"></div>
    <div>
      <div class="tag">Gate</div>
      <p class="support" style="margin-top:16px; font-size:19px;">Plain rules decide whether the proposed action actually happens.</p>
    </div>
  </div>
</div>
""", "02_architecture")

# ---------- Scene 3: tests (trimmed terminal excerpt) ----------
page("""
<div style="padding:88px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:54px; margin-bottom:56px;">54 tests. All passing.</h1>
  <div class="mono" style="font-size:22px; line-height:1.8; border-top:1px solid var(--hair); padding-top:30px;">
    <div><span class="dim">$</span> pytest -q</div>
    <div class="dim">....................................................  [100%]</div>
    <div class="ok" style="font-weight:600;">54 passed, 1 warning in 5.76s</div>
  </div>
</div>
""", "03_tests")

# ---------- Scene 4: demo run (verdict-strip, callback to the real report) ----------
page("""
<div style="padding:76px 80px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:46px;">60 scenarios, one seed, zero shortcuts.</h1>
  <div style="margin-top:56px; display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--hair); border:1px solid var(--hair);">
    <div style="background:var(--ground); padding:34px 32px;">
      <div class="mono dim" style="font-size:13px; letter-spacing:.1em;">POLICY VIOLATIONS</div>
      <div class="mono ok" style="font-size:60px; font-weight:600; margin-top:10px;">00</div>
    </div>
    <div style="background:var(--ground); padding:34px 32px;">
      <div class="mono dim" style="font-size:13px; letter-spacing:.1em;">DOUBLE CHARGES</div>
      <div class="mono ok" style="font-size:60px; font-weight:600; margin-top:10px;">00</div>
    </div>
    <div style="background:var(--ground); padding:34px 32px;">
      <div class="mono dim" style="font-size:13px; letter-spacing:.1em;">ESCALATED, NOT GUESSED</div>
      <div class="mono amber" style="font-size:60px; font-weight:600; margin-top:10px;">04</div>
    </div>
  </div>
  <p class="support" style="margin-top:36px; font-size:21px;">Every number on screen came from this run.</p>
</div>
""", "04_demo_run")

# ---------- Scene 5: the real report screenshot, dominant ----------
# Image is sized with an explicit pixel width (not a percentage/max-height
# trick, which doesn't resolve against an auto-height flex ancestor) so the
# total composition is guaranteed to fit inside the 720px frame with no
# scroll/clip. The source PNG bakes in a live browser scrollbar along its
# right edge (it's a real screenshot of a page taller than its viewport) --
# an overflow:hidden wrapper narrower than the rendered image crops that
# sliver off. The source screenshot's own 660px crop also ends mid-row
# through Exhibit B's table, so the wrapper additionally crops vertically
# to end cleanly after Exhibit A ("The Verdict") -- one exhibit shown in
# full, not a second one cut off half way through a row.
page("""
<div style="height:100%; display:flex; flex-direction:column; justify-content:center; padding:0 76px;">
  <div style="display:flex; align-items:baseline; justify-content:space-between;">
    <h1 class="headline" style="font-size:32px; margin:0;">The report reads like evidence.</h1>
    <span class="tag">Exhibit</span>
  </div>
  <div style="margin-top:26px; display:flex; justify-content:center;">
    <div style="position:relative; display:inline-block; overflow:hidden; width:980px; height:400px; border:1px solid var(--hair);">
      <span class="tick tl"></span><span class="tick tr"></span>
      <img src="assets/report_crop.png" width="995" style="display:block;">
    </div>
  </div>
  <p class="support" style="text-align:center; margin:22px auto 0; font-size:19px;">Seven exhibits. One ledger. Nothing invented.</p>
</div>
""", "05_metrics")

# ---------- Scene 6: idempotency (ledger diff + numeric outcome) ----------
page("""
<div style="padding:76px 80px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:44px;">I sent the same failure twice, on purpose.</h1>
  <div class="mono" style="margin-top:48px; font-size:20px; line-height:2; border-top:1px solid var(--hair); border-bottom:1px solid var(--hair); padding:24px 0;">
    <div>event_id=evt_scn_7 <span class="dim">&rarr;</span> processed, action taken</div>
    <div>event_id=evt_scn_7 <span class="dim">&rarr;</span> <span class="ok" style="font-weight:600;">duplicate_rejected</span>, zero actions taken</div>
  </div>
  <div style="margin-top:44px; display:flex; align-items:baseline; gap:44px;">
    <div><span class="mono" style="font-size:54px; font-weight:600;">5</span><div class="mono dim" style="font-size:13px; letter-spacing:.08em; margin-top:6px;">DUPLICATES IN</div></div>
    <div class="dim" style="font-size:28px;">&rarr;</div>
    <div><span class="mono ok" style="font-size:54px; font-weight:600;">0</span><div class="mono dim" style="font-size:13px; letter-spacing:.08em; margin-top:6px;">DOUBLE CHARGES OUT</div></div>
  </div>
</div>
""", "06_idempotency")

# ---------- Scene 7: abstain (sparest slide — one idea, one trace) ----------
page("""
<div style="padding:88px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:50px; margin-bottom:52px;">The classifier is allowed to say no.</h1>
  <div class="mono" style="font-size:23px; line-height:2; border-top:1px solid var(--hair); border-bottom:1px solid var(--hair); padding:26px 0;">
    <div>cause = <span class="bad" style="font-weight:600;">unknown</span></div>
    <div>provenance = abstain</div>
    <div><span class="dim">&rarr;</span> gate: <span class="ok" style="font-weight:600;">escalate</span></div>
  </div>
  <p class="support" style="margin-top:28px; font-size:20px;">Unknown always escalates. It never guesses.</p>
</div>
""", "07_abstain")

# ---------- Scene 8: tamper (two-state terminal diff) ----------
page("""
<div style="padding:76px 80px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:44px;">I broke the log on purpose.</h1>
  <div class="mono" style="margin-top:48px; font-size:20px; line-height:1.9; border-top:1px solid var(--hair); padding-top:28px;">
    <div><span class="dim">$</span> verify-audit <span class="dim">&rarr;</span> <span class="ok" style="font-weight:600;">OK: chain valid</span></div>
    <div class="dim" style="margin:10px 0;">// one byte, edited by hand</div>
    <div><span class="dim">$</span> verify-audit <span class="dim">&rarr;</span> <span class="bad" style="font-weight:600;">FAIL: broken at seq 20</span></div>
  </div>
  <p class="support" style="margin-top:40px; font-size:21px;">One byte changed. Verify found it instantly.</p>
</div>
""", "08_tamper")

# ---------- Scene 9: scope decision (short tagged facts, not a bullet list) ----------
page("""
<div style="padding:76px 80px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:44px;">No login. No API key. That's the point.</h1>
  <div style="margin-top:52px; display:flex; flex-direction:column; gap:20px;">
    <div style="display:flex; align-items:baseline; gap:22px;">
      <span class="tag" style="flex-shrink:0;">No API key</span>
      <span style="font-size:19px; color:var(--dim);">Missing key &rarr; the classifier abstains more. Not a crash.</span>
    </div>
    <div style="display:flex; align-items:baseline; gap:22px;">
      <span class="tag" style="flex-shrink:0;">Simulated client</span>
      <span style="font-size:19px; color:var(--dim);">Same interface as production. Zero network calls.</span>
    </div>
    <div style="display:flex; align-items:baseline; gap:22px;">
      <span class="tag" style="flex-shrink:0;">Documented causes</span>
      <span style="font-size:19px; color:var(--dim);">Every mapping cites a real Razorpay field.</span>
    </div>
  </div>
  <p class="support" style="margin-top:40px; font-size:20px;">The one thing that would need a real login, I skipped, and wrote down why.</p>
</div>
""", "09_scope")

# ---------- Scene 10: what broke (severity-labeled list, most severe emphasized) ----------
page("""
<div style="padding:76px 80px; height:100%; display:flex; flex-direction:column; justify-content:center;">
  <h1 class="headline" style="font-size:44px;">Three bugs. One of them mattered.</h1>
  <div style="margin-top:50px; display:flex; flex-direction:column; gap:24px;">
    <div style="display:flex; align-items:baseline; gap:24px;">
      <span class="mono dim" style="font-size:13px; letter-spacing:.08em; width:190px; flex-shrink:0;">CAUGHT ON WINDOWS</span>
      <span style="font-size:20px; color:var(--dim);">A Unicode arrow crashed the report output.</span>
    </div>
    <div style="display:flex; align-items:baseline; gap:24px;">
      <span class="mono dim" style="font-size:13px; letter-spacing:.08em; width:190px; flex-shrink:0;">CAUGHT IN DESIGN</span>
      <span style="font-size:20px; color:var(--dim);">The offline demo would've needed a real Razorpay login.</span>
    </div>
    <div style="display:flex; align-items:baseline; gap:24px;">
      <span class="mono amber" style="font-size:13px; letter-spacing:.08em; width:190px; flex-shrink:0; font-weight:600;">WOULD HAVE SHIPPED</span>
      <span style="font-size:21px; color:var(--ink); font-weight:500;">A policy off-by-one would've silently escalated 15 of 60 scenarios.</span>
    </div>
  </div>
  <p class="support" style="margin-top:42px; font-size:19px;">The full list, and the fix, is in <span class="mono">FAILURES.md</span>.</p>
</div>
""", "10_whatbroke")

# ---------- Scene 11: closing (bookend of scene 1) ----------
page("""
<span class="tick tl" style="top:40px;left:40px;"></span>
<span class="tick tr" style="top:40px;right:40px;"></span>
<span class="tick bl" style="bottom:40px;left:40px;"></span>
<span class="tick br" style="bottom:40px;right:40px;"></span>
<div class="meta" style="position:absolute; top:56px; left:64px;">Rebound</div>
<span class="tag" style="position:absolute; top:50px; right:64px; color:var(--ok); border-color:var(--ok);">Case closed</span>
<div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 120px;">
  <h1 style="font-size:64px; font-weight:600; letter-spacing:-0.02em; margin:0 0 26px; color:var(--ink);">Rebound</h1>
  <div class="mono dim" style="font-size:16px; letter-spacing:.06em; margin-bottom:34px;">54/54 TESTS &middot; 0 POLICY VIOLATIONS &middot; 0 DOUBLE CHARGES</div>
  <p class="support mono" style="font-size:17px; color:var(--dim);">github.com/HarshdipSaha/razorpay-ai-buildathon</p>
</div>
""", "11_closing")

print("Wrote", len(list(SLIDES.glob("*.html"))), "slide HTML files to", SLIDES)

NARRATION = {
"01_title": "A Razorpay subscription fails to charge four times in a row, and Razorpay just stops. The subscription goes to halted, and the merchant gets a note: charge this one by hand. I built Rebound to pick up right there. It figures out why the payment failed, decides what to do about it, and writes down every step so you can check its work.",
"02_architecture": "Here's the shape of it. A payment fails, and a rule checks Razorpay's own error fields to find the cause. If that's ambiguous, an LLM takes a pass, but it's allowed to say it doesn't know. Then a gate, written as plain rules, decides whether the proposed action actually happens. That's the whole rule: the model deals in words, the gate deals in wallets, and the two never swap jobs.",
"03_tests": "Before I show you anything else, here's proof it runs. Fifty four tests, on this machine, right now.",
"04_demo_run": "Sixty scenarios, seeded so you can reproduce this exact run. Zero policy violations. Zero double charges. The four cases that came back ambiguous got escalated to a person instead of guessed at.",
"05_metrics": "This is the report the batch writes. I redesigned it to read like a case file, not a dashboard: a case number, seven exhibits, a ledger that lists every decision in order. Every number on this page is either an invariant that has to be zero, or a citation back to the exact Razorpay field it came from.",
"06_idempotency": "Razorpay retries webhooks, so five of the sixty scenarios get their failure delivered twice, on purpose. The second delivery never reaches the classifier: the dedupe check runs first, and it's a database constraint on the event ID. Five duplicates in, zero double charges out.",
"07_abstain": "One of the held-out cases was genuinely unclear, so the classifier passed on it. It came back as unknown, and the gate escalates unknown to a person every time. It doesn't guess with someone's money.",
"08_tamper": "Verify passes clean. Then I open the log file and change one byte by hand. Run verify again, and it fails on the exact record I touched. Each entry's hash depends on the one before it, so there's nowhere to hide a change.",
"09_scope": "You don't need a Razorpay account to run any of this. The causes come from Razorpay's own published error fields, cited in the code, and the batch runs against a simulated client I wrote myself so none of it touches a real network. Drop the Anthropic key and the classifier just abstains more, which the design already treats as a fine outcome.",
"10_whatbroke": "Windows choked on a character the report tried to print, which was the easy one. An early version would have needed a real Razorpay login just to run the offline demo, so I built a simulated client instead. The one that mattered was a one-line policy bug: it would have quietly escalated 15 of the 60 scenarios for no reason, and I caught it by reading the gate's logic by hand, before I'd written any code.",
"11_closing": "That's Rebound: words from the model, decisions from the gate, and a ledger that proves which one did what. You don't have to trust the demo. You can read it.",
}

for name, text in NARRATION.items():
    (AUDIO / f"{name}.txt").write_text(text, encoding="utf-8")

print("Wrote", len(NARRATION), "narration text files to", AUDIO)
