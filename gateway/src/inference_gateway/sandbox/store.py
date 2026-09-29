"""Durable, metadata-only audit for bounded sandbox tasks."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SandboxTaskStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS sandbox_tasks "
                "(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, idempotency_key TEXT NOT NULL, payload TEXT NOT NULL, "
                "UNIQUE(tenant, idempotency_key))"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def by_idempotency_key(self, tenant: str, key: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM sandbox_tasks WHERE tenant = ? AND idempotency_key = ?", (tenant, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, task: dict, *, idempotency_key: str) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO sandbox_tasks(id, tenant, idempotency_key, payload) VALUES (?, ?, ?, ?)",
                (task["id"], task["tenant"], idempotency_key, json.dumps(task, sort_keys=True)),
            )

    def get(self, task_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM sandbox_tasks WHERE id = ?", (task_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_for_tenant(self, tenant: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM sandbox_tasks WHERE tenant = ? ORDER BY rowid", (tenant,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
