"""SQLite persistence for tenant-bound developer integration profiles."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SelfServiceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS integration_profiles "
                "(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, idempotency_key TEXT NOT NULL, "
                "fingerprint TEXT NOT NULL, payload TEXT NOT NULL, "
                "UNIQUE(tenant, idempotency_key))"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def by_idempotency_key(self, tenant: str, key: str) -> tuple[str, dict] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT fingerprint, payload FROM integration_profiles "
                "WHERE tenant = ? AND idempotency_key = ?",
                (tenant, key),
            ).fetchone()
        return (str(row[0]), json.loads(row[1])) if row else None

    def save(self, profile: dict, *, idempotency_key: str, fingerprint: str) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO integration_profiles(id, tenant, idempotency_key, fingerprint, payload) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    profile["id"],
                    profile["tenant"],
                    idempotency_key,
                    fingerprint,
                    json.dumps(profile, sort_keys=True),
                ),
            )

    def get(self, profile_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM integration_profiles WHERE id = ?", (profile_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list_for_tenant(self, tenant: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM integration_profiles WHERE tenant = ? ORDER BY rowid", (tenant,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
