"""Durable release plans with approval and stale-plan protection."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException


@dataclass(frozen=True)
class ReleasePlan:
    id: str
    alias: str
    requester: str
    champion_version: str
    candidate_version: str
    candidate_digest: str
    canary_weight: int
    plan_hash: str
    status: str
    approved_by: str | None
    created_at: str


class ReleaseStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS release_plans (
                id TEXT PRIMARY KEY, alias TEXT NOT NULL, requester TEXT NOT NULL,
                champion_version TEXT NOT NULL, candidate_version TEXT NOT NULL,
                candidate_digest TEXT NOT NULL, canary_weight INTEGER NOT NULL,
                plan_hash TEXT NOT NULL, status TEXT NOT NULL, approved_by TEXT,
                created_at TEXT NOT NULL)"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    @staticmethod
    def _hash(payload: dict[str, str | int]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def create(
        self,
        *,
        alias: str,
        requester: str,
        champion_version: str,
        candidate_version: str,
        candidate_digest: str,
        canary_weight: int,
    ) -> ReleasePlan:
        if not 1 <= canary_weight < 100:
            raise HTTPException(422, "canary_weight must be between 1 and 99")
        payload = {
            "alias": alias,
            "champion_version": champion_version,
            "candidate_version": candidate_version,
            "candidate_digest": candidate_digest,
            "canary_weight": canary_weight,
        }
        plan = ReleasePlan(
            id=str(uuid4()),
            requester=requester,
            plan_hash=self._hash(payload),
            status="PENDING_APPROVAL",
            approved_by=None,
            created_at=datetime.now(UTC).isoformat(),
            **payload,
        )
        with self._connect() as db:
            db.execute(
                "INSERT INTO release_plans VALUES (:id,:alias,:requester,:champion_version,"
                ":candidate_version,:candidate_digest,:canary_weight,:plan_hash,:status,"
                ":approved_by,:created_at)",
                asdict(plan),
            )
        return plan

    def get(self, plan_id: str) -> ReleasePlan:
        with self._connect() as db:
            row = db.execute("SELECT * FROM release_plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            raise HTTPException(404, "unknown release plan")
        return ReleasePlan(*row)

    def list(self) -> list[ReleasePlan]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM release_plans ORDER BY created_at DESC").fetchall()
        return [ReleasePlan(*row) for row in rows]

    def approve(self, plan_id: str, approver: str) -> ReleasePlan:
        plan = self.get(plan_id)
        if plan.requester == approver:
            raise HTTPException(403, "requester cannot approve their own release plan")
        if plan.status != "PENDING_APPROVAL":
            raise HTTPException(409, "release plan is not pending approval")
        with self._connect() as db:
            db.execute(
                "UPDATE release_plans SET status = 'APPROVED', approved_by = ? WHERE id = ?",
                (approver, plan_id),
            )
        return self.get(plan_id)

    def transition(self, plan_id: str, expected: str, target: str) -> ReleasePlan:
        with self._connect() as db:
            changed = db.execute(
                "UPDATE release_plans SET status = ? WHERE id = ? AND status = ?",
                (target, plan_id, expected),
            ).rowcount
        if changed != 1:
            raise HTTPException(409, "STALE_PLAN")
        return self.get(plan_id)
