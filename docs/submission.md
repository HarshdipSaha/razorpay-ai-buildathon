# Submission draft — Razorpay AI Buildathon form

Draft answers for `docs/hackathon-spec.md` §5's form fields, so the one-shot form is filled by copy-paste under deadline pressure, not composed live.

## Track Selection
Track 3: AI Revenue Recovery

## Project Name / Title
**Rebound**

## Project Objectives — "What does it solve?"
When a Razorpay recurring subscription payment fails four times in a row, Razorpay's own retry ladder gives up: the subscription moves to `halted` and the merchant is told to charge the customer manually. Rebound picks up exactly there. It reads *why* the payment failed from Razorpay's own documented `error_reason`/`error_source`/`error_step` fields — never invented labels — classifies ambiguous cases with an LLM that can abstain rather than guess, and routes every recovery action through a deterministic policy gate that the AI cannot override. Every decision (classify → propose → authorise → execute or block) is written to a hash-chained, tamper-evident audit log. Run against a seeded 60-scenario batch: 0 policy violations, 0 double charges (even when 5 webhooks are deliberately redelivered), 100% classifier accuracy on a held-out set with a 5% abstain rate, and every non-`unknown` classification cited back to the exact Razorpay field it came from.

## GitHub Repository URL
https://github.com/HarshdipSaha/razorpay-ai-buildathon

## 5-min Pitch Video Link
`docs/rebound-demo.mp4` in the repo (3:48, 1280×720). **Before submitting the form, upload this to YouTube (unlisted) or Loom and paste that link here** — the form needs a URL, not a repo file.

## Build Challenges & Technical Obstacles — "What issues did you face while building, and how did you solve them?"
Three real issues, in the order I hit them (full detail in `FAILURES.md`):

1. **`rebound demo` crashed on Windows with `UnicodeEncodeError`.** Windows consoles and file writes default to the `cp1252` codepage, which can't encode the `→`/`·` characters in the report. Fixed by forcing UTF-8 at every text I/O boundary (`encoding="utf-8"` on every file read/write, `sys.stdout.reconfigure(encoding="utf-8")` on startup) rather than stripping useful characters from the output.

2. **The original design would have required a real Razorpay login even for the offline demo.** The executor unconditionally calls the Razorpay client; without real test-mode keys it would crash with `AttributeError` on the first allowed action. But the batch's subscriptions are entirely synthetic — there's nothing real to charge. I built an in-memory `SimulatedRazorpayClient` that mimics the exact two calls the executor makes, deterministically, with zero network I/O. This is also why the whole submission needs no login or API key at all.

3. **A one-line policy bug would have silently escalated 15 of the 60 scenarios for no reason.** `policy.yaml` capped three causes' `max_attempts_by_cause` at 0, but the planner always proposes attempt 1 as the *first* attempt — so those three causes would hit "attempts exhausted" before their own policy row was ever consulted, silently escalating cases that should have been recovered. This was caught by hand-tracing the gate's evaluation logic during a 5-round plan review, before a single line of code existed — a pre-existing test happened to pass for the wrong reason, which is its own lesson about what a green test suite does and doesn't prove.

The deeper "what broke" is upstream of the code: an LLM council of 5 independent advisors and 5 anonymous peer reviewers converged on a fatal flaw in the *first* version of this idea — the taxonomy's novelty claims (RBI e-mandate AFA failures, UPI AutoPay mandate states) can't actually be manufactured with specific reason codes in Razorpay test mode, which would have made the classifier's precision/recall numbers circular (self-labelled data). I re-designed around that: every cause maps from Razorpay's *documented* field values (cited with doc URLs in `rebound/classify/taxonomy.py`), the report states which causes are test-mode-reproducible on real card numbers versus documented-but-unmanufacturable, and the headline metrics measure the *policy gate's* behaviour (allowed/blocked/escalated per cause) rather than an unverifiable "₹ recovered" figure.

## Final Submission Confirmation
(confirm only when actually submitting — this is a draft)
