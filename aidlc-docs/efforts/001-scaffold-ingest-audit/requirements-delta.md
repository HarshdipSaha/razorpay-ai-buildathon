# Effort 001 — requirements delta vs baseline

Baseline: `inception/01-requirements.md`. This effort implements existing requirements; it introduces **no NEW** functional requirements. Deltas are clarifications discovered while decomposing.

## CHANGED / clarified

| Ref | Baseline says | Clarification for construction |
|---|---|---|
| FR-1.3 | dedupe on `x-razorpay-event-id` | Header name normalised to lower-case at the ASGI layer; the fixture replayer supplies `event_id` in the fixture envelope so both paths hit the same `store.insert_if_new()` |
| FR-1.4 | respond within 5 s | Receiver stores + acknowledges, then processes synchronously in-process for this build (no queue) — a 60-scenario batch does not need a worker. Recorded as a deliberate simplification. |
| FR-5.1 | `hash = sha256(prev_hash + canonical_json(record_without_hash))` | Canonical JSON = `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`; genesis `prev_hash = "0"*64` |
| FR-1.5 | replay/fixture mode | Fixture envelope: `{"event_id": str, "event": str, "payload": {...razorpay webhook body...}}`; live path builds the same envelope from headers + body |

## NEW (non-functional only)

| Ref | Requirement |
|---|---|
| NFR-Layout | Package name `rebound`; single `pyproject.toml`; `Makefile` targets `install`, `test`, `demo`, `serve`, `verify-audit` |
| NFR-Stubs | `pipeline.process_event` calls `classify()`, `plan()`, `gate()` through a `Context` object so Efforts 002/003 can plug in without touching 001's files (disjoint ownership for parallel subagents) |

## Out of scope for this effort
Classifier logic (002), policy/gate/executor (003), scenarios/batch/report (004), any Razorpay API call (003/005).
