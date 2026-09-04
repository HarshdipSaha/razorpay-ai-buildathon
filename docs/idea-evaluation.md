# Idea Evaluation — hackathon-idea-evaluator rubric

Date: 2026-09-04. Rubric: **Hackathon Idea Evaluator** (hameed0342j/svh → `hackathon-skills/hackathon-idea-evaluator/SKILL.md`, as listed on mcpmarket.com). Six dimensions scored 1–10; **target ≥ 48/60 on corrected (honest) scoring**; anti-inflation rules applied; red flags → abandon. The rubric was read and applied by hand — it was not installed or executed.

Anti-inflation rules used:
- **R1 Novelty — score the tech, not the metaphor.** If the underlying algorithm/technology exists elsewhere, novelty **caps at 7**.
- **R2 Feasibility — penalise data & hardware gaps.** Needs real historical data you don't have → **−2**; paid/non-existent API integrations → **−1**.
- **R3 Impact = technical potential × adoption probability.** Model behaviour-change, cultural, chicken-and-egg, and unit-economics barriers.
- **R4 Demo-ability — mock ≠ real.** Mock-dependent demo → **−1**; static dashboards < interactive; if the core value can't be shown live, it's a pitch, not an entry.

Red flags (abandon): total < 40 · Feasibility < 5 · Demo-ability < 5 · Novelty < 4 · (Impact < 5 AND Novelty < 5).

---

## Rebound (Candidate A, Track 3) — Evaluation, as specified after the council

| Dimension | Score | Justification |
|---|---|---|
| Novelty | **7/10** | The *combination* — post-`halted` recovery typed by documented Razorpay failure cause, wrapped in a deterministic pre-action authoriser with a tamper-evident log — exists in no product (Stripe/Chargebee/Recurly/Slicker are card-decline timing optimisers) and in no paper (zero arXiv hits). But every underlying technique — rule lookup, YAML policy engine, hash-chained log, LLM text classification — exists elsewhere. **R1 cap: 7.** |
| Feasibility | **7/10** | Base 9: clearly achievable MVP; Executor's hour budget closes with a 3-h buffer; all APIs are free in test mode (no R2 API deduction). **R2 data gap −2:** there is no real failed-payment history — the 60-scenario batch is synthetic, seeded from ≤5 real captured payloads and Razorpay's documented error tables. |
| Scalability | **6/10** | Stateless pipeline keyed on `event_id`, so horizontal scale is architecturally possible; but as specified: SQLite, in-process synchronous handling, no queue. Works for thousands of events/day, not millions. |
| Impact | **7/10** | Real problem ($129B failed subscription payments in 2025; median recovery 47.6%). Adoption barrier is low for the buyer that matters here — Razorpay could ship it natively; a merchant adopts by pointing a webhook. Ceiling: RBI e-mandate AFA and UPI-mandate causes are nudge-only by regulation, so a slice of the taxonomy can never auto-recover. |
| Demo-ability | **7/10** | Base 8: three live "wow" moments in under 3 minutes — a duplicate webhook rejected with zero money moved, `verify-audit` failing after one byte is edited, and an LLM abstain routed to a human. **R4 −1:** 55 of 60 scenarios are synthetic and the output is CLI/Markdown, so part of the demo "requires explanation". |
| Domain Fit | **9/10** | Core Track 3 problem; two of the track's own example directions ("Failed-subscription recovery", "Mandate retry sequencer") in one artefact; built on Razorpay's own documented product gap. Not 10: "Hinglish voice recovery" was cut. |
| **TOTAL** | **43/60** | Below the 48 target, above the 40 abandon line. **No red flags.** |

### Verdict
**Build — after sharpening.** The idea is sound, the domain fit is near-perfect, and nothing trips a red flag; but as specified it under-invests in the two dimensions judges *see* (demo-ability, scalability) and takes the full synthetic-data penalty.

### Biggest Risk
**Demo-ability.** A CLI batch over synthetic scenarios is a strong *pitch*; the rubric wants the core value shown *live*. If the video is a terminal scrolling JSON, the panel filters it out before the code loads (the Outsider's warning).

### How to Improve Score (+5 → 48/60)

| # | Change | Dimension | Δ | Why it's honest, not inflation |
|---|---|---|---|---|
| S1 | **Live webhook moment in the demo.** During the video, fail a real test-mode subscription from the Razorpay dashboard and show `subscription.halted` arriving, classified, gated, and acted on — then show the *same* event redelivered and rejected. Fixture batch remains for the metrics. | Demo-ability | +1 (recovers R4) | The core value prop is shown live against Razorpay, not replayed |
| S2 | **Static HTML report** generated from `metrics.json` (one self-contained file, no server): per-cause bars, the audit chain, the exceptions list, a "where AI was / wasn't used" panel. Opened in a browser in the video. | Demo-ability | +1 | Still no UI project; it is a rendered report, so "requires explanation" drops |
| S3 | **Real-payload floor ≥ 10 and card-reason coverage.** Effort 005 captures ≥10 real payloads across the card test numbers (insufficient funds, expired, auth failed, timeout, gateway error) so five of seven causes are exercised end-to-end on real Razorpay responses; synthetic fills the rest and is labelled per scenario. | Feasibility | +1 (partial R2 recovery) | Data is still not "historical", so only half the deduction is recovered |
| S4 | **Explicit scale path.** `store.py` and the processing hand-off sit behind two small interfaces (`EventStore`, `Dispatcher`); README documents the swap (SQLite → Postgres; in-process → queue) and why the `event_id` dedupe makes workers safe. No second implementation is built. | Scalability | +1 | Architecture "handles" more than the demo runs; that is what the dimension measures |
| S5 | **Per-merchant impact framing** in README/video: for a merchant with N subscriptions at the industry 7.9% failure rate, show how many land in `halted`/month and what share falls in auto-recoverable vs nudge-only vs escalate causes under the stated mix. | Impact | +0 (defensibility only) | Makes the impact claim concrete without claiming ₹ |

**Projected after S1–S4: Novelty 7 · Feasibility 8 · Scalability 7 · Impact 7 · Demo-ability 9 · Domain Fit 9 = 47–48/60.** Novelty is capped at 7 by R1 and cannot be bought back; the target is met on the other five.

S1–S4 are added to the baseline as **Amendment A** in `aidlc-docs/inception/01-requirements.md` and scheduled in the implementation plan.

---

## Comparative ranking (the two candidates the council rejected, scored on the same rubric)

| Rank | Idea | Score | Strength | Weakness | Red flag |
|---|---|---|---|---|---|
| 1 | **Rebound** (Track 3) | **43 → 48** | Domain Fit 9 | Scalability 6 | none |
| 2 | AP2 mandate → gated Payment Link bridge (Track 1) | 35 | Domain Fit 8 | **Demo-ability 4** — the protocol it bridges (NPCI UAP) launches after the deadline; nothing real to integrate; R2 −1 for a non-existent API | **Demo-ability < 5 → abandon** |
| 3 | Settlement ↔ bank ↔ GST three-way reconciliation (Track 4) | 35 | Domain Fit 8 | **Novelty 3** — BlackLine/HighRadius/FloQast already ship AI-native versions; R2 −2 for thin test-mode settlement data | **Novelty < 4 → abandon** |

### Combination check (rubric §"Combination Strategy")
Rebound's pre-action authoriser is the same module Candidate B would need. Combining them would not be demo-able in 3 minutes and B's protocol does not exist yet — **not combined**. Recorded as the natural post-hackathon extension: *"wrap any Razorpay agent in the same gate."*
