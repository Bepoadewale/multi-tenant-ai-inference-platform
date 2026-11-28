import json
import shutil
from dataclasses import asdict
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inference_gateway.api import gpu_release
from inference_gateway.auth.admin import platform_admin, release_approver

from evaluations.gpu_llm.release_control import (
    ReleaseApprovalStore,
    ReleaseManifest,
    create_manifest,
    digest_json,
)

MODEL_REVISION = "a" * 40
MODEL_SHA = "b" * 64
IMAGE = "vllm/vllm-openai@sha256:" + "c" * 64
SOURCE_COMMIT = "1" * 40
RUNTIME_CONFIG = {
    "dtype": "bfloat16",
    "max_model_len": 8192,
    "max_num_seqs": 2,
    "max_num_batched_tokens": 8192,
    "gpu_memory_utilization": 0.85,
    "served_model_name": "gpu-default",
    "tensor_parallel_size": 1,
}


def _report(path, revision=MODEL_REVISION):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suite_id": "single-l4-qwen-smoke-v1",
                "suite_sha256": "d" * 64,
                "model": "gpu-default",
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "model_revision": revision,
                "automatic_gate": "pass",
                "human_review_required": True,
                "failed_count": 0,
                "runtime_config": RUNTIME_CONFIG,
                "provenance": {
                    "source_commit": SOURCE_COMMIT,
                    "model_artifact_sha256": MODEL_SHA,
                    "vllm_image": IMAGE,
                    "runtime_config_sha256": digest_json(RUNTIME_CONFIG),
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _manifest(path, alias, revision):
    return create_manifest(
        path,
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        model_revision=revision,
        model_license="Apache-2.0",
        model_artifact_sha256=MODEL_SHA,
        vllm_image=IMAGE,
        runtime_config=RUNTIME_CONFIG,
        source_commit=SOURCE_COMMIT,
        deployment_alias=alias,
    )


def _client(store):
    app = FastAPI()
    app.include_router(gpu_release.router)
    app.dependency_overrides[platform_admin] = lambda: "release-requester"
    app.dependency_overrides[release_approver] = lambda: "independent-approver"
    gpu_release.store = store
    return TestClient(app)


def test_plan_api_reads_verified_mlflow_evaluation_and_persists_manifests(tmp_path, monkeypatch):
    evaluation = _report(tmp_path / "results.json")
    champion = _manifest(_report(tmp_path / "champion.json", "e" * 40), "champion", "e" * 40)
    candidate = _manifest(evaluation, "candidate", MODEL_REVISION)
    run = SimpleNamespace(
        info=SimpleNamespace(status="FINISHED"),
        data=SimpleNamespace(
            tags={
                "runtime": "vllm",
                "content_policy": "prompt_and_completion_text_excluded",
            },
            params={
                "model_revision": MODEL_REVISION,
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "model": "gpu-default",
                "suite_id": "single-l4-qwen-smoke-v1",
                "suite_sha256": "d" * 64,
                "source_commit": SOURCE_COMMIT,
                "model_artifact_sha256": MODEL_SHA,
                "vllm_image": IMAGE,
                "runtime_config_sha256": digest_json(RUNTIME_CONFIG),
            },
            metrics={"automatic_gate_pass": 1.0, "failed_count": 0.0},
        ),
    )

    class FakeMlflowClient:
        def __init__(self, tracking_uri):
            assert tracking_uri == "http://mlflow:5000"

        def get_run(self, run_id):
            assert run_id == "run-123"
            return run

        def download_artifacts(self, run_id, artifact_path, dst_path):
            assert run_id == "run-123"
            assert artifact_path == "evaluation/results.json"
            destination = tmp_path / "downloaded-results.json"
            shutil.copyfile(evaluation, destination)
            return str(destination)

    monkeypatch.setattr(gpu_release.mlflow, "MlflowClient", FakeMlflowClient)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    store = ReleaseApprovalStore(tmp_path / "shared" / "release.sqlite")
    client = _client(store)
    response = client.post(
        "/gpu-release/v1/plans",
        json={
            "environment": "single-l4-lab",
            "champion": asdict(champion),
            "candidate": {
                "evaluation_run_id": "run-123",
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "model_revision": MODEL_REVISION,
                "model_license": "Apache-2.0",
                "model_artifact_sha256": MODEL_SHA,
                "vllm_image": IMAGE,
                "runtime_config": RUNTIME_CONFIG,
                "source_commit": "1" * 40,
            },
        },
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["plan"]["status"] == "PENDING_APPROVAL"
    assert result["candidate"]["evaluation_report_sha256"] == candidate.evaluation_report_sha256
    restored_champion, restored_candidate = store.get_manifests(result["plan"]["plan_id"])
    assert restored_champion.sha256 == champion.sha256
    assert restored_candidate.sha256 == ReleaseManifest(**result["candidate"]).sha256
    assert restored_candidate.evaluation_report_sha256 == candidate.evaluation_report_sha256

    approval = client.post(
        f"/gpu-release/v1/plans/{result['plan']['plan_id']}/approve"
    )
    assert approval.status_code == 200
    assert approval.json()["plan"]["approved_by"] == "independent-approver"


def test_plan_api_rejects_candidate_model_id_not_used_by_evaluation(tmp_path, monkeypatch):
    run = SimpleNamespace(
        info=SimpleNamespace(status="FINISHED"),
        data=SimpleNamespace(
            tags={
                "runtime": "vllm",
                "content_policy": "prompt_and_completion_text_excluded",
            },
            params={
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "model_revision": MODEL_REVISION,
            },
            metrics={},
        ),
    )

    class FakeMlflowClient:
        def __init__(self, tracking_uri):
            pass

        def get_run(self, run_id):
            return run

    monkeypatch.setattr(gpu_release.mlflow, "MlflowClient", FakeMlflowClient)
    from fastapi import HTTPException
    from inference_gateway.api.gpu_release import CandidateInput, _candidate_from_evaluation

    candidate = CandidateInput(
        evaluation_run_id="run-model-mismatch",
        model_id="some/other-model",
        model_revision=MODEL_REVISION,
        model_license="Apache-2.0",
        model_artifact_sha256=MODEL_SHA,
        vllm_image=IMAGE,
        runtime_config=RUNTIME_CONFIG,
        source_commit=SOURCE_COMMIT,
    )
    with pytest.raises(HTTPException, match="model ID") as error:
        _candidate_from_evaluation(candidate)
    assert error.value.status_code == 409


@pytest.mark.parametrize(
    "failed_run",
    [
        SimpleNamespace(
            info=SimpleNamespace(status="RUNNING"),
            data=SimpleNamespace(tags={}, params={}, metrics={}),
        ),
        SimpleNamespace(
            info=SimpleNamespace(status="FINISHED"),
            data=SimpleNamespace(
                tags={
                    "runtime": "vllm",
                    "content_policy": "prompt_and_completion_text_excluded",
                },
                params={"model_revision": MODEL_REVISION},
                metrics={"automatic_gate_pass": 0.0, "failed_count": 1.0},
            ),
        ),
    ],
)
def test_mlflow_candidate_gate_rejects_unfinished_or_failing_run(
    tmp_path, monkeypatch, failed_run
):
    class FakeMlflowClient:
        def __init__(self, tracking_uri):
            pass

        def get_run(self, run_id):
            return failed_run

    monkeypatch.setattr(gpu_release.mlflow, "MlflowClient", FakeMlflowClient)
    from fastapi import HTTPException
    from inference_gateway.api.gpu_release import CandidateInput, _candidate_from_evaluation

    candidate = CandidateInput(
        evaluation_run_id="run-fail",
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        model_revision=MODEL_REVISION,
        model_license="Apache-2.0",
        model_artifact_sha256=MODEL_SHA,
        vllm_image=IMAGE,
        runtime_config=RUNTIME_CONFIG,
        source_commit="1" * 40,
    )
    with pytest.raises(HTTPException):
        _candidate_from_evaluation(candidate)
