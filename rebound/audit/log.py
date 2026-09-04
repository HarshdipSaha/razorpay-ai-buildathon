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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _last_hash(self) -> str:
        lines = [l for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            return GENESIS_HASH
        return json.loads(lines[-1])["hash"]

    def _next_seq(self) -> int:
        lines = [l for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
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
        return self.first_break() is None

    def first_break(self) -> int | None:
        prev_hash = GENESIS_HASH
        for i, line in enumerate(self.path.read_text(encoding="utf-8").splitlines()):
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

    def read_all(self) -> list[dict]:
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
