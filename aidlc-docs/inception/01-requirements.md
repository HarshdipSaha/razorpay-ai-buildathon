# Inception · Stage 1 — Requirements

**Project (working name):** **Rebound** — recovery for halted Razorpay subscriptions, under a rulebook the AI cannot override.
**Track:** 3 — AI Revenue Recovery
**Date:** 2026-09-04 · **Depth:** standard · **Status:** awaiting approval (Gate I-1)

Inputs: `docs/hackathon-spec.md`, `docs/research-synthesis.md`, `docs/council-verdict.md`, Razorpay docs fact-check (§7).

---

## 1. Problem

Razorpay's recurring-payment retry ladder is **fixed and merchant-uncontrollable**: a failed charge is retried on T+1, T+2, T+3, then the subscription moves to `halted` and the merchant is told to *charge manually* ([payment-retries](https://razorpay.com/docs/payments/subscriptions/payment-retries/)). Industry-wide, failed subscription payments cost **$129B in 2025**; involuntary churn is 20–40% of subscription loss and is the *recoverable* kind; median recovery is **47.6%**, top programmes reach 70–85%. Existing recovery tools (Stripe Smart Retries, Chargebee, Recurly, Slicker) are card/US-centric and model none of Razorpay's `halted` state, UPI AutoPay mandate states, or RBI e-mandate re-authorisation. **No academic literature exists on this problem** (arXiv scan, `docs/research-synthesis.md` §2).

The gap is not "retry smarter". It is: *once Razorpay has given up, diagnose why the charge failed from the documented failure fields, choose a bounded, cause-appropriate intervention, execute it through real APIs, and prove afterwards that every money action was authorised.*

## 2. Goals

| # | Goal | Judged under |
|---|---|---|
| G1 | Diagnose the root cause of a failed recurring charge **from documented Razorpay fields**, never from invented labels | Build quality, AI judgment |
| G2 | Every recovery action passes a **deterministic pre-action policy gate** the LLM cannot override; every decision is in a tamper-evident audit log | Build quality, the track's "bounded and gated" bar |
| G3 | Run a **60-scenario batch** with a stated decline-mix and report honest metrics — including the misses and an exceptions list | The track's "measured across a batch" bar |
| G4 | **Engineer a real failure and recover from it** — duplicate webhook delivery must not double-charge | Failure recovery (read first) |
| G5 | Ship: public repo that runs from a clean clone with one command, Mermaid architecture, 5-min video, written failure narrative | Deliverables |

## 3. Non-goals (explicit scope cuts — council verdict)

- No Hinglish/voice; nudges are **drafted and logged**, never sent (no SMS/email/WhatsApp integration).
- No UI / dashboard. CLI + JSON/Markdown report only.
- No retry-**timing** optimisation, no ML training, no fine-tuning.
- No claim of "₹ recovered". Recovery in test mode is deterministic (`success@razorpay`), so a ₹ figure would measure our decline-mix assumption, not the system.
- No more than **7 root causes**.
- No standalone second package/README for the gate (it is a module in this repo, documented in the main README).

## 4. Actors

| Actor | Role |
|---|---|
| **Razorpay (test mode)** | Emits `payment.failed`, `subscription.pending`, `subscription.halted`, `token.*` webhooks; exposes Subscriptions, Invoices, Payment Links APIs |
| **Rebound** | Ingests events, classifies cause, proposes an action, gates it, executes, logs |
| **Merchant operator** | Reads the report; receives escalations; owns anything the gate refuses |
| **Customer** | Never contacted in this build; nudge text is drafted to the log for the operator |
| **LLM (Claude)** | Two narrow jobs — see FR-2b and FR-4c. Never chooses an action. Never touches money. |

## 5. Functional requirements

### FR-1 Ingest (webhooks)
- FR-1.1 HTTP receiver for `payment.failed`, `subscription.pending`, `subscription.halted`, `subscription.charged`, `token.paused`, `token.cancelled`, `token.rejected`.
- FR-1.2 Verify `X-Razorpay-Signature` (HMAC-SHA256 with the webhook secret) before anything else; reject and log on mismatch.
- FR-1.3 **Idempotency:** dedupe on `x-razorpay-event-id` in a local store. A replayed event is acknowledged 200 and logged as `duplicate_rejected`, and **produces no action**. Razorpay delivers at-least-once with exponential backoff for 24 h ([webhook best practices](https://razorpay.com/docs/webhooks/best-practices/)).
- FR-1.4 Respond within 5 s; enqueue processing.
- FR-1.5 A **replay/fixture mode** feeds recorded payloads (real test-mode captures + synthetic) through the same code path as live webhooks.

### FR-2 Root-cause classification
- FR-2a **Deterministic first.** Map `error_reason` (primary) and `error_source` + `error_step` (secondary) from the payment entity to one of the 7 causes in §6. Pure lookup; no model.
- FR-2b **LLM only on the residue.** If the mapped fields are generic (`payment_failed`) or `null` *and* a free-text `error_description` exists, the LLM classifies into the same 7 causes and returns `{cause, confidence, rationale}`. Below a confidence threshold (default 0.75) it **abstains** → cause = `unknown` → policy forces `escalate`.
- FR-2c Every classification records its provenance: `rule` | `llm` | `abstain`.
- FR-2d LLM calls are **cached to disk** keyed by input hash so batch reruns are deterministic and free.

### FR-3 Policy gate (pre-action authoriser)
- FR-3.1 Every proposed action is a structured request `{subscription_id, cause, action, amount, attempt_no, sim_time}` evaluated against a **declarative policy table** (YAML). Verdict: `allow` | `block` | `escalate`, with the rule id that fired.
- FR-3.2 Per-cause rows define: permitted actions, max attempts, cooldown between attempts, amount cap (must equal the invoice amount — no upsell, no partial), contact cap for nudges.
- FR-3.3 **Hard stops (global, evaluated first):** customer opt-out / no-consent flag; dispute or refund open on the subscription; subscription `cancelled` or `completed`; token `cancelled`/`rejected`; attempt count exhausted; amount mismatch; duplicate event.
- FR-3.4 The gate is the **only** code path that can call a money API. The LLM has no tool access to it.
- FR-3.5 The gate is unit-tested with a table of allow/block/escalate cases, including every hard stop.

### FR-4 Actions (Razorpay test mode)
- FR-4a `charge_invoice` — charge the halted subscription's pending invoice via the Invoices API (the documented post-halt path: halted subscriptions expose "Issue Invoice").
- FR-4b `payment_link` — create a Payment Link for the invoice amount so the customer can re-authorise/pay with a different instrument.
- FR-4c `nudge` — the LLM drafts a short customer message in English (cause-specific: e.g. "your card has expired", "please re-approve your UPI AutoPay mandate"). **Logged, not sent.**
- FR-4d `escalate` — write a structured ticket to the exceptions list for the operator.
- FR-4e `noop_wait` — hold until `sim_time` passes the cooldown.
- FR-4f **Simulated clock.** All cooldowns and retry windows use an injectable clock so a multi-day recovery sequence runs in seconds in the batch.

### FR-5 Audit log
- FR-5.1 Append-only JSONL. Each record: `{seq, ts, sim_time, event_id, subscription_id, stage, payload, prev_hash, hash}` where `hash = sha256(prev_hash + canonical_json(record_without_hash))`.
- FR-5.2 Stages logged: `event_received` · `duplicate_rejected` · `classified` (with provenance) · `action_proposed` · `policy_verdict` (with rule id) · `action_executed` / `action_blocked` · `outcome`.
- FR-5.3 `verify_audit.py` recomputes the chain and reports the first break, if any.

### FR-6 Batch harness and metrics
- FR-6.1 **60 scenarios**, deterministic seed, stated decline-mix (e.g. 30% insufficient funds, 15% expired card, 15% auth failed, 10% bank/gateway error, 10% mandate paused/not-active, 10% timeout, 10% generic/ambiguous). Each scenario: failure payload, ground-truth cause, subscription state, consent flag, and any hard-stop condition. ~5 built from **real payloads captured in test mode**; the rest synthesised from those templates and the documented error tables. The README states this split explicitly.
- FR-6.2 A **held-out** labelled subset (≥20) is never seen while writing rules or prompts; classifier precision/recall/abstain-rate are reported on it only.
- FR-6.3 The batch **deliberately replays** ≥5 duplicate webhook deliveries; the report counts `duplicate_rejected` and asserts zero double-charges.
- FR-6.4 Report (Markdown + JSON), headline metrics:
  - actions **authorised / blocked / escalated** per cause;
  - **policy violations** (any money action without an `allow` verdict) — must be 0;
  - **false escalations** (escalated where ground truth had a permitted action);
  - classifier **precision / recall per cause** and **abstain rate** on the held-out set, with the confusion matrix;
  - **duplicate deliveries rejected** / double-charges (must be 0);
  - **exceptions list** — every scenario the system could not resolve, with the reason.
- FR-6.5 Recovery outcomes are reported as *"policy outcome under the stated decline-mix"* — never as money recovered.

### FR-7 Failure narrative
- FR-7.1 `FAILURES.md` is kept from hour zero: what broke, how it was found, what changed. The idempotency replay (FR-6.3) is the anchored, reproducible entry; real breakages during the build are appended as they happen.

### FR-8 Deliverables
- FR-8.1 README: what it does in plain language (no jargon in the first paragraph), architecture (Mermaid), one-command run from a clean clone (`make demo` or `python -m rebound demo`), the metrics table pasted from the last run, the synthetic-data disclosure, where AI is and is not used, links to `FAILURES.md` and `aidlc-docs/`.
- FR-8.2 5-minute video: batch run → audit log → one duplicate rejected → one LLM abstain escalated → metrics. Plain language.
- FR-8.3 Form fields drafted in `docs/submission.md` before filling the one-shot form.

## 6. Root-cause taxonomy — grounded to documented Razorpay fields

Sources: [payment entity](https://razorpay.com/docs/api/payments/entity/) · [error parameters per method](https://razorpay.com/docs/errors/payments/payment-methods-error-parameters/) · [error reasons list](https://razorpay.com/docs/errors/payments/list/) · [e-mandate errors](https://razorpay.com/docs/payments/recurring-payments/emandate/errors/) · [recurring webhooks](https://razorpay.com/docs/api/payments/recurring-payments/webhooks/)

| # | Cause | Documented `error_reason` values (primary) | `error_source` / `error_step` hints | Test-mode reproducible? | Default policy |
|---|---|---|---|---|---|
| 1 | `insufficient_funds` | `insufficient_funds` | source `customer`/`issuer_bank`, step `payment_authorization` | **Yes (card 4100 2800 0008 0001)** | `charge_invoice` after cooldown, ≤3 attempts, then `payment_link` + `nudge`, then escalate |
| 2 | `instrument_expired_or_blocked` | `card_expired`, `debit_instrument_blocked` | source `issuer_bank` | Partially (card decline test numbers) | No retry. `payment_link` + `nudge` once, then escalate |
| 3 | `authentication_failed` | `authentication_failed`, `incorrect_otp` | step `payment_authentication`, source `customer` | **Yes (card 4100 2800 0000 0009)** | `nudge` (re-auth requires customer action — RBI AFA), 1 retry, then escalate |
| 4 | `bank_or_gateway_error` | `bank_technical_error`, `gateway_technical_error`, `payment_timed_out` | source `gateway`/`bank`/`internal`, step `payment_authorization` | **Yes (card timeout / gateway-error test numbers)** | `charge_invoice` after short cooldown, ≤3 attempts, then escalate |
| 5 | `mandate_not_active` | `mandate_not_active`, `payment_mandate_not_active`, `funds_blocked_by_mandate`, `mandate_creation_*`; token `status` ∈ {`paused`, `cancelled`, `rejected`} | `token.paused` (UPI), `token.cancelled`, `token.rejected` webhooks | **Documented, not manufacturable in test mode** — exercised via recorded/synthetic payloads only, labelled as such | No charge. `payment_link` + `nudge` to re-approve mandate, then escalate |
| 6 | `limit_exceeded` | `transaction_limit_exceeded` | source `issuer_bank`/`customer_psp` | Synthetic only | `payment_link` (different instrument) + `nudge`, then escalate |
| 7 | `unknown` | generic `payment_failed`, `null` fields, or LLM abstain | — | **This is what UPI `failure@razorpay` and dashboard "Charge this now" produce** | `escalate` always |

Hard stops (§FR-3.3) override every row.

**Honesty note for README/video:** card test numbers exercise real reason codes end-to-end; UPI and dashboard-simulated failures exercise the state machine (pending → halted → recovery) with `unknown` cause. Cause 5 is grounded in documented fields but its webhooks' test-mode firing is not documented; it is demonstrated from recorded/synthetic payloads.

## 7. Non-functional requirements

| NFR | Requirement |
|---|---|
| Determinism | Seeded batch; cached LLM responses; identical report on rerun |
| Safety | No LLM code path can reach a money API; gate enforces amount == invoice amount; violations counted and must be 0 |
| Secrets | `.env` only (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`); `.env.example` committed |
| Runnability | Clean clone → one command → report, tested on a fresh directory before submission |
| Observability | Every decision traceable from report → audit seq → payload |
| Stack | Python 3.11+, FastAPI (webhook receiver), `razorpay` SDK, `anthropic` SDK, SQLite for event/idempotency store, JSONL audit, YAML policy, pytest |

## 8. Assumptions and open questions

| Item | Handling |
|---|---|
| Test-mode API keys | Provided by the user via `.env` (not yet present at time of writing) |
| Public webhook URL | ngrok or equivalent; if unavailable, FR-1.5 fixture mode carries the demo and this is recorded in `FAILURES.md` |
| Token webhooks in test mode | Not documented → cause 5 demonstrated from recorded/synthetic payloads, labelled |
| UPI reason codes in test mode | Not available → UPI scenarios land in `unknown` → escalate; stated in the report |
| Card-token subsequent debits | Test docs say valid only within 3 days of token creation — irrelevant at 24-h horizon |

## 9. Acceptance criteria (Stage 1)

- AC-1 `make demo` on a clean clone produces `report.md` with every FR-6.4 metric populated.
- AC-2 `policy_violations == 0` and `double_charges == 0` with ≥5 duplicate deliveries replayed.
- AC-3 Every non-`unknown` classification in the report cites the documented `error_reason` it mapped from.
- AC-4 At least one scenario ends in LLM abstain → escalate, visible in the report and the video.
- AC-5 `verify_audit.py` passes on the batch's audit log; tampering one byte makes it fail.
- AC-6 README first paragraph contains none of: taxonomy, dunning, AFA, NSF, hash-chained, authoriser.

## Amendment A — from `docs/idea-evaluation.md` (2026-09-04, after Gate I-1)

Rubric score as specified: 43/60 (target ≥48). These additions lift Demo-ability, Feasibility and Scalability honestly; Novelty stays capped at 7 by rule.

| Ref | NEW requirement | Lifts |
|---|---|---|
| FR-8.2a | The video includes a **live** test-mode failure: a subscription failed from the Razorpay dashboard, its `subscription.halted` webhook arriving, classified, gated, acted on — then the same event redelivered and rejected. The fixture batch still produces the metrics. | Demo-ability |
| FR-6.6 | `rebound report --html` renders `metrics.json` into **one self-contained static HTML file** (per-cause allow/block/escalate bars, audit chain view, exceptions list, "where AI was / wasn't used" panel). No server, no framework. | Demo-ability |
| FR-6.1a | **Real-payload floor ≥ 10**, covering the documented card test numbers for insufficient funds, expired/declined, authentication failed, timeout, gateway error — so causes 1–4 are exercised end-to-end on real Razorpay responses. Every scenario is tagged `recorded` or `synthetic` in the report. | Feasibility |
| NFR-Scale | `EventStore` and `Dispatcher` are explicit interfaces; the SQLite / in-process implementations are the only ones built. README documents the swap path (Postgres; queue workers) and why `event_id` dedupe makes parallel workers safe. | Scalability |
| FR-8.1a | README states the per-merchant impact model: for N subscriptions at the industry 7.9% failure rate, the expected monthly `halted` count and its split into auto-recoverable / nudge-only / escalate under the stated decline-mix. No ₹ claim. | Impact (defensibility) |

Non-goals in §3 are unchanged: still no UI *application*, no real messaging, no Hinglish/voice.

---
*Approval gate for this stage: `audit.md` → Gate I-1 (Continue). Amendment A recorded at D-5. Next: `02-application-design.md`.*
