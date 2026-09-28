"""Durable local incident, plan, approval, guard, and audit storage."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path

from fastapi import HTTPException

from inference_gateway.remediation.models import (
    IncidentState,
    RemediationIncident,
    RemediationPlan,
    TimelineEvent,
)


class RemediationStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS remediation_incidents "
                "(id TEXT PRIMARY KEY, source_request_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS remediation_plans "
                "(id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS remediation_timeline "
                "(incident_id TEXT NOT NULL, sequence INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS remediation_guards "
                "(model TEXT PRIMARY KEY, last_action REAL NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS remediation_actions "
                "(model TEXT NOT NULL, occurred_at REAL NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save_incident(self, incident: RemediationIncident) -> RemediationIncident:
        with self._connect() as db:
            db.execute(
                "INSERT INTO remediation_incidents(id,source_request_id,payload) VALUES (?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (incident.id, incident.source_request_id, incident.model_dump_json()),
            )
        return incident

    def get_incident(self, incident_id: str) -> RemediationIncident:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM remediation_incidents WHERE id=?", (incident_id,)
            ).fetchone()
        if not row:
            raise HTTPException(404, "unknown remediation incident")
        return RemediationIncident.model_validate_json(row[0])

    def by_source_request(self, request_id: str) -> RemediationIncident | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM remediation_incidents WHERE source_request_id=?", (request_id,)
            ).fetchone()
        return RemediationIncident.model_validate_json(row[0]) if row else None

    def save_plan(self, plan: RemediationPlan) -> RemediationPlan:
        with self._connect() as db:
            db.execute(
                "INSERT INTO remediation_plans(id,incident_id,payload) VALUES (?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (plan.id, plan.incident_id, plan.model_dump_json()),
            )
        return plan

    def get_plan(self, plan_id: str) -> RemediationPlan:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM remediation_plans WHERE id=?", (plan_id,)).fetchone()
        if not row:
            raise HTTPException(404, "unknown remediation plan")
        return RemediationPlan.model_validate_json(row[0])

    def append(self, incident_id: str, event: TimelineEvent) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO remediation_timeline(incident_id,payload) VALUES (?,?)",
                (incident_id, event.model_dump_json()),
            )

    def timeline(self, incident_id: str) -> list[TimelineEvent]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM remediation_timeline WHERE incident_id=? ORDER BY sequence",
                (incident_id,),
            ).fetchall()
        return [TimelineEvent.model_validate_json(row[0]) for row in rows]

    def transition_incident(self, incident_id: str, state: IncidentState) -> RemediationIncident:
        incident = self.get_incident(incident_id)
        incident.state = state
        return self.save_incident(incident)

    @staticmethod
    def plan_hash(*, incident: RemediationIncident, weights: dict[str, int]) -> str:
        payload = {
            "incident_id": incident.id,
            "action": "ROLLBACK_CANARY_TO_STABLE",
            "model": incident.model,
            "release_plan_id": incident.release_plan_id,
            "expected_release_phase": incident.release_phase,
            "expected_weights": weights,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def reserve_action(
        self, model: str, *, cooldown_seconds: int = 30, max_actions: int = 2, window_seconds: int = 300
    ) -> tuple[bool, str]:
        now = time.time()
        with self.lock, self._connect() as db:
            row = db.execute(
                "SELECT last_action FROM remediation_guards WHERE model=?", (model,)
            ).fetchone()
            if row and now - float(row[0]) < cooldown_seconds:
                return False, "REMEDIATION_COOLDOWN"
            count = db.execute(
                "SELECT COUNT(*) FROM remediation_actions WHERE model=? AND occurred_at>=?",
                (model, now - window_seconds),
            ).fetchone()[0]
            if count >= max_actions:
                return False, "REMEDIATION_ACTION_BUDGET_EXHAUSTED"
            db.execute(
                "INSERT INTO remediation_guards(model,last_action) VALUES (?,?) "
                "ON CONFLICT(model) DO UPDATE SET last_action=excluded.last_action",
                (model, now),
            )
            db.execute("INSERT INTO remediation_actions(model,occurred_at) VALUES (?,?)", (model, now))
        return True, "RESERVED"
