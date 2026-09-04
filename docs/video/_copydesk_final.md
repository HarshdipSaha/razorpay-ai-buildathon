# Scene 1 — Title

NARRATION: A Razorpay subscription fails to charge four times in a row, and Razorpay just stops. The subscription goes to halted, and the merchant gets a note: charge this one by hand. I built Rebound to pick up right there. It figures out why the payment failed, decides what to do about it, and writes down every step so you can check its work.

ON-SCREEN:
Headline: Rebound
Support: Razorpay gives up after four failed charges. Rebound picks it up from there.

# Scene 2 — Architecture

NARRATION: Here's the shape of it. A payment fails, and a rule checks Razorpay's own error fields to find the cause. If that's ambiguous, an LLM takes a pass, but it's allowed to say it doesn't know. Then a gate, written as plain rules, decides whether the proposed action actually happens. That's the whole rule: the model deals in words, the gate deals in wallets, and the two never swap jobs.

ON-SCREEN:
Headline: Words, not wallets.
Support: classify → gate → act, in that order, every time.

# Scene 3 — Tests

NARRATION: Before I show you anything else, here's proof it runs. Fifty four tests, on this machine, right now.

ON-SCREEN:
Headline: 54 tests. All passing.

# Scene 4 — Batch run

NARRATION: Sixty scenarios, seeded so you can reproduce this exact run. Zero policy violations. Zero double charges. The four cases that came back ambiguous got escalated to a person instead of guessed at.

ON-SCREEN:
Headline: 60 scenarios, one seed, zero shortcuts.
Support: Every number on screen came from this run.

# Scene 5 — The report

NARRATION: This is the report the batch writes. I redesigned it to read like a case file, not a dashboard: a case number, seven exhibits, a ledger that lists every decision in order. Every number on this page is either an invariant that has to be zero, or a citation back to the exact Razorpay field it came from.

ON-SCREEN:
Headline: The report reads like evidence.
Support: Seven exhibits. One ledger. Nothing invented.

# Scene 6 — Idempotency

NARRATION: Razorpay retries webhooks, so five of the sixty scenarios get their failure delivered twice, on purpose. The second delivery never reaches the classifier: the dedupe check runs first, and it's a database constraint on the event ID. Five duplicates in, zero double charges out.

ON-SCREEN:
Headline: I sent the same failure twice, on purpose.
Support: 5 duplicates in. 0 double charges out.

# Scene 7 — Abstain

NARRATION: One of the held-out cases was genuinely unclear, so the classifier passed on it. It came back as unknown, and the gate escalates unknown to a person every time. It doesn't guess with someone's money.

ON-SCREEN:
Headline: The classifier is allowed to say no.
Support: Unknown always escalates. It never guesses.

# Scene 8 — Tamper

NARRATION: Verify passes clean. Then I open the log file and change one byte by hand. Run verify again, and it fails on the exact record I touched. Each entry's hash depends on the one before it, so there's nowhere to hide a change.

ON-SCREEN:
Headline: I broke the log on purpose.
Support: One byte changed. Verify found it instantly.

# Scene 9 — Scope decision

NARRATION: You don't need a Razorpay account to run any of this. The causes come from Razorpay's own published error fields, cited in the code, and the batch runs against a simulated client I wrote myself so none of it touches a real network. Drop the Anthropic key and the classifier just abstains more, which the design already treats as a fine outcome.

ON-SCREEN:
Headline: No login. No API key. That's the point.
Support: The one thing that would need a real login, I skipped, and wrote down why.

# Scene 10 — What broke

NARRATION: Windows choked on a character the report tried to print, which was the easy one. An early version would have needed a real Razorpay login just to run the offline demo, so I built a simulated client instead. The one that mattered was a one-line policy bug: it would have quietly escalated 15 of the 60 scenarios for no reason, and I caught it by reading the gate's logic by hand, before I'd written any code.

ON-SCREEN:
Headline: Three bugs. One of them mattered.
Support: The full list, and the fix, is in FAILURES.md.

# Scene 11 — Closing

NARRATION: That's Rebound: words from the model, decisions from the gate, and a ledger that proves which one did what. You don't have to trust the demo. You can read it.

ON-SCREEN:
Headline: Rebound
Support: github.com/HarshdipSaha/razorpay-ai-buildathon
