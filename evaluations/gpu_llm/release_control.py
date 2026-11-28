"""Create immutable, independently approved LLM deployment records.

This module does not start or stop vLLM. It prepares and verifies the exact release
inputs that a later, narrowly scoped EC2 deployment command must consume.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
_IMAGE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")


class ReleaseValidationError(ValueError):
    """Raised when a candidate or deployment plan is incomplete or unsafe."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def digest_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_sha256(name: str, value: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ReleaseValidationError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    model_id: str
    model_revision: str
    model_license: str
    model_artifact_sha256: str
    vllm_image: str
    runtime_config: dict[str, Any]
    deployment_alias: str
    runtime_config_sha256: str
    suite_id: str
    suite_sha256: str
    evaluation_report_sha256: str
    automatic_gate: str
    human_review_required: bool
    source_commit: str
    created_at: str

    @property
    def sha256(self) -> str:
        return digest_json(asdict(self))


def verify_manifest(manifest: ReleaseManifest) -> None:
    """Check the manifest's pins and catch edits after its creation."""
    if manifest.schema_version != 1:
        raise ReleaseValidationError("unsupported release manifest schema")
    if not _REVISION.fullmatch(manifest.model_revision):
        raise ReleaseValidationError("model revision must be a full 40-character commit SHA")
    if not _REVISION.fullmatch(manifest.source_commit):
        raise ReleaseValidationError("source commit must be a full 40-character commit SHA")
    if not manifest.model_id.strip() or not manifest.model_license.strip() or not manifest.suite_id.strip():
        raise ReleaseValidationError("model, license, and evaluation suite metadata are required")
    if manifest.deployment_alias not in {"champion", "candidate"}:
        raise ReleaseValidationError("deployment alias must be champion or candidate")
    if not _IMAGE.fullmatch(manifest.vllm_image):
        raise ReleaseValidationError("vLLM image must be pinned by SHA-256 digest")
    for name, value in (
        ("model_artifact_sha256", manifest.model_artifact_sha256),
        ("runtime_config_sha256", manifest.runtime_config_sha256),
        ("suite_sha256", manifest.suite_sha256),
        ("evaluation_report_sha256", manifest.evaluation_report_sha256),
    ):
        _require_sha256(name, value)
    if digest_json(manifest.runtime_config) != manifest.runtime_config_sha256:
        raise ReleaseValidationError("runtime configuration digest does not match contents")
    if manifest.runtime_config.get("tensor_parallel_size") != 1:
        raise ReleaseValidationError("single-L4 deployment requires tensor_parallel_size=1")
    if manifest.automatic_gate != "pass":
        raise ReleaseValidationError("candidate has not passed deterministic evaluation gates")


def create_manifest(
    report_path: str | Path,
    *,
    model_id: str,
    model_revision: str,
    model_license: str,
    model_artifact_sha256: str,
    vllm_image: str,
    runtime_config: dict[str, Any],
    source_commit: str,
    deployment_alias: str = "candidate",
) -> ReleaseManifest:
    """Bind a sanitized passing evaluation to a pinned model and serving runtime."""
    report_bytes = Path(report_path).read_bytes()
    report = json.loads(report_bytes)
    if report.get("schema_version") != 1:
        raise ReleaseValidationError("evaluation report schema_version must be 1")
    if report.get("model_revision") != model_revision:
        raise ReleaseValidationError("evaluation model revision does not match candidate")
    if report.get("automatic_gate") != "pass" or report.get("failed_count") != 0:
        raise ReleaseValidationError("candidate did not pass deterministic evaluation gates")
    if not _IMAGE.fullmatch(vllm_image):
        raise ReleaseValidationError("vLLM image must be pinned by SHA-256 digest")
    provenance = report.get("provenance", {})
    report_runtime_config = report.get("runtime_config")
    if report_runtime_config != runtime_config:
        raise ReleaseValidationError("evaluation runtime configuration does not match candidate")
    if provenance.get("source_commit") != source_commit:
        raise ReleaseValidationError("evaluation source commit does not match candidate")
    if provenance.get("model_artifact_sha256") != model_artifact_sha256:
        raise ReleaseValidationError("evaluation model artifact digest does not match candidate")
    if provenance.get("vllm_image") != vllm_image:
        raise ReleaseValidationError("evaluation vLLM image does not match candidate")
    if not _REVISION.fullmatch(model_revision):
        raise ReleaseValidationError("model revision must be a full 40-character commit SHA")
    if not _REVISION.fullmatch(source_commit):
        raise ReleaseValidationError("source commit must be a full 40-character commit SHA")
    if not model_id.strip() or not model_license.strip() or not source_commit.strip():
        raise ReleaseValidationError("model ID, license, and source commit are required")
    if deployment_alias not in {"champion", "candidate"}:
        raise ReleaseValidationError("deployment alias must be champion or candidate")
    for key in ("suite_sha256",):
        _require_sha256(key, str(report.get(key, "")))
    _require_sha256("model_artifact_sha256", model_artifact_sha256)

    config = json.loads(canonical_json(runtime_config))
    if not config:
        raise ReleaseValidationError("runtime configuration must not be empty")
    if config.get("tensor_parallel_size") != 1:
        raise ReleaseValidationError("single-L4 deployment requires tensor_parallel_size=1")
    config_digest = digest_json(config)
    if provenance.get("runtime_config_sha256") != config_digest:
        raise ReleaseValidationError("evaluation runtime configuration digest does not match candidate")
    return ReleaseManifest(
        schema_version=1,
        model_id=model_id,
        model_revision=model_revision,
        model_license=model_license,
        model_artifact_sha256=model_artifact_sha256,
        vllm_image=vllm_image,
        runtime_config=config,
        deployment_alias=deployment_alias,
        runtime_config_sha256=config_digest,
        suite_id=str(report.get("suite_id", "")),
        suite_sha256=str(report["suite_sha256"]),
        evaluation_report_sha256=hashlib.sha256(report_bytes).hexdigest(),
        automatic_gate="pass",
        human_review_required=bool(report.get("human_review_required", True)),
        source_commit=source_commit,
        created_at=datetime.now(UTC).isoformat(),
    )


@dataclass(frozen=True)
class ReleasePlan:
    plan_id: str
    environment: str
    requester: str
    champion_manifest_sha256: str
    candidate_manifest_sha256: str
    candidate_model_id: str
    candidate_model_revision: str
    vllm_image: str
    runtime_config_sha256: str
    evaluation_report_sha256: str
    plan_sha256: str
    status: str
    approved_by: str | None
    created_at: str


def _plan_payload(plan: ReleasePlan) -> dict[str, Any]:
    payload = asdict(plan)
    payload.pop("plan_sha256")
    payload.pop("status")
    payload.pop("approved_by")
    return payload


def create_plan(
    *,
    environment: str,
    requester: str,
    champion: ReleaseManifest,
    candidate: ReleaseManifest,
) -> ReleasePlan:
    verify_manifest(champion)
    verify_manifest(candidate)
    if not environment.strip() or not requester.strip():
        raise ReleaseValidationError("environment and requester are required")
    if candidate.automatic_gate != "pass":
        raise ReleaseValidationError("candidate is not eligible for release approval")
    if champion.model_id != candidate.model_id:
        raise ReleaseValidationError("champion and candidate must use the same model registry name")
    if champion.deployment_alias != "champion" or candidate.deployment_alias != "candidate":
        raise ReleaseValidationError("plan requires champion and candidate deployment aliases")
    if champion.sha256 == candidate.sha256:
        raise ReleaseValidationError("candidate manifest must differ from current champion")
    plan = ReleasePlan(
        plan_id=str(uuid4()),
        environment=environment.strip(),
        requester=requester.strip(),
        champion_manifest_sha256=champion.sha256,
        candidate_manifest_sha256=candidate.sha256,
        candidate_model_id=candidate.model_id,
        candidate_model_revision=candidate.model_revision,
        vllm_image=candidate.vllm_image,
        runtime_config_sha256=candidate.runtime_config_sha256,
        evaluation_report_sha256=candidate.evaluation_report_sha256,
        plan_sha256="",
        status="PENDING_APPROVAL",
        approved_by=None,
        created_at=datetime.now(UTC).isoformat(),
    )
    return ReleasePlan(**{**asdict(plan), "plan_sha256": digest_json(_plan_payload(plan))})


def verify_plan(plan: ReleasePlan) -> None:
    if digest_json(_plan_payload(plan)) != plan.plan_sha256:
        raise ReleaseValidationError("release plan digest does not match its contents")


def assert_not_stale(
    plan: ReleasePlan,
    *,
    current_champion: ReleaseManifest,
    current_candidate: ReleaseManifest,
) -> None:
    verify_plan(plan)
    if plan.champion_manifest_sha256 != current_champion.sha256:
        raise ReleaseValidationError("STALE_PLAN: champion manifest changed after planning")
    if plan.candidate_manifest_sha256 != current_candidate.sha256:
        raise ReleaseValidationError("STALE_PLAN: candidate manifest changed after planning")


class ReleaseApprovalStore:
    """Local SQLite journal for immutable plan records and independent approvals."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS llm_release_plans (
                plan_id TEXT PRIMARY KEY, plan_json TEXT NOT NULL,
                plan_sha256 TEXT NOT NULL, status TEXT NOT NULL,
                approved_by TEXT, approved_at TEXT)"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS llm_release_manifests (
                plan_id TEXT NOT NULL, deployment_alias TEXT NOT NULL,
                manifest_json TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,
                PRIMARY KEY (plan_id, deployment_alias))"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def save(
        self,
        plan: ReleasePlan,
        *,
        champion: ReleaseManifest,
        candidate: ReleaseManifest,
    ) -> ReleasePlan:
        verify_plan(plan)
        verify_manifest(champion)
        verify_manifest(candidate)
        if champion.sha256 != plan.champion_manifest_sha256:
            raise ReleaseValidationError("champion manifest does not match plan")
        if candidate.sha256 != plan.candidate_manifest_sha256:
            raise ReleaseValidationError("candidate manifest does not match plan")
        if plan.status != "PENDING_APPROVAL" or plan.approved_by is not None:
            raise ReleaseValidationError(
                "new release plans must be pending approval with no approver"
            )
        with self._connect() as db:
            db.execute(
                "INSERT INTO llm_release_plans VALUES (?, ?, ?, ?, ?, NULL)",
                (
                    plan.plan_id,
                    canonical_json(asdict(plan)).decode("utf-8"),
                    plan.plan_sha256,
                    plan.status,
                    plan.approved_by,
                ),
            )
            db.executemany(
                "INSERT INTO llm_release_manifests VALUES (?, ?, ?, ?)",
                [
                    (
                        plan.plan_id,
                        manifest.deployment_alias,
                        canonical_json(asdict(manifest)).decode("utf-8"),
                        manifest.sha256,
                    )
                    for manifest in (champion, candidate)
                ],
            )
        return plan

    def get_manifests(self, plan_id: str) -> tuple[ReleaseManifest, ReleaseManifest]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT deployment_alias, manifest_json, manifest_sha256 "
                "FROM llm_release_manifests WHERE plan_id = ? ORDER BY deployment_alias",
                (plan_id,),
            ).fetchall()
        manifests = {}
        for alias, raw_manifest, expected_digest in rows:
            manifest = ReleaseManifest(**json.loads(raw_manifest))
            verify_manifest(manifest)
            if manifest.sha256 != expected_digest:
                raise ReleaseValidationError("stored release manifest digest does not match contents")
            manifests[alias] = manifest
        try:
            return manifests["champion"], manifests["candidate"]
        except KeyError as error:
            raise ReleaseValidationError("release plan manifest evidence is incomplete") from error

    def get(self, plan_id: str) -> ReleasePlan:
        with self._connect() as db:
            row = db.execute(
                "SELECT plan_json, plan_sha256, status, approved_by FROM llm_release_plans WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
        if row is None:
            raise ReleaseValidationError("unknown release plan")
        payload = json.loads(row[0])
        plan = ReleasePlan(**{**payload, "plan_sha256": row[1], "status": row[2], "approved_by": row[3]})
        verify_plan(plan)
        return plan

    def approve(self, plan_id: str, approver: str) -> ReleasePlan:
        plan = self.get(plan_id)
        if not approver.strip() or approver.strip() == plan.requester:
            raise ReleaseValidationError("requester cannot approve; a different approver is required")
        if plan.status != "PENDING_APPROVAL":
            raise ReleaseValidationError("release plan is not pending approval")
        with self._connect() as db:
            changed = db.execute(
                "UPDATE llm_release_plans SET status = 'APPROVED', approved_by = ?, approved_at = ? "
                "WHERE plan_id = ? AND status = 'PENDING_APPROVAL'",
                (approver.strip(), datetime.now(UTC).isoformat(), plan_id),
            ).rowcount
        if changed != 1:
            raise ReleaseValidationError("STALE_PLAN: approval state changed concurrently")
        return self.get(plan_id)
