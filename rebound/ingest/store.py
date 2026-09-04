from __future__ import annotations
import json
import sqlite3
from pathlib import Path


class EventStore:
    """SQLite-backed idempotent event store. `INSERT OR IGNORE` on event_id is the dedupe."""

    def __init__(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
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
