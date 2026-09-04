# Effort 001 — scaffold-ingest-audit

**Type:** feature · **Depth:** standard · **Opened:** 2026-09-04
**State:** `awaiting-approval` (Gate E-001–004)

## Baseline reference
`aidlc-docs/inception/02-application-design.md` §2 (components), §5 D3–D6, §8 (layout), §9 row 001.

## Units

| Unit | Files | Satisfies | State |
|---|---|---|---|
| U1 Project skeleton | `pyproject.toml`, `Makefile`, `.env.example`, `rebound/__init__.py`, `rebound/cli.py`, `rebound/models.py` | FR-8.1 (one command), NFR-Stack | pending |
| U2 Clock | `rebound/sim/clock.py` (`Clock` protocol, `RealClock`, `SimClock`) | FR-4f, D5 | pending |
| U3 Audit log | `rebound/audit/log.py` (append, hash chain, verify) | FR-5.1–5.3, D4 | pending |
| U4 Event store | `rebound/ingest/store.py` (SQLite, `INSERT OR IGNORE`, duplicate detection) | FR-1.3, D3 | pending |
| U5 Pipeline entry | `rebound/pipeline.py` — `process_event(event, ctx)` shared by live + fixture paths; stubs for classify/plan/gate that 002/003 fill in | FR-1.5, D6 | pending |
| U6 Webhook receiver | `rebound/ingest/webhook.py` (FastAPI, HMAC verify, 200 fast, hand-off) | FR-1.1, 1.2, 1.4 | pending |
| U7 Fixture replayer | `rebound/ingest/fixtures.py` + `fixtures/recorded/README.md` | FR-1.5 | pending |
| U8 Tests | `tests/test_audit_chain.py`, `tests/test_store_dedupe.py`, `tests/test_webhook_signature.py`, `tests/test_clock.py` | NFR-Runnability | pending |

## Definition of done
- `pip install -e .` then `pytest` green on a clean clone.
- `rebound verify-audit` fails when one byte of the log is altered (AC-5).
- Replaying the same `event_id` twice yields exactly one processed event and one `duplicate_rejected` audit line (AC-2 precondition).
- Webhook with a bad signature → 400 + `signature_rejected` audit line.

## Log
| When | Note |
|---|---|
| 2026-09-04 | Opened after Gate I-2. Awaiting Gate E-001–004. |
