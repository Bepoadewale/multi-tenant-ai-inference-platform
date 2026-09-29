"""Durable device registry for the narrow flagship edge adapter."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class EdgeStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, profile TEXT NOT NULL,
                    local_models TEXT NOT NULL, endpoint TEXT NOT NULL, network TEXT NOT NULL,
                    last_seen TEXT NOT NULL, telemetry_count INTEGER NOT NULL DEFAULT 0
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def register(self, device_id: str, tenant: str, profile: str, local_models: list[str], endpoint: str) -> dict:
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO devices(device_id, tenant, profile, local_models, endpoint, network, last_seen)
                   VALUES (?, ?, ?, ?, ?, 'ONLINE', ?)
                   ON CONFLICT(device_id) DO UPDATE SET tenant=excluded.tenant, profile=excluded.profile,
                   local_models=excluded.local_models, endpoint=excluded.endpoint, last_seen=excluded.last_seen""",
                (device_id, tenant, profile, json.dumps(sorted(local_models)), endpoint, now),
            )
        return self.get(device_id)  # type: ignore[return-value]

    def heartbeat(self, device_id: str, network: str, telemetry_count: int) -> dict | None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE devices SET network=?, telemetry_count=?, last_seen=? WHERE device_id=?",
                (network, telemetry_count, self._now(), device_id),
            )
        return self.get(device_id)

    def get(self, device_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT device_id, tenant, profile, local_models, endpoint, network, last_seen, telemetry_count "
                "FROM devices WHERE device_id=?", (device_id,)
            ).fetchone()
        if row is None:
            return None
        return {
            "device_id": row[0], "tenant": row[1], "profile": row[2],
            "local_models": json.loads(row[3]), "endpoint": row[4], "network": row[5],
            "last_seen": row[6], "telemetry_count": row[7],
            "hardware": "SIMULATED",
        }

    def list(self) -> list[dict]:
        with self._connect() as connection:
            ids = [row[0] for row in connection.execute("SELECT device_id FROM devices ORDER BY device_id")]
        return [device for device_id in ids if (device := self.get(device_id))]
