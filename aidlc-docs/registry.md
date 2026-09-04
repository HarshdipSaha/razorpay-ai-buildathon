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

Full construction plan (26 tasks, TDD, reviewed 5 rounds, approved): `docs/superpowers/plans/2026-09-04-rebound-recovery-agent.md`. **Work is paused here per user instruction — the plan is the deliverable; no construction has started.**

| # | Ref | Type | State | Requirements delta | Notes |
|---|---|---|---|---|---|
| 001 | `scaffold-ingest-audit` | feature | plan approved, **not started** | `efforts/001-scaffold-ingest-audit/requirements-delta.md` | plan doc Tasks 1-4, 12-14, 13a, 19-20 |
| 002 | `taxonomy-classifier` | feature | plan approved, **not started** | — (plan doc Tasks 5-7) | depends on 001; parallel with 003 |
| 003 | `policy-gate-actions` | feature | plan approved, **not started** | — (plan doc Tasks 8-11) | depends on 001; parallel with 002 |
| 004 | `sim-batch-report` | feature | plan approved, **not started** | — (plan doc Tasks 15-18) | depends on 002, 003 |
| 005 | `hour-zero-capture` | feature | plan approved, **blocked** — waiting on `.env` test keys from user | — (plan doc Tasks 21-22) | independent of 001-004; load-bearing per council verdict |
| 006 | `deliverables` | feature | plan approved, **not started** | — (plan doc Tasks 23-25) | depends on 004, 005 |
