# LLM Council — idea selection transcript

Date: 2026-09-04. Method: Karpathy-style LLM Council — five independent advisors with distinct thinking lenses answer in parallel; their responses are anonymised and each advisor peer-reviews all five; a chairman synthesises. Advisors were spawned as *fresh* agents (not forks) so none inherited the coordinator's prior lean toward Candidate A.

Inputs: `docs/hackathon-spec.md`, `docs/research-synthesis.md`, and a framed question presenting three candidates:

- **A — Track 3:** halted-subscription recovery agent for India (deterministic root-cause taxonomy → per-cause policy gate → real test-mode recovery actions → hash-chained audit log; LLM only classifies ambiguous text with abstain, and drafts nudges).
- **B — Track 1:** AP2-style mandate → Razorpay gated Payment Link bridge.
- **C — Track 4:** settlement ↔ bank ↔ GST ledger three-way reconciliation.

## Round 1 — advisor positions (condensed)

| Advisor | Pick | Core argument |
|---|---|---|
| **Contrarian** | A, reluctantly | **The diagnosis is fake unless grounded.** Test mode has one lever ("Charge this now" → pass/fail) with no reason-code control, so the 7-cause taxonomy would run on self-invented labels; classifier P/R and "₹ recovered" become circular — the "cherry-picked" sin dressed as a confusion matrix. Fix: trace every cause to documented `payment.failed` fields; report recovery as a policy outcome under a stated decline-mix; the policy gate is the product. |
| **First Principles** | A | Wrong question. The real one: what makes a Razorpay engineer say "I want this person on my team"? Only A proves you read *their* docs and found *their* product gap (fixed retry ladder → `halted` → "charge manually"). Product = audit log + failure story. Keep `FAILURES.md` from hour one. |
| **Expansionist** | A | A hits three separate Track 3 line-items in the brief at once. The e-mandate/UPI-AutoPay taxonomy is a category gap no US/card-centric dunning tool has. Sharpeners: standalone authoriser module; "₹ per cause" headline; one deliberate LLM-abstain case shown on video. |
| **Outsider** | A | The only candidate a layperson understands ("my gym membership failed like this"). B is a bridge to nowhere; C is a smaller version of something. Cut jargon from the video: "tamper-proof record", "a rulebook the AI can't override". Show the ones it got wrong, out loud. |
| **Executor** | A | Only candidate with a concrete hour-zero keystroke. 24-hour budget supplied (setup 0–2, synthetic batch 2–4, core 4–10, LLM 10–13, metrics 13–15, README 15–17, video 17–19, form 19–21, 3h buffer). "Manufacture 5, synthesise 55, say so." Cut Hinglish voice, dashboard, real messaging, >7 causes. |

## Round 2 — anonymised peer review (5 reviewers)

Unanimous on both questions:
- **Strongest: the Contrarian** — the only response that attacked the winning candidate's evidentiary core instead of ratifying it.
- **Biggest blind spot: the Expansionist** — sells the exact number (₹ per cause) that the panel will probe first; never asks whether the novel causes can be *observed* in test mode.

What all five advisors missed (surfaced only in review):
- Webhook **idempotency / redelivery** → double-charge is the most credible real failure story.
- Dunning is multi-day → the demo needs a **simulated clock**.
- **RBI/TRAI consent** and the e-mandate AFA **regulatory ceiling** (re-auth requires customer action → nudge-only).
- Nobody verified whether Razorpay's `error_code` / `error_reason` / `error_source` enums actually distinguish the claimed causes.
- Nobody budgeted the **clean-machine clone-and-run**, the **failure essay**, or the **resume**.

## Round 3 — chairman's verdict

### Where the Council Agrees
All five advisors independently chose **Candidate A** and rejected B and C for the same reasons: B is glue for a protocol (UAP) that launches after the deadline, pitching Razorpay's own agentic-UPI pilots back to Razorpay; C is "a smaller BlackLine" requiring no Razorpay-specific insight.

Four other convergences, reached independently:
- **"LLM classifies, code decides" is a strength, not a cop-out.** The arXiv numbers (46% ledger arithmetic, 0/879 gate) defend it in one slide.
- **Cut Hinglish nudges, dashboards, real SMS/email, and >7 causes.**
- **The policy gate + audit log is the product**, not the recovery agent.
- **Synthetic data must be declared loudly**, with the misses shown.

### Where the Council Clashes
**Expansionist vs. Contrarian on the taxonomy.** Expansionist calls the AFA/UPI-mandate taxonomy "IP nobody has" and wants "₹ recovered per cause" as the headline. Contrarian says exactly those causes cannot be manufactured in test mode, so the labels are self-authored and the per-cause ₹ number is "a coin you weighted." All five reviewers sided with the Contrarian. For an insider panel that knows its own error payloads, the Contrarian is right.

**Recovery rate as headline vs. recovery as policy-outcome.** Resolved in the Contrarian's favour: recovery via `success@razorpay` is deterministic, so the rate measures your decline-mix assumption, not the system.

### Blind Spots the Council Caught
1. **Webhook idempotency and redelivery.** A duplicate `subscription.halted` that double-charges is the one failure a payments panel spots instantly, and the most honest, *real* "what broke" story available.
2. **Time is simulated, not real.** The demo needs an injectable clock.
3. **Regulatory ceiling.** RBI e-mandate AFA re-authorisation requires customer action → nudge-only. A one-line opt-out/consent hard stop shows domain taste cheaply.
4. **The scored non-code deliverables.** Clean-machine clone-and-run, resume quality, writing the failure essay well.

### The Recommendation
**APPROVE Candidate A**, reframed to survive the circularity objection:
1. **Ground the taxonomy in documented codes.** Every cause maps from Razorpay's actual `payment.failed` fields (`error_code`, `error_reason`, `error_source`, `error_step`) and mandate webhooks. Whatever cannot be traced to a documented enum is cut, or kept as a policy row labelled "spec'd, not exercised in test mode".
2. **Report recovery as a policy outcome under a stated decline-mix**, never as "₹ recovered". Headline: *actions authorised / blocked / escalated per cause, false-escalation count, classifier abstain rate* — these measure the gate, which is real.
3. **Make idempotency the engineered failure story.** Replay duplicate webhooks in the batch; show the audit log rejecting the second charge.
4. **Add a simulated clock** so cooldowns and retry caps are exercised.
5. **Add consent/opt-out as a hard stop.**

**Verify at hour zero:** does test mode expose distinguishable `error_code` values on failed subscription charges, and does "Charge this now" drive a subscription to `halted` within minutes rather than T+3 days? If both fail: record 3–5 real payloads and synthesise the rest from those templates.

**Cut:** Hinglish/voice nudges, any UI, real SMS/email, the standalone-module second README, >7 causes, retry-timing optimisation. Budget three hours for README dry-run on a clean clone, the failure essay, and the resume.

### The One Thing to Do First
Create one test-mode Plan and Subscription, hit "Charge this now" to failure, and read the raw `payment.failed` and `subscription.halted` payloads. The `error_code` fields in those two JSON blobs decide whether the taxonomy is real. Nothing else starts until you have them.
