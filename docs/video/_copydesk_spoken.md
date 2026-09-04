# Spoken narration — final, post-review (order = play order)
Pause markers: `[pause]` ≈ 350ms, `[long pause]` ≈ 700ms, converted to SSML `<break>` by `synth_narration.ps1`. Voice: Microsoft Zira (offline SAPI), rate 1, no prosody slowdown. (A first pass at rate -1 with -8% prosody ran 5:22, over the brief's 5-minute limit; corrected to 3:48.)
Review gate: prose-review found 0 hard fails; craft-review's three findings applied (coined 'the wallet gate', used exactly twice; broke the identical setup→pause→punchline shape across scenes 6-7-8 by folding scene 7's line into one thought; thinned pauses in scenes 4, 7, 9 so the heavy pausing in 5 and 8 reads as deliberate). Prose advisory applied: varied scene 2's opener away from the repeated 'Here's X' device.

## 10_whatbroke (cold open, plays first)
So, [pause] I almost shipped a bug. [pause] It would've quietly escalated 15 of 60 cases, [pause] for no reason at all. [long pause] I caught it by reading the gate's logic by hand. [pause] Before I'd written a single line of code. [long pause] Two smaller ones slipped through too. [pause] Windows choked on a character my own report tried to print. [pause] And an early version would've needed a real Razorpay login, [pause] just to run offline. [long pause] So here's what I built, [pause] to make sure none of that ships silently again.

## 01_title
Okay, so. [pause] A Razorpay subscription fails to charge. [pause] Four times in a row. [pause] And Razorpay just [pause] stops. [long pause] The subscription goes to halted, [pause] and the merchant gets a note. [pause] Charge this one by hand. [long pause] I built Rebound to pick up right there. [pause] It figures out why the payment failed, [pause] decides what to do about it, [pause] and writes down every single step, [pause] so you can check its work.

## 02_architecture
Picture a payment failing. [pause] A rule checks Razorpay's own error fields to find the cause. [long pause] If that's ambiguous, [pause] an LLM takes a pass. [pause] But it's allowed to say it doesn't know. [long pause] Then the wallet gate, [pause] just plain rules, [pause] decides whether the action actually happens. [long pause] The model deals in words. [pause] The gate deals in wallets. [pause] And the two never swap jobs.

## 03_tests
Before I show you anything else, [pause] here's proof it actually runs. [long pause] 54 tests. [pause] On this machine. [pause] Right now.

## 04_demo_run
60 scenarios, seeded so you can reproduce this exact run yourself. [long pause] 0 policy violations. [pause] 0 double charges. [long pause] And the 4 cases that came back ambiguous? [pause] They got escalated to a person instead of guessed at.

## 05_metrics
This is the report the batch writes. [long pause] I redesigned it to read like a case file. [pause] There's a case number, [pause] 7 exhibits, [pause] and a ledger that lists every decision, in order. [long pause] Every number on this page is one of two things. [pause] Either an invariant that has to be zero, [pause] or a citation, [pause] straight back to the exact Razorpay field it came from.

## 06_idempotency
Razorpay retries webhooks. [pause] So 5 of the 60 scenarios get their failure delivered twice, [pause] on purpose. [long pause] The second delivery never even reaches the classifier. [pause] The dedupe check runs first, [pause] and it's just a database constraint on the event ID. [long pause] 5 duplicates in. [pause] 0 double charges out.

## 07_abstain
One of the held-out cases was genuinely unclear, so the classifier passed on it. [pause] It came back as unknown, and the gate escalates unknown to a person every single time, [pause] because it doesn't guess with someone's money.

## 08_tamper
Verify passes clean. [long pause] Then I open the log file, [pause] and I change one byte. [pause] By hand. [long pause] Run verify again, [pause] and it fails on the exact record I touched. [long pause] Every entry's hash depends on the one before it. [pause] So there's nowhere to hide a change.

## 09_scope
You don't need a Razorpay account to run any of this. [long pause] The causes come from Razorpay's own published error fields, cited right there in the code, and the batch runs against a simulated client I wrote myself, so none of it touches a real network. [long pause] Drop the Anthropic key and the classifier just abstains more, [pause] which the design already treats as a perfectly fine outcome.

## 12_aidlc (plays just before the close; added on user request to explain the build methodology)
One last thing, [pause] about how this was built. [long pause] The whole project ran on AI-DLC. [pause] Inception happens once, requirements then design, [pause] each behind an approval gate. [long pause] Then every change is a numbered effort, [pause] with its own state file and its own requirements-delta. [long pause] Here, that meant 3 gates before any code, 6 efforts to build it, [pause] and a process log that records every tool I used and every course correction along the way. [long pause] The process is as inspectable as the code.

Review gate for this scene: prose-review 0 hard fails (advisories applied: "requirements-delta" for precision; dropped the summarizing "So" from the last line). Craft-review's two edits applied: one pause before the two-item inception list instead of three; the two numbers spoken in one breath. The two reviewers disagreed on the final line (prose: cut as a bow; craft: keep as a genuine destination). Kept, because the next scene's "You can read it" pays it off directly.

## 11_closing
So that's Rebound. [long pause] Words from the model. [pause] Decisions from the wallet gate. [pause] And a ledger that proves which one did what. [long pause] You don't have to trust the demo. [pause] You can read it.
