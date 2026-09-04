# Research Synthesis — market + academic grounding for idea selection

Date: 2026-09-04. Produced by two parallel research subagents (market/API scan; academic scan via arXiv), then synthesised. Feeds AI-DLC Inception Stage 1.

## 1. Market scan per track

| Track | Pain (evidence) | Incumbents | Gap | Razorpay test-mode fit |
|---|---|---|---|---|
| **1 Agentic Commerce** | Four competing agent-payment standards (ACP, AP2, x402, UCP); x402 alone 69k agents / 165M txns by Apr 2026 | Protocol authors (OpenAI/Stripe, Google, Coinbase). Razorpay already runs live agentic-UPI pilots (Zomato/Swiggy/Zepto). **NPCI UAP launches 9–11 Sept — after the deadline.** | AP2-style mandate → Razorpay Order → gated Payment Link with spend cap | Orders/Payments/Payment Links work with test keys; `success@razorpay` / `failure@razorpay` UPI IDs are deterministic. Novelty is protocol glue; hard to quantify. |
| **2 Risk Manager** | Friendly fraud ≈ 75% of disputes; CNP fraud → $28.1B by 2026; merchants lose ~3% revenue to fraud | **Heavily funded**: Chargeflow ($35M Series A Nov 2025), Justt (Forbes Fintech 50) | Return-abuse / refund-ring scoring for COD-heavy Indian D2C | **Weakest.** Disputes API exists but **no documented way to create a dispute in test mode** → zero data to run against. |
| **3 Revenue Recovery** | Failed subscription payments cost **$129B in 2025**; involuntary churn = 20–40% of subscription loss and mostly recoverable; **median recovery 47.6%**, top performers 70–85%; avg txn failure 7.9% | Stripe Smart Retries, Chargebee/Recurly dunning, Slicker, Baremetrics Recover — all card/US-centric. **Nothing for Razorpay `halted` subscriptions or UPI AutoPay / e-mandate failures in India.** | Razorpay's retry schedule is **fixed and merchant-uncontrollable** (T+1/T+2/T+3 → `subscription.halted`; halted invoices "you will have to charge manually"). An agent that takes `subscription.halted`, diagnoses cause, picks a bounded intervention, and stops/escalates under rules is an unfilled hole. | **Strongest.** Dashboard "Charge this now" lets you choose success/failure per charge; failing 4× fires `subscription.pending` → `subscription.halted` webhooks in test; Invoices API charges halted invoices; Payment Links for recovery. A 50+ batch with honest ₹ recovered is genuinely measurable. |
| **4 Finance Controller** | Reconciliation still manual; market expects 90%+ auto-match with explained exceptions | **Mature & AI-native**: BlackLine (Verity AI), Trintech, FloQast, HighRadius, Bluecopa, ReconArt | Razorpay settlement ↔ bank ↔ GST ledger three-way match with fee/TDS/UTR explanation | Settlements + Settlement Recon APIs exist, but test-mode recon data is thin — mostly synthetic. Reads as "smaller BlackLine." |

Sources: [ATXP protocol comparison](https://atxp.ai/blog/agent-payment-protocols-compared/) · [Chargeflow stats](https://www.chargeflow.io/blog/chargeback-statistics-trends-costs-solutions) · [Recurly failed-payment data](https://recurly.com/blog/failed-payment-recovery-data-based-strategy/) · [RetentionLens involuntary churn](https://retentionlens.com/state-of-involuntary-churn) · [Slicker 2025 benchmarks](https://www.slickerhq.com/resources/blog/2025-failed-payment-benchmarks-ai-beats-industry-averages) · [Razorpay Payment Retries](https://razorpay.com/docs/payments/subscriptions/payment-retries/) · [Razorpay Test Subscriptions](https://razorpay.com/docs/subscriptions/test-guide/) · [Razorpay Settlements APIs](https://razorpay.com/docs/payments/settlements/apis/)

## 2. Academic scan (arXiv, verified against listings)

| Paper | WHY | HOW | WHAT — and what we take from it |
|---|---|---|---|
| **A Formal Analysis of Agent Payment Protocols** — [2609.00060](https://arxiv.org/abs/2609.00060) | x402/MPP/ACP/AP2 adopted with no formal verification; authorization drifts between intent → mandate → settlement | Tamarin models of all four; authorization-consistency checks | 40 undocumented issues → 18 principles. **Authorization must be re-checked at every stage, not assumed from an upstream signature.** |
| **Beyond the Mandate: Security Analysis of AP2** — [2608.23858](https://arxiv.org/abs/2608.23858) | Is a signed mandate proof of intent? | 48 threats / 5 families; PoC exploits; scanner | A valid signature ≠ intent. **Bounds (amount, count, time, counterparty) must be enforced at execution time by something other than the agent.** |
| **Before the Tool Call: Deterministic Pre-Action Authorization (Open Agent Passport)** — [2603.20953](https://arxiv.org/abs/2603.20953) | Neither the model nor the app layer is a security-grade authorizer | Intercept every tool call; evaluate declarative policy; emit signed audit record | Social-engineering success 74.6% (permissive) → **0% / 879 attempts (restrictive)**; 53 ms median overhead. **The gate is a policy engine with a signed audit trail.** |
| **DeepScrub: Traceable LLM Reasoning for Fake-Order Fraud** — [2607.23075](https://arxiv.org/abs/2607.23075) | Reviewers need a decision *plus* a reviewable trace | RL-tuned LLM (requires training — take the pattern, not the method) | 91.8% P / 88.5% R live; 94% less manual review. **Verdict + natural-language trace.** |
| **FinBalance: Multi-Document Reconciliation Benchmark** — [2606.15949](https://arxiv.org/abs/2606.15949) | Real finance work is reconciling raw documents, not prepared statements | Deterministic generator, 8 industries × 5 levels, 23 inconsistency codes | Best LLM only **46% exact accuracy**; 26–41 pp gaps. **LLMs cannot be trusted with aggregation/arithmetic.** |
| **MACS: Hybrid Multi-Agent Conversational E-Commerce** — [2608.14068](https://arxiv.org/abs/2608.14068) | Pure-LLM agents drift on hard constraints | LLM handles language; deterministic agents own every correctness-critical op | 87.1% accuracy, **zero constraint drift**. "LLM speaks, code decides." |

Adjacent: [2607.19266](https://arxiv.org/abs/2607.19266) *Toward Auditable Fraud Detection*; [2411.13017](https://arxiv.org/abs/2411.13017) GenAI root-cause analysis for recurring failures in banking.

**Gap:** zero arXiv papers on dunning / failed-payment recovery / involuntary churn. All evidence is industry: soft declines are 70–90% of CNP failures; decline-code-specific retry timing; 3–5 attempts over 10–14 days; 47.6% avg recovery, 70%+ with ML. **Track 3 is academically unclaimed.**

## 3. Cross-source synthesis

**Common thread:** every strong result separates a *probabilistic* component (classify, explain, draft) from a *deterministic* component that decides, bounds, and records.

**Implementable in ~24h without training:**
- Root-cause taxonomy as a deterministic state machine: failure/decline code → {NSF-soft, expired/hard, issuer-do-not-honor, network-timeout, **e-mandate AFA/OTP re-auth failure**, **UPI AutoPay mandate paused / limit exceeded**, customer-cancelled}.
- Policy table per cause: permitted interventions, max retries, contact caps, cooldowns, hard stops (hard decline, dispute opened, opt-out, regulatory cap). ~150 lines. This *is* the pre-action gate.
- LLM only where language is the problem: classify ambiguous free-text failure descriptions **with confidence and an abstain path**; draft Hinglish/English re-auth nudges. Never chooses the action, never computes money.
- Append-only hash-chained audit log: proposed action → policy verdict → executed/blocked → outcome.
- Metrics on a synthetic batch: classifier P/R on held-out labels; recovery rate and ₹ recovered per cause; false-escalation count; exceptions list.

**Most novel combination not a product today:** **root-cause-typed recovery under pre-action authorization.** Incumbents optimise *timing* on card decline codes; none model RBI e-mandate AFA re-authorization or UPI AutoPay mandate states as first-class causes, and none wrap recovery actions in an OAP-style authorizer with a signed audit trail.
