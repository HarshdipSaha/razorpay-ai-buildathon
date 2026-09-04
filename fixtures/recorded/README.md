# Recorded fixtures

Real Razorpay test-mode webhook/payment payloads would go here, captured via a live
test-mode account. **This build deliberately skips that step** — it requires the
user's own Razorpay dashboard login, which was explicitly out of scope for this run
(see `FAILURES.md` and the README's "Scope decision" note).

Each cause's mapping is instead grounded directly in Razorpay's *documented* API
reference (`rebound/classify/taxonomy.py` cites the doc URL per cause), and the
60-scenario batch is entirely synthetic, generated from those same documented
`error_reason` values — labelled `"synthetic"` in every scenario's tags, never
claimed as `"recorded"`.

If real captures are added later, drop `{"event_id", "event", "payload"}` envelope
JSON files here (see `rebound/ingest/fixtures.py` for the loader) and the scenario
generator (`rebound/sim/scenarios.py`) will pick them up automatically.
