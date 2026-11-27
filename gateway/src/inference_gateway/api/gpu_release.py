"""Authenticated planning and approval for sequential single-L4 model releases."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import mlflow
from fastapi import APIRouter, Depends, HTTPException
from inference_gateway.auth.admin import platform_admin, release_approver
from pydantic import BaseModel, ConfigDict, Field

from evaluations.gpu_llm.release_control import (
    ReleaseApprovalStore,
    ReleaseManifest,
    ReleaseValidationError,
    assert_not_stale,
    create_manifest,
    create_plan,
    digest_json,
    verify_manifest,
)

router = APIRouter(prefix="/gpu-release/v1", tags=["gpu-model-release"])
store = ReleaseApprovalStore(
    os.getenv("GPU_RELEASE_DB_PATH", "/tmp/gpu-release/release.sqlite")
)


class ManifestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

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

    def to_record(self) -> ReleaseManifest:
        manifest = ReleaseManifest(**self.model_dump())
        verify_manifest(manifest)
        return manifest


class CandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation_run_id: str = Field(min_length=1, max_length=64)
    model_id: str = Field(min_length=1, max_length=200)
    model_revision: str = Field(min_length=40, max_length=40)
    model_license: str = Field(min_length=1, max_length=100)
    model_artifact_sha256: str = Field(min_length=64, max_length=64)
    vllm_image: str = Field(min_length=1, max_length=300)
    runtime_config: dict[str, Any]
    source_commit: str = Field(min_length=40, max_length=40)


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: str = Field(min_length=1, max_length=100)
    champion: ManifestInput
    candidate: CandidateInput


def _mlflow_client() -> mlflow.MlflowClient:
    return mlflow.MlflowClient(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    )


def _candidate_from_evaluation(candidate: CandidateInput) -> ReleaseManifest:
    client = _mlflow_client()
    try:
        run = client.get_run(candidate.evaluation_run_id)
        if run.info.status != "FINISHED":
            raise HTTPException(409, "evaluation run is not finished")
        if run.data.tags.get("runtime") != "vllm":
            raise HTTPException(422, "evaluation run is not tagged as a vLLM run")
        if run.data.tags.get("content_policy") != "prompt_and_completion_text_excluded":
            raise HTTPException(422, "evaluation run does not meet the sanitized-report policy")
        if run.data.params.get("model_revision") != candidate.model_revision:
            raise HTTPException(409, "evaluation run model revision does not match candidate")
        if run.data.params.get("model_id") != candidate.model_id:
            raise HTTPException(409, "evaluation run model ID does not match candidate")
        if run.data.params.get("model") != candidate.runtime_config.get("served_model_name"):
            raise HTTPException(409, "evaluation served model name does not match candidate")
        for parameter, expected in (
            ("source_commit", candidate.source_commit),
            ("model_artifact_sha256", candidate.model_artifact_sha256),
            ("vllm_image", candidate.vllm_image),
        ):
            if run.data.params.get(parameter) != expected:
                raise HTTPException(409, f"evaluation {parameter} does not match candidate")
        if digest_json(candidate.runtime_config) != run.data.params.get("runtime_config_sha256"):
            raise HTTPException(409, "evaluation runtime configuration does not match candidate")
        if run.data.metrics.get("automatic_gate_pass") != 1.0:
            raise HTTPException(422, "candidate did not pass deterministic evaluation")
        if run.data.metrics.get("failed_count") != 0.0:
            raise HTTPException(422, "candidate evaluation contains failed cases")
        with tempfile.TemporaryDirectory(prefix="gpu-release-eval-") as temp_dir:
            report_path = Path(
                client.download_artifacts(
                    candidate.evaluation_run_id,
                    "evaluation/results.json",
                    dst_path=temp_dir,
                )
            )
            manifest = create_manifest(
                report_path,
                model_id=candidate.model_id,
                model_revision=candidate.model_revision,
                model_license=candidate.model_license,
                model_artifact_sha256=candidate.model_artifact_sha256,
                vllm_image=candidate.vllm_image,
                runtime_config=candidate.runtime_config,
                source_commit=candidate.source_commit,
                deployment_alias="candidate",
            )
        if manifest.suite_id != run.data.params.get("suite_id"):
            raise HTTPException(409, "evaluation suite ID does not match MLflow run")
        if manifest.suite_sha256 != run.data.params.get("suite_sha256"):
            raise HTTPException(409, "evaluation suite digest does not match MLflow run")
        if manifest.runtime_config_sha256 != run.data.params.get("runtime_config_sha256"):
            raise HTTPException(409, "evaluation runtime configuration does not match MLflow run")
        return manifest
    except HTTPException:
        raise
    except ReleaseValidationError:
        raise
    except (mlflow.exceptions.MlflowException, OSError, ValueError) as error:
        raise HTTPException(503, "evaluation evidence could not be verified") from error


@router.post("/plans")
def create_gpu_release_plan(
    request: PlanRequest,
    requester: str = Depends(platform_admin),
) -> dict[str, object]:
    try:
        champion = request.champion.to_record()
        if champion.deployment_alias != "champion":
            raise ReleaseValidationError("current champion manifest must use champion alias")
        candidate = _candidate_from_evaluation(request.candidate)
        plan = create_plan(
            environment=request.environment,
            requester=requester,
            champion=champion,
            candidate=candidate,
        )
        store.save(plan, champion=champion, candidate=candidate)
        return {"plan": plan, "champion": champion, "candidate": candidate}
    except ReleaseValidationError as error:
        raise HTTPException(422, str(error)) from error


@router.get("/plans/{plan_id}")
def get_gpu_release_plan(
    plan_id: str,
    requester: str = Depends(platform_admin),
) -> dict[str, object]:
    try:
        plan = store.get(plan_id)
        champion, candidate = store.get_manifests(plan_id)
        assert_not_stale(plan, current_champion=champion, current_candidate=candidate)
    except ReleaseValidationError as error:
        status = 404 if str(error) == "unknown release plan" else 409
        raise HTTPException(status, str(error)) from error
    return {"plan": plan, "champion": champion, "candidate": candidate}


@router.post("/plans/{plan_id}/approve")
def approve_gpu_release_plan(
    plan_id: str,
    approver: str = Depends(release_approver),
) -> dict[str, object]:
    try:
        plan = store.get(plan_id)
        champion, candidate = store.get_manifests(plan_id)
        assert_not_stale(plan, current_champion=champion, current_candidate=candidate)
        approved = store.approve(plan_id, approver)
    except ReleaseValidationError as error:
        status = 404 if str(error) == "unknown release plan" else 409
        raise HTTPException(status, str(error)) from error
    return {"plan": approved}
