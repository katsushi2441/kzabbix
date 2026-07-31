from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any


class IncidentStore:
    def __init__(self, path: str):
        self.path = path
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                evidence_json TEXT,
                report TEXT,
                error TEXT,
                email_sent INTEGER NOT NULL DEFAULT 0,
                blog_posted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def enqueue(self, incident_id: str, event_id: str, payload: dict[str, Any]) -> bool:
        now = self._now()
        with self._connect() as db:
            cur = db.execute(
                "INSERT OR IGNORE INTO incidents "
                "(incident_id,event_id,status,payload_json,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (incident_id, event_id, "queued", json.dumps(payload, ensure_ascii=False), now, now),
            )
        return cur.rowcount == 1

    def update(self, incident_id: str, **fields: Any) -> None:
        allowed = {"status", "evidence_json", "report", "error", "email_sent", "blog_posted"}
        values = {key: value for key, value in fields.items() if key in allowed}
        if not values:
            return
        values["updated_at"] = self._now()
        sql = ",".join(f"{key}=?" for key in values)
        with self._connect() as db:
            db.execute(f"UPDATE incidents SET {sql} WHERE incident_id=?", (*values.values(), incident_id))

    def get(self, incident_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        return dict(row) if row else None

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 200)),)
            ).fetchall()
        return [dict(row) for row in rows]
