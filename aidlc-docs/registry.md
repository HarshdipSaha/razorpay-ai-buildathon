# Effort Registry (derived view)

Rebuilt from `inception/*` and `efforts/*/effort-state.md`. Do not edit by hand — edit the state files and regenerate.

**Last rebuilt:** 2026-09-04

## Inception

| Stage | Artifact | State |
|---|---|---|
| 0 | `inception/00-workspace-detection.md` | **complete** (Gate I-0: Continue) |
| 1 | `inception/01-requirements.md` | **complete** (Gate I-1: Continue) |
| 2 | `inception/02-application-design.md` | **complete** (Gate I-2: Continue) — **baseline established** |

## Efforts

Full construction plan: `docs/superpowers/plans/2026-09-04-rebound-recovery-agent.md`. **User gave full go-ahead (audit.md D-8); construction complete for everything not requiring the builder's own Razorpay login.**

| # | Ref | Type | State | Notes |
|---|---|---|---|---|
| 001 | `scaffold-ingest-audit` | feature | **complete** — 54/54 tests pass | scaffold, models, clock, audit log, event store, fixtures, webhook receiver, adapter, pipeline, CLI all built |
| 002 | `taxonomy-classifier` | feature | **complete** | taxonomy grounded to documented Razorpay fields, rule classifier, LLM residue classifier w/ abstain + cache |
| 003 | `policy-gate-actions` | feature | **complete** | gate, planner, executor, nudge drafter. Fixed `policy.yaml`'s attempts-exhausted bug found in plan review before it could ship |
| 004 | `sim-batch-report` | feature | **complete** | scenario generator, batch runner, Markdown/JSON/HTML report — real run: 0 policy violations, 0 double charges, 100% held-out accuracy |
| 005 | `hour-zero-capture` | feature | **deliberately skipped** | needs the builder's own Razorpay test-mode login — out of scope per explicit "no login/API key" instruction. Documented in README "Scope decision" and `fixtures/recorded/README.md`, not silently dropped |
| 006 | `deliverables` | feature | **README/FAILURES.md/submission.md complete; video in progress** | Simulated-Razorpay-client deviation from the original plan sketch (needed to honor "no login") recorded in `process-log.md` #23 |
