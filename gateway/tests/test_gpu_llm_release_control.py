import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from evaluations.gpu_llm.release_control import (
    ReleaseApprovalStore,
    ReleaseValidationError,
    assert_not_stale,
    create_manifest,
    create_plan,
    verify_plan,
)

MODEL_REVISION = "a" * 40
MODEL_SHA = "b" * 64
IMAGE = "vllm/vllm-openai@sha256:" + "c" * 64
RUNTIME_CONFIG = {
    "dtype": "bfloat16",
    "max_model_len": 8192,
    "max_num_seqs": 2,
    "tensor_parallel_size": 1,
}


def _report(path, *, gate="pass", failed=0, revision=MODEL_REVISION):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suite_id": "single-l4-qwen-smoke-v1",
                "suite_sha256": "d" * 64,
                "model_revision": revision,
                "automatic_gate": gate,
                "failed_count": failed,
                "human_review_required": True,
            }
        ),
        encoding="utf-8",
    )
    return path


def _manifest(
    path, *, revision=MODEL_REVISION, source_commit="1" * 40, alias="candidate"
):
    return create_manifest(
        path,
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        model_revision=revision,
        model_license="Apache-2.0",
        model_artifact_sha256=MODEL_SHA,
        vllm_image=IMAGE,
        runtime_config=RUNTIME_CONFIG,
        source_commit=source_commit,
        deployment_alias=alias,
    )


def test_manifest_binds_exact_model_runtime_and_sanitized_evaluation(tmp_path):
    report = _report(tmp_path / "report.json")
    manifest = _manifest(report)
    assert manifest.evaluation_report_sha256
    assert manifest.runtime_config_sha256
    assert manifest.model_revision == MODEL_REVISION
    assert manifest.vllm_image == IMAGE


def test_manifest_hashes_the_same_report_bytes_used_for_gate_validation(
    tmp_path, monkeypatch
):
    report = _report(tmp_path / "report.json")
    passing_bytes = report.read_bytes()
    original_read_bytes = Path.read_bytes
    reads = 0

    def read_then_simulate_concurrent_overwrite(path):
        nonlocal reads
        content = original_read_bytes(path)
        if path == report:
            reads += 1
            _report(report, gate="fail", failed=1)
        return content

    monkeypatch.setattr(Path, "read_bytes", read_then_simulate_concurrent_overwrite)
    manifest = _manifest(report)

    assert reads == 1
    assert manifest.evaluation_report_sha256 == hashlib.sha256(passing_bytes).hexdigest()
    assert json.loads(report.read_text(encoding="utf-8"))["automatic_gate"] == "fail"


@pytest.mark.parametrize(
    ("gate", "failed"), [("fail", 1), ("pass", 1)]
)
def test_failed_evaluation_cannot_become_a_candidate_manifest(tmp_path, gate, failed):
    report = _report(tmp_path / "report.json", gate=gate, failed=failed)
    with pytest.raises(ReleaseValidationError, match="deterministic evaluation"):
        _manifest(report)


def test_plan_digest_binds_candidate_champion_and_rejects_stale_inputs(tmp_path):
    champion = _manifest(
        _report(tmp_path / "champion.json", revision="e" * 40),
        revision="e" * 40,
        alias="champion",
    )
    candidate = _manifest(_report(tmp_path / "candidate.json"))
    plan = create_plan(
        environment="single-l4-lab",
        requester="release-requester",
        champion=champion,
        candidate=candidate,
    )
    verify_plan(plan)
    assert_not_stale(plan, current_champion=champion, current_candidate=candidate)

    with pytest.raises(ReleaseValidationError, match="STALE_PLAN: champion"):
        assert_not_stale(
            plan,
            current_champion=replace(champion, model_revision="f" * 40),
            current_candidate=candidate,
        )
    with pytest.raises(ReleaseValidationError, match="digest does not match"):
        verify_plan(replace(plan, vllm_image="vllm/vllm-openai:latest"))


def test_plan_requires_independent_approval_and_stores_audit_identity(tmp_path):
    champion = _manifest(
        _report(tmp_path / "champion.json", revision="e" * 40),
        revision="e" * 40,
        alias="champion",
    )
    candidate = _manifest(_report(tmp_path / "candidate.json"))
    store = ReleaseApprovalStore(tmp_path / "release" / "approvals.sqlite")
    pending = create_plan(
        environment="single-l4-lab",
        requester="release-requester",
        champion=champion,
        candidate=candidate,
    )

    with pytest.raises(ReleaseValidationError, match="pending approval with no approver"):
        store.save(replace(pending, status="APPROVED", approved_by=pending.requester))
    with pytest.raises(ReleaseValidationError, match="pending approval with no approver"):
        store.save(replace(pending, status="PENDING_APPROVAL", approved_by="other-reviewer"))

    plan = store.save(pending)

    with pytest.raises(ReleaseValidationError, match="different approver"):
        store.approve(plan.plan_id, "release-requester")
    approved = store.approve(plan.plan_id, "independent-reviewer")
    assert approved.status == "APPROVED"
    assert approved.approved_by == "independent-reviewer"
    verify_plan(approved)

    with pytest.raises(ReleaseValidationError, match="not pending approval"):
        store.approve(plan.plan_id, "second-reviewer")


def test_manifest_refuses_unpinned_images_and_multi_gpu_configuration(tmp_path):
    report = _report(tmp_path / "report.json")
    with pytest.raises(ReleaseValidationError, match="pinned by SHA-256"):
        create_manifest(
            report,
            model_id="Qwen/Qwen2.5-1.5B-Instruct",
            model_revision=MODEL_REVISION,
            model_license="Apache-2.0",
            model_artifact_sha256=MODEL_SHA,
            vllm_image="vllm/vllm-openai:latest",
            runtime_config=RUNTIME_CONFIG,
            source_commit="1" * 40,
        )
    with pytest.raises(ReleaseValidationError, match="tensor_parallel_size=1"):
        create_manifest(
            report,
            model_id="Qwen/Qwen2.5-1.5B-Instruct",
            model_revision=MODEL_REVISION,
            model_license="Apache-2.0",
            model_artifact_sha256=MODEL_SHA,
            vllm_image=IMAGE,
            runtime_config={**RUNTIME_CONFIG, "tensor_parallel_size": 2},
            source_commit="1" * 40,
        )


def test_plan_creation_detects_manifest_configuration_tampering(tmp_path):
    champion = _manifest(
        _report(tmp_path / "champion.json", revision="e" * 40),
        revision="e" * 40,
        alias="champion",
    )
    candidate = _manifest(_report(tmp_path / "candidate.json"))
    candidate.runtime_config["max_num_seqs"] = 16

    with pytest.raises(ReleaseValidationError, match="runtime configuration digest"):
        create_plan(
            environment="single-l4-lab",
            requester="release-requester",
            champion=champion,
            candidate=candidate,
        )
