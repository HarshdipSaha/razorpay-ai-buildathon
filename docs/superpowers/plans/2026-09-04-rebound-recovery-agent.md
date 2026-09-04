# Rebound Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Rebound — a Razorpay test-mode agent that, when a recurring subscription payment fails, deterministically diagnoses why from Razorpay's own documented error fields, routes the case through a pre-action policy gate the LLM cannot override, executes a bounded recovery action, and proves every step in a tamper-evident audit log — then reports honest batch metrics for the Razorpay AI Buildathon (Track 3).

**Architecture:** Webhook/fixture ingest → SQLite-deduped event store → rule-first classifier (LLM only on the ambiguous residue, with an abstain path) → deterministic planner → YAML-driven policy gate (the *only* module allowed to call a money API) → executor/nudge-drafter/exceptions → hash-chained audit log → Markdown/JSON/HTML report. A `Clock` abstraction lets a 60-scenario, multi-day batch run in seconds.

**Tech Stack:** Python 3.12 (uv), FastAPI, `razorpay` SDK, `anthropic` SDK, Pydantic v2, PyYAML, SQLite (`sqlite3` stdlib), pytest.

**Specs:**
- `aidlc-docs/inception/01-requirements.md` (incl. Amendment A)
- `aidlc-docs/inception/02-application-design.md`
- `docs/idea-evaluation.md` (S1–S4 sharpening: S1 → Task 25's live demo moment, S2 → Task 18's HTML report, S3 → Task 22's real-payload capture, S4 → Task 23/24's scale-path README section)

---

## Scope note

This is one cohesive subsystem (one pipeline, one repo) — not split into sub-plans. It is organized as AI-DLC Efforts 001–006 (`aidlc-docs/inception/02-application-design.md` §9); each Task below is tagged with the effort it belongs to so the effort-state files can be checked off against it.

## File structure

```
rebound/
  __init__.py          package marker
  models.py             all Pydantic models (§Data model, design doc §3)
  cli.py                 `rebound demo|serve|verify-audit|report`
  sim/
    clock.py             Clock protocol, RealClock, SimClock
    scenarios.py          seeded scenario generator
    batch.py               batch runner
    report.py               metrics.md / metrics.json / metrics.html
  audit/
    log.py                append-only hash-chained JSONL + verify()
  ingest/
    store.py              SQLite event store, dedupe
    webhook.py            FastAPI receiver, HMAC verification
    fixtures.py           fixture envelope loader/replayer
  classify/
    taxonomy.py           Cause enum + documented error_reason → cause map
    rules.py               deterministic classifier
    llm.py                  LLM residue classifier, cache, abstain
  actions/
    planner.py            cause+state → ActionRequest
    executor.py             Razorpay SDK calls (charge_invoice, payment_link)
    nudge.py                 LLM nudge drafting (logged, never sent)
  policy/
    gate.py                policy engine (hard stops + per-cause rows)
    policy.yaml             declarative policy table
  pipeline.py            process_event() shared by webhook + fixture paths

fixtures/
  recorded/              real test-mode captures (Task 22, Effort 005)
  recorded/README.md      what each capture is and how it was made

tests/
  test_clock.py
  test_audit_chain.py
  test_store_dedupe.py
  test_webhook_signature.py
  test_taxonomy_rules.py
  test_llm_classifier.py    (uses a fake LLM client — no network in CI)
  test_gate.py               table-driven allow/block/escalate incl. every hard stop
  test_planner.py
  test_executor.py           uses a fake Razorpay client
  test_scenarios.py          determinism (same seed → same batch)
  test_batch_smoke.py         end-to-end on a tiny scenario set
  test_report.py

FAILURES.md            kept live from Task 1 onward
README.md              final pass is Task 26
.env.example
pyproject.toml
Makefile
```

Rationale: `classify/`, `actions/`, `policy/` are separated because they are owned by different parallel efforts (002 vs 003) and must not share files (design doc §9 — peer-parallel pattern needs disjoint ownership). `models.py` is one file, not split, because every module imports from it and Pydantic models are cheap to hold in context together; if it exceeds ~300 lines during implementation, split by domain (`models_events.py`, `models_policy.py`) at that point, not before (YAGNI).

---

## Task 0: Prerequisites gate (STOP if not met)

**Files:** none — this is a check, not a code task.

- [ ] **Step 1: Verify Razorpay test-mode keys exist**

Run: `test -f "H:/augsepthacks/RAZORPAY AI/.env" && grep -q RAZORPAY_KEY_ID "H:/augsepthacks/RAZORPAY AI/.env" && echo OK || echo MISSING`

Expected: `OK`. If `MISSING`: stop and ask the user for `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` in `.env` (git-ignored). Tasks 1–20 (everything except Tasks 21–22's live work) can proceed without keys since they use fixtures/fakes, but **Task 21** (tunnel + live `serve`) and **Task 22** (Effort 005, the real payload capture that grounds the taxonomy) are fully blocked until keys exist — do not skip either silently; Task 22 in particular is load-bearing per the LLM council verdict (`docs/council-verdict.md`).

- [ ] **Step 2: Verify `ANTHROPIC_API_KEY` is available**

Run: `test -n "$ANTHROPIC_API_KEY" && echo OK || echo "MISSING — LLM classifier/nudge tasks (10, 14) will need it before their integration tests can hit the real API; unit tests use a fake client and do not need it."`

- [ ] **Step 3: Confirm Python toolchain**

Run: `python --version && uv --version`
Expected: Python 3.12.x, uv present (already confirmed: Python 3.12.0, uv 0.9.4).

- [ ] **Step 4: Note the ngrok gap**

`ngrok` is not installed on this machine (confirmed). Task 21 (webhook receiver) and Task 22 (live capture) need a public URL to receive real webhooks. Before Task 21, either install a tunnel (`winget install ngrok.ngrok` or download the zip) or confirm an alternative (Cloudflare Tunnel, `localhost.run` via SSH, or a cloud VM). Record whichever is chosen in `FAILURES.md` as a build-time decision, not a silent assumption.

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `.env.example`
- Create: `rebound/__init__.py`
- Create: `rebound/models.py`
- Create: `FAILURES.md`

**Effort:** 001 (scaffold-ingest-audit), Unit U1

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "rebound"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "pydantic>=2.9",
    "pyyaml>=6.0",
    "razorpay>=1.4",
    "anthropic>=0.40",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.3", "httpx>=0.27"]

[project.scripts]
rebound = "rebound.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["rebound*"]
```

- [ ] **Step 2: Write `Makefile`**

```makefile
.PHONY: install test demo serve verify-audit report

install:
	uv pip install -e ".[dev]"

test:
	pytest -q

demo:
	python -m rebound.cli demo

serve:
	python -m rebound.cli serve

verify-audit:
	python -m rebound.cli verify-audit

report:
	python -m rebound.cli report --html
```

- [ ] **Step 3: Write `.env.example`**

```
RAZORPAY_KEY_ID=rzp_test_xxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

- [ ] **Step 4: Create `rebound/__init__.py`** (empty, package marker)

- [ ] **Step 5: Write `rebound/models.py`** with the Pydantic models from design doc §3:

```python
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel


class Cause(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INSTRUMENT_EXPIRED_OR_BLOCKED = "instrument_expired_or_blocked"
    AUTHENTICATION_FAILED = "authentication_failed"
    BANK_OR_GATEWAY_ERROR = "bank_or_gateway_error"
    MANDATE_NOT_ACTIVE = "mandate_not_active"
    LIMIT_EXCEEDED = "limit_exceeded"
    UNKNOWN = "unknown"


class Action(str, Enum):
    CHARGE_INVOICE = "charge_invoice"
    PAYMENT_LINK = "payment_link"
    NUDGE = "nudge"
    ESCALATE = "escalate"
    NOOP_WAIT = "noop_wait"


Provenance = Literal["rule", "llm", "abstain"]
Decision = Literal["allow", "block", "escalate"]


class Event(BaseModel):
    event_id: str
    event_type: str
    received_at: datetime
    payload: dict


class PaymentFailure(BaseModel):
    payment_id: str
    subscription_id: str
    amount: int  # paise
    method: str
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    token_status: Optional[str] = None


class Classification(BaseModel):
    cause: Cause
    provenance: Provenance
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    mapped_from: Optional[str] = None  # the documented field/value it came from


class SubscriptionState(BaseModel):
    subscription_id: str
    status: str
    attempt_no: int = 0
    consent: bool = True
    dispute_open: bool = False
    token_status: Optional[str] = None
    last_action_at: Optional[float] = None  # sim_time seconds


class ActionRequest(BaseModel):
    subscription_id: str
    cause: Cause
    action: Action
    amount: int
    attempt_no: int
    sim_time: float


class Verdict(BaseModel):
    decision: Decision
    rule_id: str
    reason: str


class Outcome(BaseModel):
    action: Action
    executed: bool
    api_ref: Optional[str] = None
    error: Optional[str] = None


class ProcessResult(BaseModel):
    """What Pipeline.process_failure returns for a non-duplicate event."""
    classification: "Classification"
    outcome: "Outcome"


class AuditRecord(BaseModel):
    seq: int
    ts: datetime
    sim_time: float
    event_id: Optional[str] = None
    subscription_id: Optional[str] = None
    stage: str
    payload: dict
    prev_hash: str
    hash: str


class Scenario(BaseModel):
    id: str
    tags: list[str]  # subset of {heldout, replay_duplicate, recorded, synthetic}
    failure: PaymentFailure
    state: SubscriptionState
    truth_cause: Cause
    truth_action: Optional[Action] = None
```

- [ ] **Step 6: Create `FAILURES.md`** with just a header, to be appended to throughout the build:

```markdown
# Failures and recoveries — kept live

Format per entry: **What broke** / **How it was found** / **What changed**.

---
```

- [ ] **Step 7: Verify the package imports**

Run: `cd "H:/augsepthacks/RAZORPAY AI" && uv pip install -e . && python -c "from rebound.models import Cause, Action, Scenario; print(list(Cause))"`
Expected: prints the 7 `Cause` enum members, no errors.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml Makefile .env.example rebound/__init__.py rebound/models.py FAILURES.md
git commit -m "feat: project scaffold and core data models"
```

---

## Task 2: Simulated clock

**Files:**
- Create: `rebound/sim/__init__.py`
- Create: `rebound/sim/clock.py`
- Test: `tests/test_clock.py`

**Effort:** 001, Unit U2. Satisfies FR-4f.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_clock.py
from rebound.sim.clock import SimClock, RealClock
import time


def test_sim_clock_advances_on_demand():
    clock = SimClock(start=0.0)
    assert clock.now() == 0.0
    clock.advance(3600)
    assert clock.now() == 3600.0


def test_real_clock_uses_wall_time():
    clock = RealClock()
    t0 = clock.now()
    time.sleep(0.01)
    assert clock.now() > t0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_clock.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.sim'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/sim/clock.py
from __future__ import annotations
import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float: ...


class RealClock:
    def now(self) -> float:
        return time.time()


class SimClock:
    def __init__(self, start: float = 0.0) -> None:
        self._t = start

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_clock.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/sim/__init__.py rebound/sim/clock.py tests/test_clock.py
git commit -m "feat: injectable clock (real + simulated)"
```

---

## Task 3: Hash-chained audit log

**Files:**
- Create: `rebound/audit/__init__.py`
- Create: `rebound/audit/log.py`
- Test: `tests/test_audit_chain.py`

**Effort:** 001, Unit U3. Satisfies FR-5.1–5.3, AC-5, design doc D4.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_audit_chain.py
import json
from pathlib import Path
from rebound.audit.log import AuditLog


def test_append_builds_valid_chain(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append(stage="event_received", payload={"a": 1}, sim_time=0.0)
    log.append(stage="classified", payload={"cause": "insufficient_funds"}, sim_time=1.0)
    assert log.verify() is True


def test_tampering_breaks_the_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append(stage="event_received", payload={"a": 1}, sim_time=0.0)
    log.append(stage="classified", payload={"cause": "insufficient_funds"}, sim_time=1.0)

    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["a"] = 999  # tamper
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    log2 = AuditLog(path)
    assert log2.verify() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_audit_chain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.audit'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/audit/log.py
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

GENESIS_HASH = "0" * 64


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.touch(exist_ok=True)

    def _last_hash(self) -> str:
        lines = [l for l in self.path.read_text().splitlines() if l.strip()]
        if not lines:
            return GENESIS_HASH
        return json.loads(lines[-1])["hash"]

    def _next_seq(self) -> int:
        lines = [l for l in self.path.read_text().splitlines() if l.strip()]
        return len(lines)

    def append(self, stage: str, payload: dict, sim_time: float,
               event_id: str | None = None, subscription_id: str | None = None) -> dict:
        prev_hash = self._last_hash()
        record = {
            "seq": self._next_seq(),
            "ts": datetime.now(timezone.utc).isoformat(),
            "sim_time": sim_time,
            "event_id": event_id,
            "subscription_id": subscription_id,
            "stage": stage,
            "payload": payload,
            "prev_hash": prev_hash,
        }
        record["hash"] = hashlib.sha256(
            (prev_hash + _canonical(record)).encode("utf-8")
        ).hexdigest()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(_canonical(record) + "\n")
        return record

    def verify(self) -> bool:
        prev_hash = GENESIS_HASH
        for line in self.path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            claimed_hash = record["hash"]
            check = dict(record)
            del check["hash"]
            if check["prev_hash"] != prev_hash:
                return False
            recomputed = hashlib.sha256(
                (prev_hash + _canonical(check)).encode("utf-8")
            ).hexdigest()
            if recomputed != claimed_hash:
                return False
            prev_hash = claimed_hash
        return True

    def first_break(self) -> int | None:
        """Returns the seq of the first broken record, or None if the chain is valid."""
        prev_hash = GENESIS_HASH
        for i, line in enumerate(self.path.read_text().splitlines()):
            if not line.strip():
                continue
            record = json.loads(line)
            check = dict(record)
            claimed_hash = check.pop("hash")
            if check["prev_hash"] != prev_hash:
                return i
            recomputed = hashlib.sha256(
                (prev_hash + _canonical(check)).encode("utf-8")
            ).hexdigest()
            if recomputed != claimed_hash:
                return i
            prev_hash = claimed_hash
        return None
```

Note: `_canonical(record)` must be computed on the record *without* the `hash` key both when appending and when verifying — the implementation above builds `record` without `hash`, hashes it, then adds `hash` only to the object written to disk (the `_canonical(record)` call in `append` happens before `record["hash"]` is assigned, so this is correct as written — double-check this in Step 4).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_audit_chain.py -v`
Expected: 2 passed. If `test_append_builds_valid_chain` fails, check that `_canonical(record)` in `append()` is called before `record["hash"]` is set (the dict must not contain `hash` yet when hashed).

- [ ] **Step 5: Commit**

```bash
git add rebound/audit/__init__.py rebound/audit/log.py tests/test_audit_chain.py
git commit -m "feat: hash-chained append-only audit log"
```

---

## Task 4: Event store with idempotent dedupe

**Files:**
- Create: `rebound/ingest/__init__.py`
- Create: `rebound/ingest/store.py`
- Test: `tests/test_store_dedupe.py`

**Effort:** 001, Unit U4. Satisfies FR-1.3, design doc D3, AC-2 precondition.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_store_dedupe.py
from rebound.ingest.store import EventStore


def test_first_insert_is_new(tmp_path):
    store = EventStore(tmp_path / "events.db")
    is_new = store.insert_if_new("evt_1", "payment.failed", {"x": 1})
    assert is_new is True


def test_duplicate_insert_is_rejected(tmp_path):
    store = EventStore(tmp_path / "events.db")
    store.insert_if_new("evt_1", "payment.failed", {"x": 1})
    is_new = store.insert_if_new("evt_1", "payment.failed", {"x": 1})
    assert is_new is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_store_dedupe.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.ingest'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/ingest/store.py
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Protocol


class EventStoreProtocol(Protocol):
    def insert_if_new(self, event_id: str, event_type: str, payload: dict) -> bool: ...


class EventStore:
    """SQLite-backed idempotent event store. `INSERT OR IGNORE` on event_id is the dedupe."""

    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        self.conn.commit()

    def insert_if_new(self, event_id: str, event_type: str, payload: dict) -> bool:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO events (event_id, event_type, payload) VALUES (?, ?, ?)",
            (event_id, event_type, json.dumps(payload)),
        )
        self.conn.commit()
        return cur.rowcount == 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_store_dedupe.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/ingest/__init__.py rebound/ingest/store.py tests/test_store_dedupe.py
git commit -m "feat: idempotent SQLite event store"
```

---

## Task 5: Taxonomy data (documented Razorpay fields)

**Files:**
- Create: `rebound/classify/__init__.py`
- Create: `rebound/classify/taxonomy.py`
- Test: `tests/test_taxonomy_rules.py` (taxonomy portion)

**Effort:** 002 (taxonomy-classifier). Satisfies FR-2a, requirements §6.

- [ ] **Step 0: Open the effort tracker**

Create `aidlc-docs/efforts/002-taxonomy-classifier/effort-state.md`, copying the shape of `aidlc-docs/efforts/001-scaffold-ingest-audit/effort-state.md` (units table, definition of done, log). List units: taxonomy data (this task), rule classifier (Task 6), LLM residue classifier (Task 7). State `in-progress`. Do this once per effort, at its first task — Effort 003 does the same in Task 8 Step 0, Effort 004 in Task 15 Step 0, Effort 005 in Task 22 Step 0, Effort 006 in Task 24 Step 0 — so Task 26 is not the first time any of these files are touched.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_taxonomy_rules.py
from rebound.classify.taxonomy import REASON_TO_CAUSE, DOC_URLS
from rebound.models import Cause


def test_insufficient_funds_maps_correctly():
    assert REASON_TO_CAUSE["insufficient_funds"] == Cause.INSUFFICIENT_FUNDS


def test_every_cause_has_a_doc_url():
    for cause in Cause:
        assert cause in DOC_URLS, f"{cause} missing a source doc URL"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_taxonomy_rules.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.classify'`

- [ ] **Step 3: Write minimal implementation**, transcribing the table from `aidlc-docs/inception/01-requirements.md` §6 exactly:

```python
# rebound/classify/taxonomy.py
from rebound.models import Cause

# error_reason (primary key) -> Cause, per documented values.
# Source: https://razorpay.com/docs/errors/payments/list/
#         https://razorpay.com/docs/payments/recurring-payments/emandate/errors/
REASON_TO_CAUSE: dict[str, Cause] = {
    "insufficient_funds": Cause.INSUFFICIENT_FUNDS,
    "card_expired": Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
    "debit_instrument_blocked": Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
    "authentication_failed": Cause.AUTHENTICATION_FAILED,
    "incorrect_otp": Cause.AUTHENTICATION_FAILED,
    "bank_technical_error": Cause.BANK_OR_GATEWAY_ERROR,
    "gateway_technical_error": Cause.BANK_OR_GATEWAY_ERROR,
    "payment_timed_out": Cause.BANK_OR_GATEWAY_ERROR,
    "mandate_not_active": Cause.MANDATE_NOT_ACTIVE,
    "payment_mandate_not_active": Cause.MANDATE_NOT_ACTIVE,
    "funds_blocked_by_mandate": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_declined": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_expired": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_failed": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_timeout": Cause.MANDATE_NOT_ACTIVE,
    "transaction_limit_exceeded": Cause.LIMIT_EXCEEDED,
    # generic / not distinguishable -> UNKNOWN, handled by absence from this map
}

# token.status values (recurring_details.status) that also mean MANDATE_NOT_ACTIVE
TOKEN_STATUS_TO_CAUSE: dict[str, Cause] = {
    "paused": Cause.MANDATE_NOT_ACTIVE,
    "cancelled": Cause.MANDATE_NOT_ACTIVE,
    "rejected": Cause.MANDATE_NOT_ACTIVE,
}

DOC_URLS: dict[Cause, str] = {
    Cause.INSUFFICIENT_FUNDS: "https://razorpay.com/docs/errors/payments/list/",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "https://razorpay.com/docs/errors/payments/list/",
    Cause.AUTHENTICATION_FAILED: "https://razorpay.com/docs/errors/payments/payment-methods-error-parameters/",
    Cause.BANK_OR_GATEWAY_ERROR: "https://razorpay.com/docs/errors/payments/list/",
    Cause.MANDATE_NOT_ACTIVE: "https://razorpay.com/docs/payments/recurring-payments/emandate/errors/",
    Cause.LIMIT_EXCEEDED: "https://razorpay.com/docs/errors/payments/list/",
    Cause.UNKNOWN: "https://razorpay.com/docs/api/payments/entity/",  # generic/null fields
}

# Per-cause test-mode reproducibility, for the report's honesty disclosure (requirements §6).
TEST_MODE_REPRODUCIBLE: dict[Cause, str] = {
    Cause.INSUFFICIENT_FUNDS: "yes_card",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "partial_card",
    Cause.AUTHENTICATION_FAILED: "yes_card",
    Cause.BANK_OR_GATEWAY_ERROR: "yes_card",
    Cause.MANDATE_NOT_ACTIVE: "documented_not_manufacturable",
    Cause.LIMIT_EXCEEDED: "synthetic_only",
    Cause.UNKNOWN: "yes_upi_and_dashboard",  # this is what generic failures ARE
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_taxonomy_rules.py -v`
Expected: 2 passed (more tests added in Task 6)

- [ ] **Step 5: Commit**

```bash
git add rebound/classify/__init__.py rebound/classify/taxonomy.py tests/test_taxonomy_rules.py
git commit -m "feat: root-cause taxonomy grounded in documented Razorpay fields"
```

---

## Task 6: Deterministic rule classifier

**Files:**
- Create: `rebound/classify/rules.py`
- Modify: `tests/test_taxonomy_rules.py` (add classifier tests)

**Effort:** 002. Satisfies FR-2a, FR-2c.

- [ ] **Step 1: Write the failing test** (append to `tests/test_taxonomy_rules.py`)

```python
from rebound.classify.rules import classify_by_rules
from rebound.models import PaymentFailure, Cause


def test_classifies_insufficient_funds_from_error_reason():
    pf = PaymentFailure(
        payment_id="pay_1", subscription_id="sub_1", amount=50000, method="card",
        error_reason="insufficient_funds", error_source="issuer_bank", error_step="payment_authorization",
    )
    result = classify_by_rules(pf)
    assert result is not None
    assert result.cause == Cause.INSUFFICIENT_FUNDS
    assert result.provenance == "rule"
    assert result.mapped_from == "error_reason=insufficient_funds"


def test_returns_none_on_generic_reason():
    pf = PaymentFailure(
        payment_id="pay_2", subscription_id="sub_2", amount=50000, method="upi",
        error_reason="payment_failed",
    )
    assert classify_by_rules(pf) is None


def test_token_status_maps_to_mandate_not_active():
    pf = PaymentFailure(
        payment_id="pay_3", subscription_id="sub_3", amount=50000, method="upi",
        token_status="paused",
    )
    result = classify_by_rules(pf)
    assert result is not None
    assert result.cause == Cause.MANDATE_NOT_ACTIVE
    assert result.mapped_from == "token_status=paused"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_taxonomy_rules.py -v`
Expected: FAIL — `ImportError: cannot import name 'classify_by_rules'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/classify/rules.py
from rebound.models import Classification, PaymentFailure
from rebound.classify.taxonomy import REASON_TO_CAUSE, TOKEN_STATUS_TO_CAUSE


def classify_by_rules(pf: PaymentFailure) -> Classification | None:
    """Pure lookup against documented fields. Returns None if the fields are
    generic/null and the case must fall through to the LLM residue path."""
    if pf.error_reason and pf.error_reason in REASON_TO_CAUSE:
        return Classification(
            cause=REASON_TO_CAUSE[pf.error_reason],
            provenance="rule",
            mapped_from=f"error_reason={pf.error_reason}",
        )
    if pf.token_status and pf.token_status in TOKEN_STATUS_TO_CAUSE:
        return Classification(
            cause=TOKEN_STATUS_TO_CAUSE[pf.token_status],
            provenance="rule",
            mapped_from=f"token_status={pf.token_status}",
        )
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_taxonomy_rules.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/classify/rules.py tests/test_taxonomy_rules.py
git commit -m "feat: deterministic rule-based cause classifier"
```

---

## Task 7: LLM residue classifier with abstain and disk cache

**Files:**
- Create: `rebound/classify/llm.py`
- Test: `tests/test_llm_classifier.py`

**Effort:** 002. Satisfies FR-2b, FR-2d.

- [ ] **Step 1: Write the failing test** (uses a fake client — no network, no `ANTHROPIC_API_KEY` needed)

```python
# tests/test_llm_classifier.py
import json
from rebound.classify.llm import LLMClassifier
from rebound.models import PaymentFailure


class FakeAnthropicClient:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = 0

    class _Messages:
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kwargs):
            self.outer.calls += 1
            class R:
                content = [type("Block", (), {"text": self.outer.response_text})()]
            return R()

    @property
    def messages(self):
        return self._Messages(self)


def test_confident_classification_is_used(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "authentication_failed", "confidence": 0.9, "rationale": "OTP mismatch mentioned"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path)
    pf = PaymentFailure(
        payment_id="p1", subscription_id="s1", amount=1000, method="card",
        error_reason="payment_failed", error_description="customer entered wrong OTP twice",
    )
    result = clf.classify(pf)
    assert result.cause.value == "authentication_failed"
    assert result.provenance == "llm"
    assert fake.calls == 1


def test_low_confidence_abstains(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "insufficient_funds", "confidence": 0.3, "rationale": "unclear"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path, confidence_threshold=0.75)
    pf = PaymentFailure(
        payment_id="p2", subscription_id="s2", amount=1000, method="upi",
        error_reason="payment_failed", error_description="vague failure",
    )
    result = clf.classify(pf)
    assert result.cause.value == "unknown"
    assert result.provenance == "abstain"


def test_second_call_hits_cache_not_the_client(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "bank_or_gateway_error", "confidence": 0.8, "rationale": "timeout mentioned"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path)
    pf = PaymentFailure(
        payment_id="p3", subscription_id="s3", amount=1000, method="card",
        error_reason="payment_failed", error_description="gateway took too long",
    )
    clf.classify(pf)
    clf.classify(pf)
    assert fake.calls == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'LLMClassifier'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/classify/llm.py
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any
from rebound.models import Cause, Classification, PaymentFailure

_VALID_CAUSES = {c.value for c in Cause}

_PROMPT = """You are classifying why a recurring payment failed, into exactly one of these causes:
insufficient_funds, instrument_expired_or_blocked, authentication_failed, bank_or_gateway_error,
mandate_not_active, limit_exceeded, unknown.

Use ONLY the free-text description below; do not invent details. If the description is too vague
to be confident, return "unknown" with low confidence rather than guessing.

Description: {description}

Respond with ONLY a JSON object: {{"cause": "<one of the causes above>", "confidence": <0.0-1.0>, "rationale": "<one sentence>"}}"""


class LLMClassifier:
    def __init__(self, client: Any, cache_dir: Path, confidence_threshold: float = 0.75,
                 model: str = "claude-sonnet-5") -> None:
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = confidence_threshold
        self.model = model

    def _cache_key(self, pf: PaymentFailure) -> Path:
        h = hashlib.sha256(pf.model_dump_json().encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.json"

    def classify(self, pf: PaymentFailure) -> Classification:
        cache_path = self._cache_key(pf)
        if cache_path.exists():
            raw = json.loads(cache_path.read_text())
        else:
            prompt = _PROMPT.format(description=pf.error_description or "")
            response = self.client.messages.create(
                model=self.model, max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            raw = json.loads(text)
            cache_path.write_text(json.dumps(raw))

        cause_str = raw.get("cause", "unknown")
        confidence = float(raw.get("confidence", 0.0))
        rationale = raw.get("rationale")

        if cause_str not in _VALID_CAUSES or confidence < self.threshold:
            return Classification(cause=Cause.UNKNOWN, provenance="abstain",
                                   confidence=confidence, rationale=rationale)
        return Classification(cause=Cause(cause_str), provenance="llm",
                               confidence=confidence, rationale=rationale)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_classifier.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/classify/llm.py tests/test_llm_classifier.py
git commit -m "feat: LLM residue classifier with confidence threshold, abstain, disk cache"
```

---

## Task 8: Policy gate and declarative policy table

**Files:**
- Create: `rebound/policy/__init__.py`
- Create: `rebound/policy/policy.yaml`
- Create: `rebound/policy/gate.py`
- Test: `tests/test_gate.py`

**Effort:** 003 (policy-gate-actions). Satisfies FR-3.1–3.5, design doc D2, AC-3 groundwork.

- [ ] **Step 0: Open the effort tracker**

Create `aidlc-docs/efforts/003-policy-gate-actions/effort-state.md` (same shape as 001/002). Units: gate + policy.yaml (this task), planner (Task 9), executor (Task 10), nudge drafter (Task 11). State `in-progress`.

- [ ] **Step 1: Write the failing test** — table-driven, covering every hard stop plus the default rows

```python
# tests/test_gate.py
from rebound.policy.gate import PolicyGate
from rebound.models import ActionRequest, Action, Cause, SubscriptionState


def make_state(**overrides):
    base = dict(subscription_id="sub_1", status="halted", attempt_no=0,
                consent=True, dispute_open=False, token_status=None)
    base.update(overrides)
    return SubscriptionState(**base)


def test_allows_charge_invoice_for_insufficient_funds_first_attempt():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision == "allow"


def test_blocks_when_dispute_open():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(dispute_open=True))
    assert verdict.decision == "block"
    assert "dispute" in verdict.rule_id


def test_blocks_when_no_consent():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.AUTHENTICATION_FAILED,
                         action=Action.NUDGE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(consent=False))
    assert verdict.decision == "block"
    assert "consent" in verdict.rule_id


def test_blocks_when_attempts_exhausted():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=4, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision in ("block", "escalate")


def test_blocks_when_amount_mismatch():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=99999999, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(), invoice_amount=50000)
    assert verdict.decision == "block"
    assert "amount" in verdict.rule_id


def test_mandate_not_active_never_allows_charge():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(token_status="paused"))
    assert verdict.decision != "allow"


def test_mandate_not_active_allows_payment_link_on_first_attempt():
    # Regression test: max_attempts_by_cause for mandate_not_active must be 1, not 0.
    # plan_action always proposes attempt_no=1 as the FIRST attempt, so a cap of 0 would
    # trip hard_stop.attempts_exhausted before this row is ever reached, silently
    # escalating every case instead of permitting the one payment_link attempt
    # requirements §6 documents ("no retry... once, then escalate").
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state(token_status="paused"))
    assert verdict.decision == "allow"
    assert verdict.rule_id == "causes.mandate_not_active.allow"


def test_instrument_expired_allows_payment_link_on_first_attempt_only():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    allowed = gate.evaluate(
        ActionRequest(subscription_id="sub_1", cause=Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
                      action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0),
        make_state(),
    )
    assert allowed.decision == "allow"
    second = gate.evaluate(
        ActionRequest(subscription_id="sub_1", cause=Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
                      action=Action.PAYMENT_LINK, amount=50000, attempt_no=2, sim_time=0.0),
        make_state(),
    )
    assert second.decision == "escalate"


def test_unknown_cause_always_escalates():
    gate = PolicyGate.from_yaml("rebound/policy/policy.yaml")
    req = ActionRequest(subscription_id="sub_1", cause=Cause.UNKNOWN,
                         action=Action.ESCALATE, amount=50000, attempt_no=1, sim_time=0.0)
    verdict = gate.evaluate(req, make_state())
    assert verdict.decision == "escalate"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.policy'`

- [ ] **Step 3: Write `rebound/policy/policy.yaml`**

```yaml
# Declarative policy table. Evaluated top to bottom: hard_stops first (any match -> block/escalate),
# then the row matching the request's cause.
hard_stops:
  - id: hard_stop.dispute_open
    when: dispute_open
    decision: block
  - id: hard_stop.no_consent
    when: no_consent
    action_in: [nudge]
    decision: block
  - id: hard_stop.amount_mismatch
    when: amount_mismatch
    decision: block
  - id: hard_stop.subscription_terminal
    when: subscription_terminal
    decision: block
  - id: hard_stop.attempts_exhausted
    when: attempts_exhausted
    max_attempts_by_cause:
      insufficient_funds: 3
      bank_or_gateway_error: 3
      authentication_failed: 1
      instrument_expired_or_blocked: 1
      mandate_not_active: 1
      limit_exceeded: 1
    decision: escalate
    # NOTE: these three are capped at 1, not 0. plan_action (Task 9) always sets
    # attempt_no = state.attempt_no + 1, so the *first* proposed action already has
    # attempt_no == 1. A cap of 0 would trip this hard stop before the gate ever
    # reaches the causes.* row below, silently escalating every occurrence of these
    # causes instead of allowing the single payment_link/nudge attempt requirements
    # §6 documents for them ("no retry... once, then escalate"). Verified by
    # Task 8's test_gate.py cases below.

causes:
  insufficient_funds:
    allow_actions: [charge_invoice, payment_link, nudge, escalate]
    cooldown_seconds: 3600
  instrument_expired_or_blocked:
    allow_actions: [payment_link, nudge, escalate]
    cooldown_seconds: 0
  authentication_failed:
    allow_actions: [nudge, escalate]
    cooldown_seconds: 1800
  bank_or_gateway_error:
    allow_actions: [charge_invoice, escalate]
    cooldown_seconds: 900
  mandate_not_active:
    allow_actions: [payment_link, nudge, escalate]
    cooldown_seconds: 0
  limit_exceeded:
    allow_actions: [payment_link, nudge, escalate]
    cooldown_seconds: 0
  unknown:
    allow_actions: [escalate]
    cooldown_seconds: 0
```

- [ ] **Step 4: Write `rebound/policy/gate.py`**

```python
# rebound/policy/gate.py
from __future__ import annotations
from pathlib import Path
import yaml
from rebound.models import ActionRequest, SubscriptionState, Verdict


class PolicyGate:
    """The ONLY module permitted to authorise a call to a money API.
    Deterministic: same inputs always produce the same verdict."""

    def __init__(self, policy: dict) -> None:
        self.policy = policy

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyGate":
        with open(path) as f:
            return cls(yaml.safe_load(f))

    def evaluate(self, req: ActionRequest, state: SubscriptionState,
                 invoice_amount: int | None = None) -> Verdict:
        invoice_amount = invoice_amount if invoice_amount is not None else req.amount

        if state.dispute_open:
            return Verdict(decision="block", rule_id="hard_stop.dispute_open",
                            reason="a dispute is open on this subscription")

        if not state.consent and req.action.value == "nudge":
            return Verdict(decision="block", rule_id="hard_stop.no_consent",
                            reason="customer has not consented to contact")

        if req.amount != invoice_amount:
            return Verdict(decision="block", rule_id="hard_stop.amount_mismatch",
                            reason=f"requested amount {req.amount} != invoice amount {invoice_amount}")

        if state.status in ("cancelled", "completed"):
            return Verdict(decision="block", rule_id="hard_stop.subscription_terminal",
                            reason=f"subscription status is {state.status}")

        cause_key = req.cause.value
        max_attempts = self.policy["hard_stops"][4]["max_attempts_by_cause"].get(cause_key, 0)
        if req.attempt_no > max_attempts:
            return Verdict(decision="escalate", rule_id="hard_stop.attempts_exhausted",
                            reason=f"attempt {req.attempt_no} exceeds max {max_attempts} for {cause_key}")

        row = self.policy["causes"].get(cause_key)
        if row is None or req.action.value not in row["allow_actions"]:
            return Verdict(decision="escalate", rule_id=f"causes.{cause_key}.action_not_allowed",
                            reason=f"{req.action.value} is not a permitted action for {cause_key}")

        return Verdict(decision="allow", rule_id=f"causes.{cause_key}.allow",
                        reason=f"{req.action.value} permitted for {cause_key}, attempt {req.attempt_no}")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_gate.py -v`
Expected: 9 passed. If `test_blocks_when_attempts_exhausted` fails, check the hard_stops list index (`[4]`) matches `attempts_exhausted`'s position in the YAML — prefer looking it up by `id` instead of a fixed index; fix `gate.py` to `next(hs for hs in self.policy["hard_stops"] if hs["id"] == "hard_stop.attempts_exhausted")` if the index is fragile. If the two new regression tests fail with `escalate` instead of `allow`, the YAML's `max_attempts_by_cause` for that cause is still `0` — it must be `1` (see the NOTE in Task 8 Step 3's `policy.yaml`).

- [ ] **Step 6: Commit**

```bash
git add rebound/policy/ tests/test_gate.py
git commit -m "feat: deterministic pre-action policy gate with hard stops"
```

---

## Task 9: Planner

**Files:**
- Create: `rebound/actions/__init__.py`
- Create: `rebound/actions/planner.py`
- Test: `tests/test_planner.py`

**Effort:** 003. Satisfies FR-3.1 input, requirements §6 "default policy" column.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_planner.py
from rebound.actions.planner import plan_action
from rebound.models import Cause, SubscriptionState, Action


def test_insufficient_funds_first_attempt_charges():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.INSUFFICIENT_FUNDS, state, amount=50000, sim_time=0.0)
    assert req.action == Action.CHARGE_INVOICE
    assert req.attempt_no == 1


def test_mandate_not_active_never_charges():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.MANDATE_NOT_ACTIVE, state, amount=50000, sim_time=0.0)
    assert req.action in (Action.PAYMENT_LINK, Action.NUDGE)


def test_unknown_always_escalates():
    state = SubscriptionState(subscription_id="s1", status="halted", attempt_no=0)
    req = plan_action(Cause.UNKNOWN, state, amount=50000, sim_time=0.0)
    assert req.action == Action.ESCALATE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_planner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/actions/planner.py
from rebound.models import Action, ActionRequest, Cause, SubscriptionState

_DEFAULT_ACTION: dict[Cause, Action] = {
    Cause.INSUFFICIENT_FUNDS: Action.CHARGE_INVOICE,
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: Action.PAYMENT_LINK,
    Cause.AUTHENTICATION_FAILED: Action.NUDGE,
    Cause.BANK_OR_GATEWAY_ERROR: Action.CHARGE_INVOICE,
    Cause.MANDATE_NOT_ACTIVE: Action.PAYMENT_LINK,
    Cause.LIMIT_EXCEEDED: Action.PAYMENT_LINK,
    Cause.UNKNOWN: Action.ESCALATE,
}


def plan_action(cause: Cause, state: SubscriptionState, amount: int, sim_time: float) -> ActionRequest:
    action = _DEFAULT_ACTION[cause]
    return ActionRequest(
        subscription_id=state.subscription_id, cause=cause, action=action,
        amount=amount, attempt_no=state.attempt_no + 1, sim_time=sim_time,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_planner.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/actions/__init__.py rebound/actions/planner.py tests/test_planner.py
git commit -m "feat: deterministic action planner"
```

---

## Task 10: Executor (Razorpay test-mode calls) with a fake client for tests

**Files:**
- Create: `rebound/actions/executor.py`
- Test: `tests/test_executor.py`

**Effort:** 003. Satisfies FR-4a, FR-4b, NFR-Safety.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_executor.py
from rebound.actions.executor import Executor
from rebound.models import Action, ActionRequest, Cause


class FakeRazorpayClient:
    def __init__(self):
        self.charged = []
        self.links_created = []

    class _Invoice:
        def __init__(self, outer):
            self.outer = outer
        def issue(self, invoice_id):
            return {"id": invoice_id, "status": "issued"}

    class _PaymentLink:
        def __init__(self, outer):
            self.outer = outer
        def create(self, data):
            self.outer.links_created.append(data)
            return {"id": "plink_1", "short_url": "https://rzp.io/i/fake"}

    @property
    def invoice(self):
        return self._Invoice(self)

    @property
    def payment_link(self):
        return self._PaymentLink(self)


def test_charge_invoice_rejects_amount_mismatch():
    fake = FakeRazorpayClient()
    ex = Executor(client=fake)
    req = ActionRequest(subscription_id="s1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=999, attempt_no=1, sim_time=0.0)
    outcome = ex.execute(req, invoice_id="inv_1", invoice_amount=50000)
    assert outcome.executed is False
    assert "amount" in (outcome.error or "")


def test_payment_link_creates_with_correct_amount():
    fake = FakeRazorpayClient()
    ex = Executor(client=fake)
    req = ActionRequest(subscription_id="s1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0)
    outcome = ex.execute(req, invoice_id="inv_1", invoice_amount=50000)
    assert outcome.executed is True
    assert fake.links_created[0]["amount"] == 50000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_executor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation.** This module is called **only** by code that has already received `Verdict(decision="allow")` from the gate (enforced at the call site in `pipeline.py`, Task 12) — it re-checks the amount as defense in depth, never trusts the caller alone.

```python
# rebound/actions/executor.py
from __future__ import annotations
from typing import Any
from rebound.models import Action, ActionRequest, Outcome


class Executor:
    """Calls Razorpay test-mode APIs. Must only be invoked after a gate `allow` verdict.

    Caveat: the amount check below compares req.amount against `invoice_amount`, which
    the pipeline (Task 12) always sets to `failure.amount` — the same source req.amount
    was derived from — so this is a self-consistency check, not independent verification
    against a real fetched invoice total. Acceptable for this build's synthetic/fixture
    data; Task 22 Step 9's real invoice lookup is the natural place to also fetch the
    real invoice amount and check against *that*, if there's time.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def execute(self, req: ActionRequest, invoice_id: str, invoice_amount: int) -> Outcome:
        if req.amount != invoice_amount:
            return Outcome(action=req.action, executed=False,
                            error=f"amount mismatch: {req.amount} != invoice {invoice_amount}")

        if req.action == Action.CHARGE_INVOICE:
            result = self.client.invoice.issue(invoice_id)
            return Outcome(action=req.action, executed=True, api_ref=result.get("id"))

        if req.action == Action.PAYMENT_LINK:
            result = self.client.payment_link.create({
                "amount": req.amount, "currency": "INR",
                "description": f"Recovery for subscription {req.subscription_id}",
                "notes": {"subscription_id": req.subscription_id, "cause": req.cause.value},
            })
            return Outcome(action=req.action, executed=True, api_ref=result.get("id"))

        return Outcome(action=req.action, executed=False, error=f"{req.action} is not an executor action")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_executor.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/actions/executor.py tests/test_executor.py
git commit -m "feat: test-mode executor with amount re-verification"
```

---

## Task 11: Nudge drafter (LLM, logged, never sent)

**Files:**
- Create: `rebound/actions/nudge.py`
- Modify: `tests/test_executor.py` (add nudge test) or create `tests/test_nudge.py`

**Effort:** 003. Satisfies FR-4c.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nudge.py
from rebound.actions.nudge import draft_nudge
from rebound.models import Cause


class FakeAnthropicClient:
    class _Messages:
        def create(self, **kwargs):
            class R:
                content = [type("Block", (), {"text": "Your card has expired — please update it to keep your subscription active."})()]
            return R()
    @property
    def messages(self):
        return self._Messages()


def test_draft_nudge_returns_text_only_no_send():
    fake = FakeAnthropicClient()
    text = draft_nudge(fake, Cause.INSTRUMENT_EXPIRED_OR_BLOCKED)
    assert "expired" in text.lower()
    assert len(text) < 400  # short, per FR-4c "≤2 sentences"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_nudge.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/actions/nudge.py
from typing import Any
from rebound.models import Cause

_TEMPLATES = {
    Cause.INSUFFICIENT_FUNDS: "the customer's last payment attempt showed insufficient funds",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "the customer's card appears expired or blocked",
    Cause.AUTHENTICATION_FAILED: "the customer needs to re-approve/re-authenticate the payment (e.g. UPI AutoPay mandate re-authorisation)",
    Cause.MANDATE_NOT_ACTIVE: "the customer's payment mandate is no longer active and needs re-approval",
    Cause.LIMIT_EXCEEDED: "the transaction exceeded a limit; a different payment method may be needed",
}


def draft_nudge(client: Any, cause: Cause) -> str:
    """Drafts a short customer-facing message. NEVER sent — logged to the audit trail
    and the exceptions/report output for a human operator to review and send manually."""
    context = _TEMPLATES.get(cause, "there was an issue with the recent payment")
    prompt = (
        f"Write a single short, polite message (max 2 sentences, plain English) to a customer "
        f"whose recurring payment failed because {context}. Ask them to take the appropriate action. "
        f"Do not mention internal system details."
    )
    response = client.messages.create(
        model="claude-sonnet-5", max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_nudge.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/actions/nudge.py tests/test_nudge.py
git commit -m "feat: LLM nudge drafter (logged, never sent)"
```

---

## Task 12: Pipeline — wire ingest, classify, plan, gate, act, audit together

**Files:**
- Create: `rebound/pipeline.py`
- Test: `tests/test_batch_smoke.py` (first version, single event)

**Effort:** 001 Unit U5 (stub), completed once 002+003 exist. This is the integration point — build it after Tasks 5–11.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_batch_smoke.py
from pathlib import Path
from rebound.pipeline import Pipeline, PipelineContext
from rebound.models import PaymentFailure, SubscriptionState
from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.policy.gate import PolicyGate
from rebound.sim.clock import SimClock


class FakeRazorpayClient:
    class _Invoice:
        def issue(self, invoice_id):
            return {"id": invoice_id, "status": "issued"}
    @property
    def invoice(self):
        return self._Invoice()
    @property
    def payment_link(self):
        raise NotImplementedError


def build_context(tmp_path) -> PipelineContext:
    return PipelineContext(
        store=EventStore(tmp_path / "events.db"),
        audit=AuditLog(tmp_path / "audit.jsonl"),
        gate=PolicyGate.from_yaml("rebound/policy/policy.yaml"),
        executor_client=FakeRazorpayClient(),
        llm_client=None,  # not needed: this failure has a documented error_reason
        clock=SimClock(0.0),
    )


def test_pipeline_processes_one_documented_failure_end_to_end(tmp_path):
    ctx = build_context(tmp_path)
    pl = Pipeline(ctx)
    failure = PaymentFailure(payment_id="pay_1", subscription_id="sub_1", amount=50000,
                              method="card", error_reason="insufficient_funds")
    state = SubscriptionState(subscription_id="sub_1", status="halted", attempt_no=0)
    result = pl.process_failure(event_id="evt_1", failure=failure, state=state, invoice_id="inv_1")
    assert result is not None
    assert result.classification.cause.value == "insufficient_funds"
    assert result.classification.provenance == "rule"
    assert result.outcome.executed is True
    assert ctx.audit.verify() is True


def test_duplicate_event_id_produces_no_second_action(tmp_path):
    ctx = build_context(tmp_path)
    pl = Pipeline(ctx)
    failure = PaymentFailure(payment_id="pay_1", subscription_id="sub_1", amount=50000,
                              method="card", error_reason="insufficient_funds")
    state = SubscriptionState(subscription_id="sub_1", status="halted", attempt_no=0)
    pl.process_failure(event_id="evt_dup", failure=failure, state=state, invoice_id="inv_1")
    second = pl.process_failure(event_id="evt_dup", failure=failure, state=state, invoice_id="inv_1")
    assert second is None  # rejected as duplicate, no ProcessResult produced
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_batch_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.pipeline'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/pipeline.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from rebound.models import Outcome, PaymentFailure, ProcessResult, SubscriptionState
from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.classify.rules import classify_by_rules
from rebound.classify.llm import LLMClassifier
from rebound.actions.planner import plan_action
from rebound.policy.gate import PolicyGate
from rebound.actions.executor import Executor
from rebound.sim.clock import Clock


@dataclass
class PipelineContext:
    store: EventStore
    audit: AuditLog
    gate: PolicyGate
    executor_client: Any
    llm_client: Any
    clock: Clock
    llm_cache_dir: str = ".llm_cache"


class Pipeline:
    def __init__(self, ctx: PipelineContext) -> None:
        self.ctx = ctx
        self.executor = Executor(ctx.executor_client)

    def process_failure(self, event_id: str, failure: PaymentFailure,
                         state: SubscriptionState, invoice_id: str) -> Optional[ProcessResult]:
        """Returns None only when the event_id is a duplicate (no action taken).
        Otherwise returns both the Classification and the Outcome, so callers
        (the batch runner, the report) can compute classifier metrics as well
        as gate/execution metrics from one call."""
        sim_time = self.ctx.clock.now()
        is_new = self.ctx.store.insert_if_new(event_id, "payment.failed", failure.model_dump())
        self.ctx.audit.append("event_received", failure.model_dump(), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)
        if not is_new:
            self.ctx.audit.append("duplicate_rejected", {"event_id": event_id}, sim_time,
                                   event_id=event_id, subscription_id=failure.subscription_id)
            return None

        classification = classify_by_rules(failure)
        if classification is None:
            if self.ctx.llm_client is None:
                from rebound.models import Classification, Cause
                classification = Classification(cause=Cause.UNKNOWN, provenance="abstain",
                                                  rationale="no LLM client configured")
            else:
                classifier = LLMClassifier(self.ctx.llm_client, cache_dir=self.ctx.llm_cache_dir)
                classification = classifier.classify(failure)
        self.ctx.audit.append("classified", classification.model_dump(), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        req = plan_action(classification.cause, state, amount=failure.amount, sim_time=sim_time)
        self.ctx.audit.append("action_proposed", req.model_dump(), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        verdict = self.ctx.gate.evaluate(req, state, invoice_amount=failure.amount)
        self.ctx.audit.append("policy_verdict", verdict.model_dump(), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)

        if verdict.decision != "allow":
            self.ctx.audit.append("action_blocked", {"verdict": verdict.model_dump()}, sim_time,
                                   event_id=event_id, subscription_id=failure.subscription_id)
            outcome = Outcome(action=req.action, executed=False, error=verdict.reason)
            return ProcessResult(classification=classification, outcome=outcome)

        outcome = self.executor.execute(req, invoice_id=invoice_id, invoice_amount=failure.amount)
        self.ctx.audit.append("action_executed" if outcome.executed else "action_failed",
                               outcome.model_dump(), sim_time,
                               event_id=event_id, subscription_id=failure.subscription_id)
        return ProcessResult(classification=classification, outcome=outcome)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_batch_smoke.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/pipeline.py tests/test_batch_smoke.py
git commit -m "feat: wire ingest, classify, plan, gate, execute, audit into one pipeline"
```

---

## Task 13: Webhook receiver with signature verification

**Files:**
- Create: `rebound/ingest/webhook.py`
- Test: `tests/test_webhook_signature.py`

**Effort:** 001 Unit U6. Satisfies FR-1.1, 1.2, 1.4. Ingest + dedupe only — dispatch into the pipeline is wired in Task 13a, once the adapter that translates raw Razorpay JSON into our models exists.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_webhook_signature.py
import hashlib
import hmac
import json
from fastapi.testclient import TestClient
from rebound.ingest.webhook import create_app


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "testsecret")
    app = create_app(db_path=tmp_path / "events.db")
    client = TestClient(app)
    body = json.dumps({"event": "payment.failed", "payload": {}}).encode()
    sig = sign(body, "testsecret")
    resp = client.post("/webhook", content=body,
                        headers={"X-Razorpay-Signature": sig, "x-razorpay-event-id": "evt_1"})
    assert resp.status_code == 200


def test_invalid_signature_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "testsecret")
    app = create_app(db_path=tmp_path / "events.db")
    client = TestClient(app)
    body = json.dumps({"event": "payment.failed", "payload": {}}).encode()
    resp = client.post("/webhook", content=body,
                        headers={"X-Razorpay-Signature": "wrong", "x-razorpay-event-id": "evt_2"})
    assert resp.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_webhook_signature.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/ingest/webhook.py
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, Request, Response
from rebound.ingest.store import EventStore


def _verify(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def create_app(db_path: Path, ctx: Optional[Any] = None) -> FastAPI:
    """`ctx`, when provided, is a rebound.pipeline.PipelineContext — if set, a new,
    non-duplicate event is also dispatched through the pipeline (Task 13a wires this
    for `payment.failed` / `subscription.halted`). If None (as in the tests above),
    the handler does ingest + dedupe only."""
    app = FastAPI()
    store = EventStore(db_path)

    @app.post("/webhook")
    async def webhook(request: Request):
        body = await request.body()
        signature = request.headers.get("x-razorpay-signature", "")
        secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not secret or not _verify(body, signature, secret):
            return Response(status_code=400, content="invalid signature")

        event_id = request.headers.get("x-razorpay-event-id", "")
        payload = json.loads(body)
        is_new = store.insert_if_new(event_id, payload.get("event", "unknown"), payload)

        if is_new and ctx is not None:
            _dispatch(ctx, event_id, payload)

        return Response(status_code=200, content="ok" if is_new else "duplicate")

    return app


def _dispatch(ctx: Any, event_id: str, payload: dict) -> None:
    """Filled in by Task 13a once the adapter exists. Left as a hook here so this
    task's tests (ctx=None) pass on their own before Task 13a's tests are added.
    From Task 22 onward, event_to_pipeline_inputs also accepts ctx.executor_client
    to resolve a real invoice_id instead of the placeholder — passed through here."""
    from rebound.ingest.adapter import event_to_pipeline_inputs
    from rebound.pipeline import Pipeline

    parsed = event_to_pipeline_inputs(payload, client=getattr(ctx, "executor_client", None))
    if parsed is None:
        return  # event type we don't act on (e.g. subscription.charged) — ingest only
    failure, state, invoice_id = parsed
    Pipeline(ctx).process_failure(event_id=event_id, failure=failure, state=state, invoice_id=invoice_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_webhook_signature.py -v`
Expected: 2 passed (both calls use `ctx=None`, so `_dispatch` — and its import of the not-yet-written `adapter` module — is never reached).

- [ ] **Step 5: Commit**

```bash
git add rebound/ingest/webhook.py tests/test_webhook_signature.py
git commit -m "feat: FastAPI webhook receiver with HMAC signature verification"
```

---

## Task 13a: Razorpay payload adapter and live dispatch wiring

**Files:**
- Create: `rebound/ingest/adapter.py`
- Test: `tests/test_adapter.py`

**Effort:** 001, closes the gap the plan reviewer flagged: the video script's live "classified, gated, executed" moment (Task 25) needs `serve` to actually run events through `Pipeline`, which needs raw Razorpay JSON translated into `PaymentFailure`/`SubscriptionState`.

- [ ] **Step 1: Write the failing test**, using the shape of a real `payment.failed` webhook body per `https://razorpay.com/docs/api/payments/entity/` (`payload.payment.entity`) and a `subscription.halted` body (`payload.subscription.entity`):

```python
# tests/test_adapter.py
from rebound.ingest.adapter import event_to_pipeline_inputs
from rebound.models import Cause


def test_payment_failed_extracts_failure_and_state():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {"entity": {
                "id": "pay_abc", "amount": 50000, "method": "card",
                "error_code": "BAD_REQUEST_ERROR", "error_reason": "insufficient_funds",
                "error_source": "issuer_bank", "error_step": "payment_authorization",
                "description": "", "notes": {"subscription_id": "sub_abc"},
            }},
        },
    }
    result = event_to_pipeline_inputs(payload)
    assert result is not None
    failure, state, invoice_id = result
    assert failure.subscription_id == "sub_abc"
    assert failure.error_reason == "insufficient_funds"
    assert state.status == "active"  # payment.failed alone doesn't imply halted


def test_subscription_halted_extracts_state():
    payload = {
        "event": "subscription.halted",
        "payload": {
            "subscription": {"entity": {
                "id": "sub_xyz", "status": "halted",
                "notes": {},
            }},
        },
    }
    result = event_to_pipeline_inputs(payload)
    assert result is not None
    failure, state, invoice_id = result
    assert state.status == "halted"
    assert state.subscription_id == "sub_xyz"


def test_unhandled_event_type_returns_none():
    payload = {"event": "subscription.charged", "payload": {}}
    assert event_to_pipeline_inputs(payload) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rebound.ingest.adapter'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/ingest/adapter.py
from __future__ import annotations
from typing import Any
from rebound.models import PaymentFailure, SubscriptionState

_HANDLED_EVENTS = {"payment.failed", "subscription.halted", "subscription.pending"}


def _resolve_invoice_id(client: Any, subscription_id: str) -> str:
    """Real Razorpay invoice lookup, shared by both branches below since either event
    type can lead the planner to choose `charge_invoice` (it decides from the cause
    alone, not from subscription status — see Task 9). Falls back to a placeholder
    when no real client is configured (batch/tests). Task 22 Step 9 replaces only
    this function's body with a real `client.invoice.all(...)` call once the response
    shape has been confirmed against the live API — callers never change."""
    if client is None:
        return f"inv_{subscription_id}"
    return f"inv_{subscription_id}"  # placeholder body; Task 22 replaces this line only


def event_to_pipeline_inputs(
    payload: dict, client: Any = None,
) -> tuple[PaymentFailure, SubscriptionState, str] | None:
    """Translates a raw Razorpay webhook envelope into (PaymentFailure, SubscriptionState,
    invoice_id) for Pipeline.process_failure. Returns None for event types this build
    doesn't act on (ingest-only, e.g. subscription.charged). `client`, when a real
    Razorpay client, is used by _resolve_invoice_id for a live invoice lookup — see
    Task 22 Step 9; batches and tests pass client=None and get the placeholder id."""
    event_type = payload.get("event")
    if event_type not in _HANDLED_EVENTS:
        return None

    body = payload.get("payload", {})

    if event_type == "payment.failed":
        entity = body.get("payment", {}).get("entity", {})
        subscription_id = (entity.get("notes") or {}).get("subscription_id") or entity.get("subscription_id", "unknown")
        failure = PaymentFailure(
            payment_id=entity.get("id", "unknown"),
            subscription_id=subscription_id,
            amount=entity.get("amount", 0),
            method=entity.get("method", "unknown"),
            error_code=entity.get("error_code"),
            error_description=entity.get("error_description") or entity.get("description"),
            error_source=entity.get("error_source"),
            error_step=entity.get("error_step"),
            error_reason=entity.get("error_reason"),
        )
        # payment.failed alone doesn't move the subscription to halted (that needs 4
        # failed retries) — default to "active" unless a subscription.entity is also present.
        state = SubscriptionState(subscription_id=subscription_id, status="active", attempt_no=0)
        return failure, state, _resolve_invoice_id(client, subscription_id)

    # subscription.halted / subscription.pending
    entity = body.get("subscription", {}).get("entity", {})
    subscription_id = entity.get("id", "unknown")
    failure = PaymentFailure(
        payment_id="unknown", subscription_id=subscription_id, amount=0, method="unknown",
    )
    state = SubscriptionState(
        subscription_id=subscription_id, status=entity.get("status", "halted"), attempt_no=0,
    )
    return failure, state, _resolve_invoice_id(client, subscription_id)
```

**Known limitation, deliberately left open here:** `invoice_id` is returned as the placeholder `f"inv_{subscription_id}"` in **both** branches (`payment.failed` and `subscription.halted`/`pending`) — note the planner (Task 9) picks `charge_invoice` from the *cause* alone, not from subscription status, so a live `payment.failed` event can trigger a real charge attempt just as easily as a `subscription.halted` one. This placeholder is correct for the batch (Task 15's fixtures) and for tests using `FakeRazorpayClient`, which don't care what the ID string is. It is **not** a real Razorpay invoice ID, so a live `charge_invoice` action against the real API (Task 21/25) will fail with an invoice-not-found error until Task 22 replaces it with a real lookup keyed on `subscription_id` — e.g. `client.invoice.all({"subscription_id": subscription_id, "status": "issued"})` and taking the first result — applied uniformly regardless of which event type triggered the lookup. Do this as part of Task 22 (it is exactly the kind of real-API-shape discovery that task exists for), and record whatever the real behavior turns out to be in `FAILURES.md` rather than guessing now.

Note: for `subscription.halted` this adapter has no `error_reason` (that lives on the earlier `payment.failed` event for the same subscription) — Task 22's real captures will confirm whether Razorpay's `subscription.halted` payload embeds the last payment's error fields directly; if it does, extend this adapter then and add a regression test, recording the finding in `FAILURES.md`. Do not guess at the shape now — this is exactly the kind of thing hour-zero capture (Task 22) exists to settle.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_adapter.py -v`
Expected: 3 passed

- [ ] **Step 5: Wire it into `serve`** — no code change needed here: `webhook.py`'s `_dispatch()` (Task 13) already imports and calls `event_to_pipeline_inputs`; this task just makes that import resolve. Re-run Task 13's tests to confirm nothing broke:

Run: `pytest tests/test_webhook_signature.py tests/test_adapter.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add rebound/ingest/adapter.py tests/test_adapter.py
git commit -m "feat: adapter translating raw Razorpay webhook JSON into pipeline inputs"
```

---

## Task 14: Fixture replayer

**Files:**
- Create: `rebound/ingest/fixtures.py`
- Create: `fixtures/recorded/README.md` (placeholder until Task 22 populates real captures)
- Test: add to `tests/test_batch_smoke.py` or new `tests/test_fixtures.py`

**Effort:** 001 Unit U7. Satisfies FR-1.5, design doc D6.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fixtures.py
import json
from rebound.ingest.fixtures import load_fixture, iter_fixtures


def test_load_single_fixture(tmp_path):
    f = tmp_path / "sample.json"
    f.write_text(json.dumps({"event_id": "evt_x", "event": "payment.failed", "payload": {"a": 1}}))
    envelope = load_fixture(f)
    assert envelope["event_id"] == "evt_x"


def test_iter_fixtures_yields_all_json_files(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"event_id": "e1", "event": "x", "payload": {}}))
    (tmp_path / "b.json").write_text(json.dumps({"event_id": "e2", "event": "x", "payload": {}}))
    ids = sorted(e["event_id"] for e in iter_fixtures(tmp_path))
    assert ids == ["e1", "e2"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fixtures.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/ingest/fixtures.py
import json
from pathlib import Path
from typing import Iterator


def load_fixture(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def iter_fixtures(directory: Path) -> Iterator[dict]:
    for f in sorted(Path(directory).glob("*.json")):
        yield load_fixture(f)
```

Also create `fixtures/recorded/README.md`:

```markdown
# Recorded fixtures

Real Razorpay test-mode webhook/payment payloads captured in Task 22 (Effort 005),
with any key material stripped. Each file is one JSON envelope:
`{"event_id": "...", "event": "...", "payload": {...}}`.

Populated once `.env` test keys are available. Until then this directory is empty
and the scenario generator (Task 15) falls back to fully synthetic scenarios, labelled as such
in the report.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fixtures.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/ingest/fixtures.py fixtures/recorded/README.md tests/test_fixtures.py
git commit -m "feat: fixture replayer sharing the pipeline's live-webhook code path"
```

---

## Task 15: Seeded scenario generator

**Files:**
- Create: `rebound/sim/scenarios.py`
- Test: `tests/test_scenarios.py`

**Effort:** 004 (sim-batch-report). Satisfies FR-6.1, FR-6.1a (Amendment A), FR-6.2, FR-6.3.

- [ ] **Step 0: Open the effort tracker**

Create `aidlc-docs/efforts/004-sim-batch-report/effort-state.md` (same shape as prior efforts). Units: scenario generator (this task), batch runner incl. classification threading (Task 16), report with per-cause P/R and confusion matrix (Task 17), HTML report (Task 18). State `in-progress`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scenarios.py
from rebound.sim.scenarios import generate_scenarios
from rebound.models import Cause


def test_same_seed_produces_identical_batch():
    a = generate_scenarios(seed=42, n=60)
    b = generate_scenarios(seed=42, n=60)
    assert [s.id for s in a] == [s.id for s in b]
    assert [s.truth_cause for s in a] == [s.truth_cause for s in b]


def test_batch_has_at_least_20_heldout():
    scenarios = generate_scenarios(seed=42, n=60)
    heldout = [s for s in scenarios if "heldout" in s.tags]
    assert len(heldout) >= 20


def test_batch_has_at_least_5_duplicate_replays():
    scenarios = generate_scenarios(seed=42, n=60)
    dupes = [s for s in scenarios if "replay_duplicate" in s.tags]
    assert len(dupes) >= 5


def test_batch_declares_recorded_vs_synthetic():
    scenarios = generate_scenarios(seed=42, n=60, recorded_dir=None)  # no fixtures yet
    for s in scenarios:
        assert ("recorded" in s.tags) != ("synthetic" not in s.tags) or "synthetic" in s.tags
        assert "recorded" in s.tags or "synthetic" in s.tags


def test_recorded_envelope_is_converted_not_validated_as_scenario(tmp_path):
    # Regression test: recorded fixtures are raw {event_id, event, payload} webhook
    # envelopes (Task 22), not pre-built Scenario JSON. Scenario.model_validate(envelope)
    # would raise a Pydantic ValidationError here — generate_scenarios must instead run
    # the envelope through the adapter and derive truth_cause from the documented fields.
    import json
    envelope = {
        "event_id": "evt_captured_1", "event": "payment.failed",
        "payload": {"payment": {"entity": {
            "id": "pay_captured", "amount": 49900, "method": "card",
            "error_reason": "insufficient_funds", "error_source": "issuer_bank",
            "error_step": "payment_authorization", "notes": {"subscription_id": "sub_captured"},
        }}},
    }
    (tmp_path / "card_insufficient_funds.json").write_text(json.dumps(envelope))

    scenarios = generate_scenarios(seed=1, n=1, recorded_dir=tmp_path)
    recorded = [s for s in scenarios if "recorded" in s.tags]
    assert len(recorded) == 1
    assert recorded[0].truth_cause == Cause.INSUFFICIENT_FUNDS
    assert recorded[0].failure.subscription_id == "sub_captured"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenarios.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation.** Starting point is requirements §FR-6.1's decline-mix (30% insufficient funds, 15% expired card, 15% auth failed, 10%+10% bank/gateway-error+timeout folded together, 10% mandate paused/not-active, 10% generic/ambiguous). That mix has 6 buckets; the code below carves 5 points out of bank/gateway-error's 20% to give `LIMIT_EXCEEDED` its own 5% bucket so all 7 taxonomy causes are actually exercised (see the comment in the code) — bank/gateway-error is 15%, not 20%, as a deliberate, documented deviation from FR-6.1's mix, not an error.

```python
# rebound/sim/scenarios.py
from __future__ import annotations
import random
from pathlib import Path
from rebound.models import Cause, PaymentFailure, Scenario, SubscriptionState
from rebound.ingest.fixtures import iter_fixtures

_DECLINE_MIX: list[tuple[Cause, float]] = [
    (Cause.INSUFFICIENT_FUNDS, 0.30),
    (Cause.INSTRUMENT_EXPIRED_OR_BLOCKED, 0.15),
    (Cause.AUTHENTICATION_FAILED, 0.15),
    (Cause.BANK_OR_GATEWAY_ERROR, 0.15),
    (Cause.MANDATE_NOT_ACTIVE, 0.10),
    (Cause.LIMIT_EXCEEDED, 0.05),
    (Cause.UNKNOWN, 0.10),
]
# All 7 causes are represented in the generator (unlike an earlier draft that omitted
# LIMIT_EXCEEDED) so the held-out classifier metrics cover the full taxonomy, not 6/7 of it.

_REASON_BY_CAUSE = {
    Cause.INSUFFICIENT_FUNDS: "insufficient_funds",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "card_expired",
    Cause.AUTHENTICATION_FAILED: "authentication_failed",
    Cause.BANK_OR_GATEWAY_ERROR: "bank_technical_error",
    Cause.MANDATE_NOT_ACTIVE: None,  # comes via token_status instead
    Cause.LIMIT_EXCEEDED: "transaction_limit_exceeded",
    Cause.UNKNOWN: "payment_failed",
}


def _synthetic_scenario(idx: int, rng: random.Random) -> Scenario:
    causes, weights = zip(*_DECLINE_MIX)
    cause = rng.choices(causes, weights=weights, k=1)[0]
    amount = rng.choice([49900, 99900, 149900, 299900])
    reason = _REASON_BY_CAUSE[cause]
    failure = PaymentFailure(
        payment_id=f"pay_synth_{idx}", subscription_id=f"sub_synth_{idx}",
        amount=amount, method=rng.choice(["card", "upi"]),
        error_reason=reason,
        token_status="paused" if cause == Cause.MANDATE_NOT_ACTIVE else None,
        error_description="customer support ticket text unclear about cause" if cause == Cause.UNKNOWN else None,
    )
    state = SubscriptionState(subscription_id=failure.subscription_id, status="halted", attempt_no=0)
    return Scenario(id=f"scn_{idx}", tags=["synthetic"], failure=failure, state=state, truth_cause=cause)


def _scenario_from_recorded_envelope(envelope: dict, idx: int) -> Scenario | None:
    """Recorded fixtures (Task 22) are saved as raw {event_id, event, payload}
    webhook envelopes, NOT pre-built Scenario JSON — this runs them through the
    same adapter the live webhook path uses (Task 13a), then derives the ground
    truth from the documented fields themselves via the rule classifier. This is
    valid ground truth specifically because each recorded file was captured using
    a test card/scenario deliberately chosen to trigger that documented reason
    (Task 22 Step 2) — we are not guessing the label, we are reading back the
    label Razorpay's own response already committed to. Returns None (skipped)
    for an envelope the adapter doesn't recognize (e.g. an accidental capture of
    an unrelated event type)."""
    from rebound.ingest.adapter import event_to_pipeline_inputs
    from rebound.classify.rules import classify_by_rules

    # envelope IS the {"event_id", "event", "payload"} shape event_to_pipeline_inputs
    # expects — do NOT unwrap to envelope["payload"] first, that strips the top-level
    # "event" key the adapter reads to decide the event type, and it would silently
    # return None for every recorded fixture (verified against Task 13a's own tests,
    # which call event_to_pipeline_inputs on the full envelope, not its "payload" key).
    parsed = event_to_pipeline_inputs(envelope)
    if parsed is None:
        return None
    failure, state, _invoice_id = parsed
    classification = classify_by_rules(failure)
    truth_cause = classification.cause if classification is not None else Cause.UNKNOWN
    return Scenario(id=f"scn_recorded_{idx}", tags=["recorded"], failure=failure,
                     state=state, truth_cause=truth_cause)


def generate_scenarios(seed: int, n: int = 60, recorded_dir: Path | None = None) -> list[Scenario]:
    rng = random.Random(seed)
    scenarios: list[Scenario] = []

    recorded_count = 0
    if recorded_dir is not None and Path(recorded_dir).exists():
        for i, envelope in enumerate(iter_fixtures(Path(recorded_dir))):
            scenario = _scenario_from_recorded_envelope(envelope, i)
            if scenario is not None:
                scenarios.append(scenario)
                recorded_count += 1

    remaining = n - recorded_count
    for i in range(remaining):
        scenarios.append(_synthetic_scenario(i, rng))

    # tag >=20 as heldout (never used while tuning rules/prompts), spread across causes
    heldout_target = max(20, n // 3)
    heldout_idx = set(rng.sample(range(len(scenarios)), min(heldout_target, len(scenarios))))
    for i in heldout_idx:
        scenarios[i] = scenarios[i].model_copy(update={"tags": scenarios[i].tags + ["heldout"]})

    # tag >=5 for duplicate-webhook replay
    dup_target = 5
    dup_idx = rng.sample(range(len(scenarios)), min(dup_target, len(scenarios)))
    for i in dup_idx:
        scenarios[i] = scenarios[i].model_copy(update={"tags": scenarios[i].tags + ["replay_duplicate"]})

    return scenarios
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenarios.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/sim/scenarios.py tests/test_scenarios.py
git commit -m "feat: seeded scenario generator with held-out set and duplicate replays"
```

---

## Task 16: Batch runner

**Files:**
- Create: `rebound/sim/batch.py`
- Modify: `tests/test_batch_smoke.py` (add a full-batch test)

**Effort:** 004. Satisfies FR-6.1–6.3 execution.

- [ ] **Step 1: Write the failing test** (append to `tests/test_batch_smoke.py`)

```python
from rebound.sim.batch import run_batch
from rebound.sim.scenarios import generate_scenarios


def test_run_batch_produces_one_result_per_scenario_plus_duplicates(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    # every non-duplicate-tagged scenario produces exactly one primary result,
    # every replay_duplicate scenario produces one extra "duplicate_rejected" result
    assert len(results) >= len(scenarios)


def test_run_batch_records_predicted_cause_from_classification(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    primary = [r for r in results if "replay_duplicate_check" not in r["tags"]]
    for r in primary:
        assert r["predicted_cause"] is not None
        assert r["provenance"] in ("rule", "llm", "abstain")
        # AC-3: a rule-based classification must cite the documented field it came from
        if r["provenance"] == "rule":
            assert r["mapped_from"] is not None and "=" in r["mapped_from"]


def test_run_batch_has_zero_policy_violations(tmp_path):
    ctx = build_context(tmp_path)
    scenarios = generate_scenarios(seed=1, n=10)
    results = run_batch(ctx, scenarios)
    violations = [r for r in results if r.get("policy_violation")]
    assert violations == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_batch_smoke.py -v`
Expected: FAIL — `ImportError: cannot import name 'run_batch'`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/sim/batch.py
from __future__ import annotations
from rebound.models import Scenario
from rebound.pipeline import Pipeline, PipelineContext


def run_batch(ctx: PipelineContext, scenarios: list[Scenario]) -> list[dict]:
    pipeline = Pipeline(ctx)
    results: list[dict] = []

    for scenario in scenarios:
        event_id = f"evt_{scenario.id}"
        result = pipeline.process_failure(
            event_id=event_id, failure=scenario.failure, state=scenario.state,
            invoice_id=f"inv_{scenario.id}",
        )
        outcome = result.outcome if result else None
        results.append({
            "scenario_id": scenario.id,
            "tags": scenario.tags,
            "truth_cause": scenario.truth_cause.value,
            "predicted_cause": result.classification.cause.value if result else None,
            "provenance": result.classification.provenance if result else None,
            "mapped_from": result.classification.mapped_from if result else None,  # AC-3
            "outcome": outcome.model_dump() if outcome else None,
            "policy_violation": bool(outcome and outcome.executed and outcome.error),
        })

        if "replay_duplicate" in scenario.tags:
            ctx.clock.advance(1)  # SimClock; RealClock ignores .advance if not implemented
            dup_result = pipeline.process_failure(
                event_id=event_id,  # SAME event_id -> must be rejected
                failure=scenario.failure, state=scenario.state, invoice_id=f"inv_{scenario.id}",
            )
            results.append({
                "scenario_id": scenario.id, "tags": ["replay_duplicate_check"],
                "truth_cause": scenario.truth_cause.value,
                "predicted_cause": None, "provenance": None, "mapped_from": None,
                "outcome": dup_result.outcome.model_dump() if dup_result else None,
                "policy_violation": dup_result is not None,  # must be None (rejected)
            })

    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_batch_smoke.py -v`
Expected: 5 passed (2 from Task 12 + 3 new). Note: `SimClock` from Task 2 needs `.advance()`; if using `RealClock` here would error, so `run_batch`'s duplicate-replay path assumes a `SimClock` in batch context — assert this in the function or document it, since `serve` (live mode, Task 20/13a) never calls `run_batch`.

- [ ] **Step 5: Commit**

```bash
git add rebound/sim/batch.py tests/test_batch_smoke.py
git commit -m "feat: batch runner exercising duplicate-webhook rejection per scenario"
```

---

## Task 17: Metrics report (Markdown + JSON) — per-cause P/R, confusion matrix, false escalations

**Files:**
- Create: `rebound/sim/report.py`
- Test: `tests/test_report.py`

**Effort:** 004. Satisfies FR-6.4 in full (per-cause precision/recall, abstain rate, confusion matrix, false escalations — not just an aggregate accuracy number), FR-6.5, AC-1, AC-4.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
from rebound.sim.report import build_report


def _row(scenario_id, tags, truth, predicted, provenance, action, executed, error=None, mapped_from=None):
    return {
        "scenario_id": scenario_id, "tags": tags, "truth_cause": truth,
        "predicted_cause": predicted, "provenance": provenance, "mapped_from": mapped_from,
        "outcome": {"action": action, "executed": executed, "error": error},
        "policy_violation": False,
    }


def test_build_report_computes_confusion_matrix_and_per_cause_precision_recall():
    results = [
        _row("s1", ["synthetic", "heldout"], "insufficient_funds", "insufficient_funds", "rule",
             "charge_invoice", True, mapped_from="error_reason=insufficient_funds"),
        _row("s2", ["synthetic", "heldout"], "insufficient_funds", "bank_or_gateway_error", "llm",
             "charge_invoice", True),  # misclassified
        _row("s3", ["synthetic", "heldout"], "unknown", "unknown", "abstain", "escalate", False, "escalate"),
        {"scenario_id": "s1", "tags": ["replay_duplicate_check"], "truth_cause": "insufficient_funds",
         "predicted_cause": None, "provenance": None, "mapped_from": None, "outcome": None, "policy_violation": False},
    ]
    report = build_report(results)

    assert report["duplicates_rejected"] == 1
    assert report["double_charges"] == 0
    assert report["policy_violations"] == 0
    assert report["classifier"]["heldout_count"] == 3
    assert report["classifier"]["confusion_matrix"]["insufficient_funds->insufficient_funds"] == 1
    assert report["classifier"]["confusion_matrix"]["insufficient_funds->bank_or_gateway_error"] == 1
    # AC-3: the rule-classified, non-unknown cause must appear with its source field cited
    citations = {c["scenario_id"]: c for c in report["classification_citations"]}
    assert citations["s1"]["mapped_from"] == "error_reason=insufficient_funds"
    assert "s3" not in citations  # unknown causes are excluded — nothing to cite
    # confirm the report is actually JSON-serializable (this is what broke before the fix:
    # a tuple-keyed confusion matrix crashes json.dumps in cmd_demo)
    import json
    json.dumps(report)
    pr = report["classifier"]["per_cause"]["insufficient_funds"]
    assert pr["recall"] == 0.5  # 1 of 2 actual insufficient_funds correctly found
    assert pr["precision"] == 1.0  # every prediction of insufficient_funds was correct


def test_build_report_flags_double_charge_as_violation():
    results = [
        _row("s1", ["replay_duplicate_check"], "insufficient_funds", "insufficient_funds", "rule",
             "charge_invoice", True),
    ]
    report = build_report(results)
    assert report["double_charges"] == 1


def test_build_report_counts_false_escalations():
    results = [
        # ground truth says this cause is normally auto-recoverable (charge_invoice permitted),
        # but the system escalated it -> false escalation
        _row("s1", ["synthetic", "heldout"], "insufficient_funds", "insufficient_funds", "rule",
             "escalate", False, "escalate"),
    ]
    report = build_report(results, permitted_action_by_cause={"insufficient_funds": "charge_invoice"})
    assert report["false_escalations"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# rebound/sim/report.py
from __future__ import annotations
from collections import defaultdict

# Ground-truth "expected permitted action" per cause, used only to compute false
# escalations (requirements FR-6.4) — mirrors the planner's default table (Task 9)
# but kept separate and explicit here since the report must judge the pipeline's
# choices against an independent expectation, not re-import the code under test.
_DEFAULT_PERMITTED_ACTION = {
    "insufficient_funds": "charge_invoice",
    "instrument_expired_or_blocked": "payment_link",
    "authentication_failed": "nudge",
    "bank_or_gateway_error": "charge_invoice",
    "mandate_not_active": "payment_link",
    "limit_exceeded": "payment_link",
    "unknown": "escalate",
}


def build_report(results: list[dict], permitted_action_by_cause: dict | None = None) -> dict:
    permitted = permitted_action_by_cause or _DEFAULT_PERMITTED_ACTION

    duplicates_rejected = sum(
        1 for r in results if "replay_duplicate_check" in r["tags"] and r["outcome"] is None
    )
    double_charges = sum(
        1 for r in results
        if "replay_duplicate_check" in r["tags"] and r["outcome"] is not None and r["outcome"].get("executed")
    )
    policy_violations = sum(1 for r in results if r.get("policy_violation"))

    per_cause_outcomes: dict[str, dict] = defaultdict(lambda: {"allowed": 0, "blocked": 0, "escalated": 0})
    false_escalations = 0
    exceptions = []
    for r in results:
        if "replay_duplicate_check" in r["tags"]:
            continue
        cause = r["truth_cause"]
        outcome = r["outcome"]
        if outcome is None:
            continue
        if outcome.get("executed"):
            per_cause_outcomes[cause]["allowed"] += 1
        elif outcome.get("action") == "escalate":
            per_cause_outcomes[cause]["escalated"] += 1
            exceptions.append({"scenario_id": r["scenario_id"], "truth_cause": cause, "reason": outcome["error"]})
            if permitted.get(cause) not in (None, "escalate"):
                false_escalations += 1  # ground truth had a real permitted action; we escalated anyway
        else:
            per_cause_outcomes[cause]["blocked"] += 1

    # --- classifier metrics, held-out set only (FR-6.2, FR-6.4) ---
    heldout = [r for r in results if "heldout" in r["tags"]]
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    for r in heldout:
        if r["predicted_cause"] is not None:
            confusion[(r["truth_cause"], r["predicted_cause"])] += 1

    causes = sorted({r["truth_cause"] for r in heldout} | {r["predicted_cause"] for r in heldout if r["predicted_cause"]})
    per_cause_pr: dict[str, dict] = {}
    for cause in causes:
        tp = confusion.get((cause, cause), 0)
        actual_total = sum(v for (t, _p), v in confusion.items() if t == cause)
        predicted_total = sum(v for (_t, p), v in confusion.items() if p == cause)
        per_cause_pr[cause] = {
            "precision": (tp / predicted_total) if predicted_total else None,
            "recall": (tp / actual_total) if actual_total else None,
        }

    correct = sum(1 for r in heldout if r.get("predicted_cause") == r["truth_cause"])
    abstained = sum(1 for r in heldout if r.get("provenance") == "abstain")

    # AC-3: every non-unknown classification in the report must cite the documented
    # field it mapped from. Collected across the WHOLE batch (not just held-out) since
    # AC-3 doesn't scope itself to held-out — it's about the report being traceable.
    classification_citations = [
        {"scenario_id": r["scenario_id"], "cause": r["predicted_cause"],
         "provenance": r["provenance"], "mapped_from": r.get("mapped_from")}
        for r in results
        if "replay_duplicate_check" not in r["tags"]
        and r.get("predicted_cause") not in (None, "unknown")
    ]

    return {
        "duplicates_rejected": duplicates_rejected,
        "double_charges": double_charges,
        "policy_violations": policy_violations,
        "false_escalations": false_escalations,
        "per_cause": dict(per_cause_outcomes),
        "classifier": {
            "heldout_count": len(heldout),
            "accuracy": (correct / len(heldout)) if heldout else None,
            "abstain_rate": (abstained / len(heldout)) if heldout else None,
            # JSON object keys must be strings — "truth->predicted" instead of a (truth, predicted)
            # tuple, so `json.dumps(report)` in the CLI (Task 20) doesn't raise TypeError.
            "confusion_matrix": {f"{t}->{p}": v for (t, p), v in confusion.items()},
            "per_cause": per_cause_pr,
        },
        "exceptions": exceptions,
        "classification_citations": classification_citations,
    }


def render_markdown(report: dict) -> str:
    lines = ["# Rebound batch report", ""]
    lines.append(f"- Duplicates rejected: **{report['duplicates_rejected']}**")
    lines.append(f"- Double charges: **{report['double_charges']}** (must be 0)")
    lines.append(f"- Policy violations: **{report['policy_violations']}** (must be 0)")
    lines.append(f"- False escalations: **{report['false_escalations']}**")
    lines.append("")
    lines.append("## Per-cause outcomes (policy outcome, not money recovered)")
    lines.append("| Cause | Allowed | Blocked | Escalated |")
    lines.append("|---|---|---|---|")
    for cause, counts in report["per_cause"].items():
        lines.append(f"| {cause} | {counts['allowed']} | {counts['blocked']} | {counts['escalated']} |")
    lines.append("")
    c = report["classifier"]
    lines.append(f"## Classifier (held-out set, n={c['heldout_count']})")
    lines.append(f"- Overall accuracy: {c['accuracy']} · Abstain rate: {c['abstain_rate']}")
    lines.append("")
    lines.append("| Cause | Precision | Recall |")
    lines.append("|---|---|---|")
    for cause, pr in c["per_cause"].items():
        lines.append(f"| {cause} | {pr['precision']} | {pr['recall']} |")
    lines.append("")
    lines.append("### Confusion matrix (truth → predicted : count)")
    for key, count in sorted(c["confusion_matrix"].items()):
        lines.append(f"- {key.replace('->', ' → ')}: {count}")
    lines.append("")
    lines.append("## Exceptions")
    for e in report["exceptions"]:
        lines.append(f"- `{e['scenario_id']}` ({e['truth_cause']}): {e['reason']}")
    lines.append("")
    lines.append("## Classification citations (AC-3 — every non-unknown cause traced to its source field)")
    for cite in report["classification_citations"]:
        source = cite["mapped_from"] or f"LLM ({cite['provenance']})"
        lines.append(f"- `{cite['scenario_id']}` → {cite['cause']}: {source}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add rebound/sim/report.py tests/test_report.py
git commit -m "feat: batch metrics report with per-cause P/R, confusion matrix, false escalations"
```

---

## Task 18: HTML report renderer (Amendment A, S2)

**Files:**
- Create: `rebound/sim/report_html.py`
- Modify: `tests/test_report.py` (add HTML render test)

**Effort:** 004, scheduled by `docs/idea-evaluation.md` sharpener S2 → FR-6.6.

- [ ] **Step 1: Write the failing test** (append to `tests/test_report.py`)

```python
from rebound.sim.report_html import render_html


def test_render_html_is_self_contained_and_includes_key_sections():
    report = {
        "duplicates_rejected": 1, "double_charges": 0, "policy_violations": 0,
        "per_cause": {"insufficient_funds": {"allowed": 5, "blocked": 0, "escalated": 1}},
        "classifier": {"heldout_count": 20, "accuracy": 0.9, "abstain_rate": 0.1},
        "exceptions": [{"scenario_id": "s1", "truth_cause": "unknown", "reason": "escalate"}],
    }
    audit_records = [
        {"seq": 0, "stage": "event_received", "subscription_id": "sub_1", "hash": "aaaa1111" * 8},
        {"seq": 1, "stage": "duplicate_rejected", "subscription_id": "sub_1", "hash": "bbbb2222" * 8},
    ]
    html = render_html(report, audit_records=audit_records)
    assert "<style>" in html  # inline CSS, no external assets
    assert "<script" not in html.lower()  # no external JS dependency needed
    assert "insufficient_funds" in html
    assert "Where AI was" in html
    assert "duplicate_rejected" in html  # FR-6.6 / S2: the audit chain view
    assert "aaaa1111" in html  # hashes shown (truncated is fine), so tampering is visibly checkable


def test_render_html_works_with_no_audit_records():
    report = {
        "duplicates_rejected": 0, "double_charges": 0, "policy_violations": 0,
        "per_cause": {}, "classifier": {"heldout_count": 0, "accuracy": None, "abstain_rate": None},
        "exceptions": [],
    }
    html = render_html(report, audit_records=[])
    assert "<style>" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation** — a single self-contained HTML string, no external files, no server. `audit_records` is a list of dicts as read from the audit log JSONL (Task 3); the CLI (Task 20) is responsible for reading `.rebound_data/audit.jsonl` and passing the parsed records in.

```python
# rebound/sim/report_html.py
def render_html(report: dict, audit_records: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{cause}</td><td>{c['allowed']}</td><td>{c['blocked']}</td><td>{c['escalated']}</td></tr>"
        for cause, c in report["per_cause"].items()
    )
    exceptions = "".join(
        f"<li><code>{e['scenario_id']}</code> ({e['truth_cause']}): {e['reason']}</li>"
        for e in report["exceptions"]
    )
    audit_rows = "".join(
        f"<tr><td>{r['seq']}</td><td>{r['stage']}</td><td>{r.get('subscription_id', '')}</td>"
        f"<td><code>{r['hash'][:12]}…</code></td></tr>"
        for r in audit_records
    )
    def _citation_line(cite: dict) -> str:
        source = cite["mapped_from"] or f"LLM ({cite['provenance']})"
        return f"<li><code>{cite['scenario_id']}</code> → {cite['cause']}: {source}</li>"

    citations = "".join(_citation_line(cite) for cite in report.get("classification_citations", []))
    c = report["classifier"]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Rebound batch report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; color: #1a1a1a; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }}
.metric {{ font-size: 1.4rem; font-weight: bold; }}
.zero-required {{ color: #0a7d2c; }}
section {{ margin-bottom: 2rem; }}
</style></head>
<body>
<h1>Rebound — batch report</h1>
<section>
  <p>Duplicates rejected: <span class="metric">{report['duplicates_rejected']}</span></p>
  <p>Double charges (must be 0): <span class="metric zero-required">{report['double_charges']}</span></p>
  <p>Policy violations (must be 0): <span class="metric zero-required">{report['policy_violations']}</span></p>
</section>
<section>
  <h2>Per-cause outcomes (policy outcome, not money recovered)</h2>
  <table><tr><th>Cause</th><th>Allowed</th><th>Blocked</th><th>Escalated</th></tr>{rows}</table>
</section>
<section>
  <h2>Classifier (held-out, n={c['heldout_count']})</h2>
  <p>Accuracy: {c['accuracy']} · Abstain rate: {c['abstain_rate']}</p>
</section>
<section>
  <h2>Exceptions</h2>
  <ul>{exceptions}</ul>
</section>
<section>
  <h2>Classification citations (every non-unknown cause traced to its source field)</h2>
  <ul>{citations}</ul>
</section>
<section>
  <h2>Audit chain (tamper-evident — run <code>rebound verify-audit</code> to check)</h2>
  <table><tr><th>Seq</th><th>Stage</th><th>Subscription</th><th>Hash</th></tr>{audit_rows}</table>
</section>
<section>
  <h2>Where AI was and was not used</h2>
  <p>Documented-field classification: rules only. Ambiguous-text classification: LLM, with confidence + abstain.
     Choosing and authorising every action: deterministic code only. Nudge text: LLM, logged, never sent.</p>
</section>
</body></html>"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report.py -v`
Expected: 5 passed (3 from Task 17 + 2 new here)

- [ ] **Step 5: Commit**

```bash
git add rebound/sim/report_html.py tests/test_report.py
git commit -m "feat: self-contained HTML batch report (Amendment A / S2)"
```

---

## Task 19: `verify_audit` standalone check

**Files:**
- Modify: `rebound/audit/log.py` (already has `verify()`/`first_break()` from Task 3 — no change needed)
- Create: `tests/test_verify_audit_cli.py`

**Effort:** 001. Satisfies AC-5 as a CLI-reachable command (wired fully in Task 20).

- [ ] **Step 1: Write the failing test** (tests the function directly; CLI wiring tested in Task 20)

```python
# tests/test_verify_audit_cli.py
from rebound.audit.log import AuditLog


def test_first_break_reports_correct_seq(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append("event_received", {"a": 1}, 0.0)
    log.append("classified", {"a": 2}, 1.0)
    log.append("action_executed", {"a": 3}, 2.0)

    import json
    lines = path.read_text().splitlines()
    rec = json.loads(lines[1])
    rec["payload"]["a"] = 999
    lines[1] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    log2 = AuditLog(path)
    assert log2.first_break() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify_audit_cli.py -v`
Expected: Should already PASS if `first_break()` from Task 3 is correct — this task is a **regression check**, not new code. If it fails, fix `first_break()` in `rebound/audit/log.py`.

- [ ] **Step 3: N/A** (no new implementation expected)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_verify_audit_cli.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit** (only if Step 2 required a fix)

```bash
git add rebound/audit/log.py tests/test_verify_audit_cli.py
git commit -m "test: verify audit first_break() pinpoints the tampered record"
```

---

## Task 20: CLI (`demo`, `serve`, `verify-audit`, `report`)

**Files:**
- Create: `rebound/cli.py`
- Test: manual run per step (CLI entry points are thin; covered by the module tests above)

**Effort:** 001/004 glue. Satisfies FR-8.1 (one command), Makefile targets from Task 1.

- [ ] **Step 1: Write `rebound/cli.py`**

```python
# rebound/cli.py
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.policy.gate import PolicyGate
from rebound.sim.clock import SimClock, RealClock
from rebound.sim.scenarios import generate_scenarios
from rebound.sim.batch import run_batch
from rebound.sim.report import build_report, render_markdown
from rebound.sim.report_html import render_html
from rebound.pipeline import PipelineContext

DATA_DIR = Path(".rebound_data")


def _make_context(clock) -> PipelineContext:
    DATA_DIR.mkdir(exist_ok=True)
    executor_client = None
    llm_client = None
    if os.environ.get("RAZORPAY_KEY_ID"):
        import razorpay
        executor_client = razorpay.Client(auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"]))
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        llm_client = anthropic.Anthropic()
    return PipelineContext(
        store=EventStore(DATA_DIR / "events.db"),
        audit=AuditLog(DATA_DIR / "audit.jsonl"),
        gate=PolicyGate.from_yaml(Path(__file__).parent / "policy" / "policy.yaml"),
        executor_client=executor_client,
        llm_client=llm_client,
        clock=clock,
        llm_cache_dir=str(DATA_DIR / "llm_cache"),
    )


def cmd_demo(args: argparse.Namespace) -> None:
    ctx = _make_context(SimClock(0.0))
    recorded_dir = Path("fixtures/recorded")
    scenarios = generate_scenarios(seed=42, n=60,
                                    recorded_dir=recorded_dir if recorded_dir.exists() else None)
    results = run_batch(ctx, scenarios)  # results already carry predicted_cause/provenance (Task 16)
    report = build_report(results)
    Path("report.json").write_text(json.dumps(report, indent=2))
    Path("report.md").write_text(render_markdown(report))
    print(render_markdown(report))
    print(f"\nOK: audit chain valid = {ctx.audit.verify()}")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    from rebound.ingest.webhook import create_app
    ctx = _make_context(RealClock())  # live mode: real Razorpay/Anthropic clients if keys are set
    app = create_app(db_path=DATA_DIR / "events.db", ctx=ctx)
    uvicorn.run(app, host="0.0.0.0", port=args.port)


def cmd_verify_audit(args: argparse.Namespace) -> None:
    log = AuditLog(DATA_DIR / "audit.jsonl")
    if log.verify():
        print("OK: audit chain is valid")
        sys.exit(0)
    else:
        print(f"FAIL: chain broken at seq {log.first_break()}")
        sys.exit(1)


def _read_audit_records() -> list[dict]:
    path = DATA_DIR / "audit.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def cmd_report(args: argparse.Namespace) -> None:
    report = json.loads(Path("report.json").read_text())
    if args.html:
        Path("report.html").write_text(render_html(report, audit_records=_read_audit_records()))
        print("wrote report.html")
    else:
        print(render_markdown(report))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="rebound")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo").set_defaults(func=cmd_demo)

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=cmd_serve)

    sub.add_parser("verify-audit").set_defaults(func=cmd_verify_audit)

    p_report = sub.add_parser("report")
    p_report.add_argument("--html", action="store_true")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it end-to-end**

Run: `cd "H:/augsepthacks/RAZORPAY AI" && uv pip install -e . && python -m rebound.cli demo`
Expected: prints a Markdown report; `report.json` and `report.md` created; last line `OK: audit chain valid = True`.

- [ ] **Step 3: Run `verify-audit`, then tamper and re-run**

Run: `python -m rebound.cli verify-audit`
Expected: `OK: audit chain is valid`, exit 0.

Then: manually edit one character inside `.rebound_data/audit.jsonl`, re-run the same command.
Expected: `FAIL: chain broken at seq N`, exit 1. Restore the file afterward (`git checkout` won't help since it's git-ignored — just re-run `demo` to regenerate it).

- [ ] **Step 4: Commit**

```bash
git add rebound/cli.py
git commit -m "feat: CLI — demo, serve, verify-audit, report"
```

---

## Task 21: Install a webhook tunnel and stand up `serve` against Razorpay test mode

**Files:** none (infra + manual verification)

**Effort:** 005 (hour-zero-capture), prerequisite half. **Blocked until Task 0 Step 1 (`.env`) is satisfied.**

- [ ] **Step 1: Install a tunnel** — per Task 0 Step 4's decision (e.g. `winget install ngrok.ngrok`, then `ngrok config add-authtoken <token>`).

- [ ] **Step 2: Start the server and tunnel**

Run (two terminals): `python -m rebound.cli serve --port 8000` and `ngrok http 8000`.
Expected: ngrok prints a public `https://*.ngrok-free.app` URL.

- [ ] **Step 3: Register the webhook in the Razorpay Dashboard (test mode)**

Settings → Webhooks → add the ngrok URL + `/webhook`, secret = `RAZORPAY_WEBHOOK_SECRET` from `.env`, select events: `payment.failed`, `subscription.pending`, `subscription.halted`, `subscription.charged`, `token.paused`, `token.cancelled`, `token.rejected`.

- [ ] **Step 4: Send a test webhook from the dashboard's "Test Webhook" button**

Expected: server logs `200`/`ok`; `.rebound_data/events.db` has one new row (`sqlite3 .rebound_data/events.db "select * from events;"`). Because `cmd_serve` now wires a real `PipelineContext` (Task 20) through the adapter (Task 13a), this event is also classified and gated for real — watch the audit log (`.rebound_data/audit.jsonl`) grow by several records, not just the event store. If the cause resolves to something other than `escalate`/`unknown` and a real Razorpay client is configured, the executor will attempt a live test-mode API call using the placeholder `invoice_id` noted in Task 13a — expect it to fail against the real API at this stage; that failure, and fixing it with a real invoice lookup, is exactly Task 22's job, not a sign this step is broken.

- [ ] **Step 5: Record in `FAILURES.md`**

Append an entry noting the tunnel tool chosen, any signature-verification mismatch encountered (a common one: Razorpay signs the *raw* body — if a proxy or framework middleware re-serializes JSON before your handler sees it, the signature check fails; `webhook.py` in Task 13 reads `request.body()` raw, which avoids this, but confirm it live) and how it was resolved.

- [ ] **Step 6: Commit** (only if any code changed to fix a real issue found here)

```bash
git add rebound/ingest/webhook.py FAILURES.md
git commit -m "fix: <whatever the live signature/tunnel issue actually was>"
```

---

## Task 22: Hour-zero real-payload capture (grounds the taxonomy)

**Files:**
- Create: `fixtures/recorded/*.json` (≥10 files per Amendment A / S3)
- Modify: `fixtures/recorded/README.md`

**Effort:** 005. **This is the single most important task in the plan** — it is the LLM council's "one thing to do first" and the hackathon-idea-evaluator's S3 sharpener, both. Do not skip or defer it past the earliest point `.env` and Task 21 are ready.

- [ ] **Step 0: Open the effort tracker**

Create `aidlc-docs/efforts/005-hour-zero-capture/effort-state.md` (same shape as prior efforts). Note it was `blocked` until `.env` existed; mark `in-progress` now. Units: Plan/Subscription setup, real payload capture (this task), real invoice-ID lookup fix (Step 9 below).

- [ ] **Step 1: Create one test-mode Plan and Subscription** via the Razorpay Dashboard or API (per `aidlc-docs/inception/01-requirements.md` §8, `docs/hackathon-spec.md`).

- [ ] **Step 2: Drive it to failure using the documented test-card table** (`https://razorpay.com/docs/payments/payments/test-card-details/`) — capture one payload per row for: insufficient funds, card expired/declined, authentication failed, payment timeout, gateway technical error. That is 5 of the ≥10 required by FR-6.1a.

- [ ] **Step 3: Capture the raw `payment.failed` JSON for each**, using the `serve` receiver from Task 21 (it logs the full payload to the event store) or the Dashboard's webhook logs. Save each as `fixtures/recorded/card_<reason>.json` in the `{"event_id", "event", "payload"}` envelope shape from Task 14.

- [ ] **Step 4: Use "Charge this now" to fail the subscription 4× and capture `subscription.halted`** — save as `fixtures/recorded/subscription_halted.json`. This confirms empirically whether the failure path compresses to minutes (per the earlier fact-check) — record the actual elapsed time in `FAILURES.md` either way.

- [ ] **Step 5: Attempt a UPI failure via `failure@razorpay`** and capture it — save as `fixtures/recorded/upi_generic_failure.json`, explicitly labelled generic (this is the "cause 7 = unknown" evidence for the report's honesty disclosure, not a new distinguishable cause).

- [ ] **Step 6: Strip secrets** from every captured file (API keys never appear in webhook payloads, but double-check `notes`/`description` fields don't leak anything project-specific before committing).

- [ ] **Step 7: Update `fixtures/recorded/README.md`** listing each file, what it demonstrates, and its capture date — this doubles as evidence for FR-6.1a's "recorded vs. synthetic" disclosure.

- [ ] **Step 8: Re-run the taxonomy tests against real data**

Run: `python -c "
import json
from pathlib import Path
from rebound.classify.rules import classify_by_rules
from rebound.models import PaymentFailure
for f in Path('fixtures/recorded').glob('card_*.json'):
    env = json.loads(f.read_text())
    pf = PaymentFailure(**env['payload']['payment']['entity'])
    print(f.name, '->', classify_by_rules(pf))
"`

Expected: each file maps to the cause its filename claims. If any maps to `None` (falls through to LLM/unknown), that is a real finding — record it in `FAILURES.md`: which documented `error_reason` value actually appeared vs. what was expected, and update `rebound/classify/taxonomy.py`'s `REASON_TO_CAUSE` map accordingly (this is exactly the kind of "what broke and how you got out" the submission is judged on).

- [ ] **Step 9: Resolve the real invoice-ID lookup** (closes the limitation flagged in Task 13a)

Using the real Razorpay client against the halted subscription from Step 4, find the actual pending invoice: `client.invoice.all({"subscription_id": sub_id})` and inspect the response shape (save one anonymized example to `fixtures/recorded/invoice_list_sample.json`). Replace **only** `_resolve_invoice_id`'s placeholder body in `rebound/ingest/adapter.py` with the real lookup — its signature, and both call sites in `event_to_pipeline_inputs`, were already set up for this in Task 13a, so nothing else changes. Add two new tests in `tests/test_adapter.py` using a fake client that returns a canned invoice list — one exercising the `payment.failed` branch, one exercising `subscription.halted` — asserting the real ID is used when a client is provided and the placeholder is still used when `client=None`.

Run: `pytest tests/test_adapter.py -v`
Expected: 5 passed (3 from Task 13a + 2 new here).

- [ ] **Step 10: Re-run Step 4's live webhook test end to end** now that the invoice ID is real — confirm `charge_invoice` (if that's the planned action for the captured cause) actually succeeds against the real test-mode API, or document the real error if it still doesn't and fix from there. This is the live moment Task 25's video script depends on; do not treat it as done until it has actually executed successfully once outside a test.

- [ ] **Step 11: Commit**

```bash
git add fixtures/recorded/ FAILURES.md rebound/classify/taxonomy.py rebound/ingest/adapter.py tests/test_adapter.py
git commit -m "feat: capture real test-mode payloads grounding the taxonomy; resolve real invoice IDs (S3)"
```

---

## Task 23: Explicit scale-path documentation (Amendment A, S4)

**Files:**
- Modify: `README.md` (add a "Scaling this" section — content only, no new code per NFR-Scale's "no second implementation is built")

**Effort:** 006 (deliverables).

- [ ] **Step 1: Confirm the existing interfaces already support the swap** — `EventStoreProtocol` (Task 4) and the `Clock` protocol (Task 2) are the seams; no new file needed since design doc explicitly says "no second implementation is built."

- [ ] **Step 2: Write the README section** — save it to `docs/_readme_scaling_section.md` for now; **Task 24 Step 5a inserts this exact content into `README.md`** (Task 24 is the task that actually rewrites `README.md`; Task 26 never touches it — do not defer insertion to Task 26):

```markdown
## Scaling this

Built for a 24-hour demo (SQLite, in-process, synchronous). The seams for production scale
already exist:
- `EventStoreProtocol` (`rebound/ingest/store.py`) — swap SQLite for Postgres/DynamoDB behind
  the same `insert_if_new(event_id, ...) -> bool` contract; the `event_id` uniqueness constraint
  is what makes concurrent workers safe, with or without SQLite.
- The webhook receiver can hand off to a queue (SQS/Celery) instead of processing in-line;
  `Pipeline.process_failure` doesn't know or care who calls it.
- `Clock` swaps `SimClock` (batch/demo) for `RealClock` (production) with no other code change.
```

- [ ] **Step 3: Commit the draft**

```bash
git add docs/_readme_scaling_section.md
git commit -m "docs: draft scale-path section for README (Amendment A / S4)"
```

(No separate insertion commit — Task 24 Step 9's single README commit covers the actual insertion.)

---

## Task 24: README, architecture diagram, deliverables pass

**Files:**
- Modify: `README.md` (full rewrite of the project section, keeping the AI-DLC status table, **including Task 23's Scaling section — this is the only task that writes README.md, so it must land here**)
- Modify: `FAILURES.md` (final pass)
- Create: `docs/submission.md`

**Effort:** 006. Satisfies FR-8.1, FR-8.1a, FR-8.3, AC-6, and (via Step 5a) Amendment A / S4.

- [ ] **Step 0: Open the effort tracker**

Create `aidlc-docs/efforts/006-deliverables/effort-state.md`. Units: README/architecture/impact framing incl. scale-path section (this task, folding in Task 23's draft), video script (Task 25). State `in-progress`.

- [ ] **Step 1: Write the README first paragraph** — run it past AC-6 (must contain none of: taxonomy, dunning, AFA, NSF, hash-chained, authoriser):

> "When a Razorpay subscription payment fails four times in a row, Razorpay stops retrying and tells the merchant to charge the customer by hand. Rebound picks up from there: it reads *why* the payment failed straight from Razorpay's own records, picks a sensible next step for that reason, and checks every step against a rulebook the AI is not allowed to override. Every decision is written to a record nobody — including the AI — can quietly edit afterward."

- [ ] **Step 2: Embed the Mermaid architecture diagram** from `aidlc-docs/inception/02-application-design.md` §1 directly (GitHub renders Mermaid natively).

- [ ] **Step 3: Paste the latest `report.md` metrics table** (regenerate via `make demo` first — this must be the actual last run's output, not typed by hand).

- [ ] **Step 4: Add the per-merchant impact framing (FR-8.1a)** — e.g. "For a merchant with 10,000 active subscriptions at the industry-average 7.9% recurring-payment failure rate, roughly 790 subscriptions land in `halted` per month; under the batch's decline-mix, ~55% are auto-recoverable, ~25% are nudge-only (mandate re-approval), and ~20% require human escalation." (Numbers computed from the actual `report.json` per-cause split, not invented.)

- [ ] **Step 5: Add "where AI is / is not used"** table (from design doc §6) and link `docs/research-synthesis.md`, `docs/council-verdict.md`, `docs/idea-evaluation.md`, `aidlc-docs/`.

- [ ] **Step 5a: Insert Task 23's "Scaling this" section** — copy the content of `docs/_readme_scaling_section.md` (written in Task 23 Step 2) verbatim into `README.md`, after the "where AI is / is not used" section. Delete `docs/_readme_scaling_section.md` once it's inlined (it was scratch, not a deliverable). This is the actual fulfillment of Amendment A / S4 — Task 23 only drafted the text.

- [ ] **Step 6: Finalize `FAILURES.md`** — ensure the idempotency/duplicate-webhook entry (the engineered failure) and the real breakages from Tasks 21/22 are both present and dated.

- [ ] **Step 7: Write `docs/submission.md`** — draft answers for the buildathon form fields from `docs/hackathon-spec.md` §5 (Project Name/Title, Objectives, GitHub URL, pitch video link placeholder, Build Challenges & Technical Obstacles pulled from `FAILURES.md`) so the one-shot form is filled by copy-paste, not composed live under deadline pressure.

- [ ] **Step 8: Run the clean-clone dry run** (Executor's and Reviewer 1/4's flagged risk)

Run: `rm -rf /tmp/rebound_clean_clone && git clone "H:/augsepthacks/RAZORPAY AI" /tmp/rebound_clean_clone && cd /tmp/rebound_clean_clone && cp .env.example .env && # fill real test values into this copy only, never commit them` then `make install && make test && make demo`
Expected: every step succeeds with no reference to any path outside the clone. Fix anything that assumes `H:/augsepthacks/RAZORPAY AI` specifically.

- [ ] **Step 9: Commit**

```bash
git add README.md FAILURES.md docs/submission.md
git rm docs/_readme_scaling_section.md
git commit -m "docs: README architecture + metrics + impact framing + scale-path, submission draft"
git push origin main
```

---

## Task 25: 5-minute pitch video script (S1 live moment included)

**Files:**
- Create: `docs/video-script.md`

**Effort:** 006. Satisfies FR-8.2, Amendment A S1.

- [ ] **Step 1: Write a timed script** (target ≤5:00):

```markdown
# Video script (target 4:45)

0:00–0:30  Problem, plain language (the README first paragraph, said aloud)
0:30–1:15  LIVE: fail a real test-mode subscription in the Razorpay Dashboard, show
           `subscription.halted` land in `rebound serve`'s log, classified, gated, executed
           (Amendment A / S1 — the core value prop shown against real Razorpay, not fixtures)
1:15–1:45  LIVE: redeliver the same webhook event (Dashboard "resend" or curl replay) —
           show it rejected, zero money moved, one audit line
1:45–2:30  `make demo`: 60-scenario batch runs; open `report.html` — per-cause bars,
           duplicates/policy-violations = 0, classifier accuracy on held-out
2:30–3:00  One LLM abstain → escalated, shown in the exceptions list — "here's where I
           chose not to trust the AI"
3:00–3:30  `rebound verify-audit`, then tamper one byte, run again — chain breaks, exact seq shown
3:30–4:15  Architecture diagram walkthrough: "the LLM only ever writes a label or a sentence;
           this gate is the only code that can touch money"
4:15–4:45  What broke (pick the sharpest FAILURES.md entry, told as a 20-second story) + close
```

- [ ] **Step 2: Record in one take per the Executor's cut-scope guidance** — no editing budget was reserved; a single continuous take screen-recording the terminal/browser is acceptable and matches the "build quality, not production values" judging criterion.

- [ ] **Step 3: Commit the script (not the video — video is uploaded separately per the form)**

```bash
git add docs/video-script.md
git commit -m "docs: pitch video script"
git push origin main
```

---

## Task 26: Final AI-DLC closeout

**Files:**
- Modify: `aidlc-docs/registry.md`, `aidlc-docs/process-log.md`, `aidlc-docs/audit.md`
- Modify each `efforts/*/effort-state.md` to `complete`

**Effort:** all. This is bookkeeping, not code — closes the loop the user asked to be showcased.

- [ ] **Step 1: Mark each effort's `effort-state.md` `complete`** with a one-line summary of what shipped vs. planned (note any cut scope explicitly — e.g. if Task 21's tunnel never worked and the demo fell back to fixture-only, say so; that's the honest failure-recovery story, not a hidden gap).

- [ ] **Step 2: Rebuild `registry.md`** from the effort states (per its own "derived view" convention).

- [ ] **Step 3: Append the remaining `process-log.md` entries** for every task actually executed (tool used = mostly none — this is hand-written code per the plan, which is itself worth noting: "construction was executed directly, not via further LLM code generation, once the plan was approved").

- [ ] **Step 4: Final commit**

```bash
git add aidlc-docs/
git commit -m "chore: AI-DLC closeout — mark efforts complete, rebuild registry"
git push origin main
```

---

## Out of scope (explicitly, per requirements §3 and the council/rubric verdicts)

Do not build: Hinglish/voice nudges, any web UI beyond the static HTML report, real SMS/email/WhatsApp sending, retry-*timing* optimization, more than 7 causes, a standalone second package for the gate, ML training/fine-tuning, Postgres/queue infra (documented only, per S4).

**Declared but intentionally not enforced in this build:** `policy.yaml`'s `cooldown_seconds` per cause and a per-subscription contact cap for nudges (both named in FR-3.2) are present in the policy data but not read anywhere in `gate.py` — the gate currently evaluates hard stops and attempt counts only, not elapsed time since the last action. `Action.NOOP_WAIT` (FR-4e) is likewise defined in the model but never produced by the planner or permitted in any policy row. All three are real MVP cuts made for the 24-hour budget, not oversights — if there's spare time after Task 26, wiring `SubscriptionState.last_action_at` against `cooldown_seconds` in `gate.py` is the natural next increment, but it is not required for any acceptance criterion in `01-requirements.md` §9.
