"""Durable, metadata-only audit for delegated agent tool calls."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class AgentToolAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS agent_tool_audit "
                "(sequence INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def append(self, *, event: str, actor: str, tenant: str, tool: str, arguments: dict) -> None:
        payload = {
            "event": event,
            "actor": actor,
            "tenant": tenant,
            "tool": tool,
            "arguments_sha256": hashlib.sha256(
                json.dumps(arguments, sort_keys=True).encode()
            ).hexdigest(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        with self._connect() as db:
            db.execute("INSERT INTO agent_tool_audit(payload) VALUES (?)", (json.dumps(payload),))

    def list(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM agent_tool_audit ORDER BY sequence").fetchall()
        return [json.loads(row[0]) for row in rows]
