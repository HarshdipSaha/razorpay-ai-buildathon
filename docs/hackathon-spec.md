# Razorpay AI Buildathon — Hackathon Spec

Source: https://razorpay.com/buildathon/ (single-page site, captured 2026-09-04 via Playwright) and the application form at https://forms.gle/d9r2gvxp8cmoZhon9 (Google Form titled "Razorpay AI Builder Internship 2026", created inside Razorpay).

Tagline: **"Build. Show. Get hired."** / "Your code speaks louder than your resume."

---

## 1. What it is

Not a prize hackathon — it is a **hiring funnel**. A student-only program to discover and hire Razorpay's next generation of **AI Builder Interns**. There is no resume screening and no long application. The build *is* the application.

Four steps:
1. Pick a track.
2. Build something real.
3. Show your work — a **public GitHub repo**, a **5-minute pitch video**, and the **architecture**.
4. If it has signal, they call you in.

## 2. Key dates and constraints

| Item | Value |
|---|---|
| **Applications close** | **5 September** (footer: "Applications close 5 September") — i.e. tomorrow relative to 2026-09-04 |
| Eligibility | Students only. Form's Graduation Year dropdown offers **only 2027, 2028, 2029** — 2026 (or earlier) grads cannot select a valid year |
| Internship start | In-person, **Bangalore, from September** |
| Duration | 6 or 12 months — your choice |
| Stipend | **₹75,000 / month** |
| Process after shortlist | Straight to a **panel**. No aptitude test. No group discussion |
| Submission finality | Form has a "Final Submission Confirmation" checkbox: no further edits after submitting |

## 3. Tracks (five ways in)

The form's dropdown labels them: *Track 1: AI Growth & Agentic Commerce*, *Track 2: AI Risk Manager*, *Track 3: AI Revenue Recovery*, *Track 4: AI Finance Controller*, *Open Track*.

### Track 1 — AI Growth & Agentic Commerce
- **One-liner:** Grow the merchant's revenue, and make them sellable to AI buyers.
- **Brief:** Build an agent that grows revenue for a merchant on **Razorpay test-mode APIs**, or that makes a merchant transactable by an AI buyer end to end.
- **Why now:** NPCI's UAP and the global protocol race (ACP, AP2, x402) make agent-to-agent commerce the open problem of the year; Razorpay's in-app pilots are already live.
- **Example directions:** Conversational in-app checkout · Agent-readable catalog · Upsell & cross-sell agent · Campaign orchestrator.
- **The bar:** Every money action **explainable, bounded and gated**. Show the **audit trail** and **one failure handled gracefully**.

### Track 2 — AI Risk Manager
- **One-liner:** Stop the merchant losing money to fraud, returns and chargebacks.
- **Brief:** Build a working detector, verifier or auto-responder for **one class of loss**, with **measured precision and recall on a held-out test set**.
- **Why now:** AI-enabled fraud is hitting Indian BFSI while returns and chargebacks quietly eat margin. This track surfaces risk/ML-minded builders the others miss.
- **Example directions:** Chargeback evidence responder · Return-risk scorer · Fraud-spike detector · Abuse-ring sentinel.
- **The bar:** **Honest metrics including false-positive cost.** **Strictly defense-only — anything offense-capable is disqualified.**

### Track 3 — AI Revenue Recovery
- **One-liner:** Find revenue that's slipping away and win it back.
- **Brief:** Build an agent that **detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow** — from payment failures and checkout abandonment to overdue receivables.
- **Why now:** Revenue loss rarely happens in one clean step: a payment degrades, a checkout is abandoned, a subscription fails, an invoice goes overdue. AI can now close the loop from detect → diagnose → choose intervention → recover.
- **Example directions:** Payment degradation → root cause → recovery action · Checkout drop-off recovery · Failed-subscription recovery · B2B receivables chaser · Mandate retry sequencer · Hinglish voice recovery · Promise-to-pay tracker.
- **The bar:** Don't just identify the problem. Show **measured money recovered across a batch**, with **compliant escalation, stopping rules, and an audit trail**.

### Track 4 — AI Finance Controller
- **One-liner:** Run the books and the cash position.
- **Brief:** Build an agent that **closes one finance-ops loop across a 50+ record batch of synthetic data**, reporting its **match rate** and the **exceptions it could not resolve**.
- **Why now:** The 2026 builder consensus: verification capacity, not generation speed, is the bottleneck. Reconciliation, settlement and forecasting are still done by hand.
- **Example directions:** Multi-source reconciliation · Settlement Q&A agent · Forward cash forecaster · Tax-line matcher.
- **The bar:** **Throughput + measured accuracy + an honest exception list.** "One cherry-picked match proves nothing."

### Track 5 — Open Track
- **One-liner:** Build what you believe should exist.
- **Brief:** Idea doesn't fit the above? Pick a real problem, use AI meaningfully, show something that works. Any domain, workflow, or user is fair game.
- **Why now:** The best ideas don't always fit a predefined category.
- **Example directions:** Surprise us · Solve a problem you deeply understand · Build something we haven't thought of.
- **The bar:** "Open doesn't mean easier." Real problem, working product, meaningful use of AI, evidence it creates value. **Same bar for execution, reliability, and depth.**

## 4. How submissions are evaluated

"We read the work, not the resume. We look at how you think, build and solve problems."

| Criterion | What they ask |
|---|---|
| **Problem taste** | Did you pick something that actually matters? |
| **Build quality** | Does it run, is it structured, would you trust it? |
| **AI judgment** | The right tool in the right place — **and where you chose *not* to use one**. |
| **Failure recovery** | What broke, and what you did about it. |

Explicit hint from the site: *"We still take the resume. We just don't screen on it. **The last one [what broke, and how you got out] is the one we read first.**"*

## 5. The application form (12 answers, ~15 minutes)

Multi-page Google Form. Pages observed:

**Page 1 — About you**
1. Email (required)
2. Full Name
3. College Name
4. Graduation Year — dropdown: 2027 / 2028 / 2029
5. In-person Internship availability starting September — Yes / No

**Page 2 — Internship Details**
6. Preferred Internship Duration — 6-Month Internship / 12-Month Internship

**Page 3 — Track Selection & the build** (per the form as seen by the applicant)
7. Selected Track — dropdown: Track 1 / Track 2 / Track 3 / Track 4 / Open Track
8. Project Name / Title
9. Project Objectives — "What does it solve?"
10. GitHub Repository URL — must be **public**
11. 5-min Pitch Video Link — unlisted is fine
12. Build Challenges & Technical Obstacles — "What issues did you face while building, and how did you solve them?"
13. Final Submission Confirmation — checkbox: "I confirm that this is my official final project submission. I understand that no further changes or edits can be made after submitting."

The site also lists a **Resume file** upload among the 12 items (likely on a page requiring Google sign-in; not reached).

## 6. What a winning submission needs (derived)

Common thread across every track's "bar":
- **Measured, honest numbers** on a batch — precision/recall, match rate, money recovered — never a single demo happy path.
- **Bounded, gated money actions** with an **audit trail**.
- **Explicit failure handling**: stopping rules, escalation, exceptions list, at least one failure shown recovered gracefully.
- **Synthetic / test-mode data**: Razorpay test-mode APIs (Track 1), held-out test set (Track 2), 50+ synthetic records (Track 4).
- **Defense-only** posture — anything offense-capable in risk work is disqualifying.
- **AI judgment** — be able to say where an LLM was the wrong tool and you used deterministic code instead.

Deliverables checklist:
- [ ] Public GitHub repo with README covering architecture
- [ ] 5-minute pitch video (unlisted YouTube/Loom OK) — show it running, show the metrics, show the failure and the recovery
- [ ] Written "what broke and how you got out" narrative — this is read first
- [ ] Resume file (not screened on, but collected)
- [ ] Submit before **5 September** — the form is one-shot, no edits after

## 7. Notes / open questions
- Time zone for the 5 September close is not stated; assume IST end-of-day at the latest, aim earlier.
- No team-size rule is stated anywhere; the form collects a single applicant's identity, implying **solo submissions**.
- No judging rubric weights, prize money, or leaderboard — the "prize" is the internship interview.
- Page footer: "Copyright © Razorpay · Built during the night shift."
