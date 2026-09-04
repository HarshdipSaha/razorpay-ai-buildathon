# Failures and recoveries — kept live

Format per entry: **What broke** / **How it was found** / **What changed**.

---

## 1. `rebound demo` crashed on Windows with `UnicodeEncodeError`

**What broke:** The first real run of `python -m rebound.cli demo` crashed with
`UnicodeEncodeError: 'charmap' codec can't encode character '→'` — Windows
consoles and `Path.write_text()` default to the `cp1252` codepage, which can't
represent the `→` and `·` characters the report renderer uses.

**How it was found:** Ran the command for real immediately after the code was
written, rather than assuming it worked because the unit tests passed — the tests
never write the Markdown report to a real file or print it to a real console.

**What changed:** Forced UTF-8 explicitly at every text I/O boundary: `encoding="utf-8"`
on every `write_text`/`read_text` call in `cli.py`, and `sys.stdout.reconfigure(encoding="utf-8")`
at the top of `main()` (wrapped in `try/except` since not every stream supports
`reconfigure`). Left the report content itself untouched — the fix belongs at the
I/O boundary, not by stripping useful characters out of the output.

## 2. `Executor` originally required a real Razorpay client for the batch/demo path

**What broke:** Nothing crashed — this was caught during design, not at runtime — but
the original plan's `cmd_demo` built its `PipelineContext` the same way `cmd_serve`
does: a real `razorpay.Client` if `RAZORPAY_KEY_ID` is set, otherwise `None`. Since
`Executor.execute()` unconditionally calls `self.client.invoice.issue(...)` or
`self.client.payment_link.create(...)`, running `demo` without real Razorpay
credentials would have crashed with `AttributeError: 'NoneType' object has no
attribute 'invoice'` on the very first allowed action.

**How it was found:** Reviewing the plan against the stated constraint that the
core judged deliverable (batch metrics, audit trail, HTML report) must run without
the builder's own Razorpay login — a real API client contradicts that by design,
since the batch's subscriptions and payments are synthetic/fixture data, not live
Razorpay entities that could actually be charged.

**What changed:** Added `rebound/sim/fake_razorpay.py` — an in-memory
`SimulatedRazorpayClient` implementing the same `invoice.issue` / `payment_link.create`
surface the real SDK exposes, deterministically succeeding with zero network I/O.
`cmd_demo` now always uses it (`simulate_razorpay=True`); `cmd_serve` (live webhooks)
is the only path that would use a real client, and that path was never exercised in
this run since it requires the user's own Razorpay test-mode login, which was
explicitly out of scope here.

## 3. `policy.yaml`'s `max_attempts_by_cause: 0` would have silently broken three causes

**What broke:** Nothing crashed — this was caught during the plan's review loop
(round 4), before any code existed. `max_attempts_by_cause: 0` for
`instrument_expired_or_blocked`, `mandate_not_active`, and `limit_exceeded` combined
with the planner always proposing `attempt_no = state.attempt_no + 1` (so the very
first attempt is already `attempt_no == 1`) meant every occurrence of those three
causes would hit `hard_stop.attempts_exhausted` before the gate ever reached their
own `causes.*` row — silently escalating ~25% of the batch regardless of what their
policy row actually permitted. A pre-existing test for `mandate_not_active` passed
the whole time, but only because it happened to assert `verdict.decision != "allow"`,
which is true whether the block comes from the (wrong) attempts-exhausted rule or the
(intended) cause-specific behaviour.

**How it was found:** Traced the gate's evaluation order by hand against the stated
requirement ("no retry... once, then escalate") during a plan-review pass, rather
than trusting that a green test suite meant the logic was right.

**What changed:** Changed the three values to `1`. Added two regression tests
(`test_mandate_not_active_allows_payment_link_on_first_attempt`,
`test_instrument_expired_allows_payment_link_on_first_attempt_only`) that assert the
*correct* action is allowed on attempt 1 and escalated on attempt 2 — not just that
something other than `charge_invoice` happens.

---
*(No live Razorpay webhook was exercised in this build — see the README's "Scope decision" for why, and `docs/hackathon-spec.md` / `docs/idea-evaluation.md` for how the taxonomy is still grounded in Razorpay's documented fields rather than invented labels.)*
