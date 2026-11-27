import hashlib
import json
import stat
import subprocess
import sys
from dataclasses import asdict, replace

import pytest

from evaluations.gpu_llm.release_control import create_manifest, create_plan, digest_json
from scripts.gpu_release_controller import (
    DEFAULT_API_URL,
    ControllerError,
    HostController,
    RejectRedirectHandler,
    approved_plan_from_json,
    atomic_write_private,
    fetch_approved_plan,
    main,
    model_snapshot_digest,
    update_environment,
    verify_container_config,
)

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
IMAGE = "vllm/vllm-openai@sha256:" + "c" * 64
SOURCE_COMMIT = "1" * 40
CONFIG = {
    "served_model_name": "gpu-default",
    "dtype": "bfloat16",
    "max_model_len": 8192,
    "max_num_seqs": 2,
    "max_num_batched_tokens": 8192,
    "gpu_memory_utilization": 0.85,
    "tensor_parallel_size": 1,
}


def _manifest(tmp_path, *, alias, revision, artifact_digest):
    report_path = tmp_path / f"{alias}-{revision}.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suite_id": "single-l4-qwen-smoke-v1",
                "suite_sha256": "d" * 64,
                "model_revision": revision,
                "automatic_gate": "pass",
                "failed_count": 0,
                "human_review_required": True,
                "runtime_config": CONFIG,
                "provenance": {
                    "source_commit": SOURCE_COMMIT,
                    "model_artifact_sha256": artifact_digest,
                    "vllm_image": IMAGE,
                    "runtime_config_sha256": digest_json(CONFIG),
                },
            }
        ),
        encoding="utf-8",
    )
    return create_manifest(
        report_path,
        model_id=MODEL_ID,
        model_revision=revision,
        model_license="Apache-2.0",
        model_artifact_sha256=artifact_digest,
        vllm_image=IMAGE,
        runtime_config=CONFIG,
        source_commit=SOURCE_COMMIT,
        deployment_alias=alias,
    )


def _release_pair(tmp_path):
    champion = _manifest(
        tmp_path, alias="champion", revision="a" * 40, artifact_digest="b" * 64
    )
    candidate = _manifest(
        tmp_path, alias="candidate", revision="e" * 40, artifact_digest="f" * 64
    )
    plan = create_plan(
        environment="single-l4-lab",
        requester="release-requester",
        champion=champion,
        candidate=candidate,
    )
    approved = replace(plan, status="APPROVED", approved_by="release-reviewer")
    record = {
        "plan": asdict(approved),
        "champion": asdict(champion),
        "candidate": asdict(candidate),
    }
    return champion, candidate, approved, record


def test_model_snapshot_digest_handles_hub_cache_symlinks(tmp_path):
    cache = tmp_path / "hub"
    repository = cache / "models--Qwen--Qwen2.5-1.5B-Instruct"
    snapshot = repository / "snapshots" / ("a" * 40)
    blobs = repository / "blobs"
    snapshot.mkdir(parents=True)
    blobs.mkdir()
    weight = blobs / "weight-shard"
    weight.write_bytes(b"verified test weights")
    (snapshot / "model.safetensors").symlink_to(weight)
    (snapshot / "config.json").write_text("{}", encoding="utf-8")

    actual = model_snapshot_digest(cache, MODEL_ID, "a" * 40)
    entries = [
        {
            "path": "config.json",
            "size_bytes": 2,
            "sha256": hashlib.sha256(b"{}").hexdigest(),
        },
        {
            "path": "model.safetensors",
            "size_bytes": len(b"verified test weights"),
            "sha256": hashlib.sha256(b"verified test weights").hexdigest(),
        },
    ]
    assert actual == hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_model_snapshot_digest_rejects_symlink_outside_cache(tmp_path):
    cache = tmp_path / "hub"
    snapshot = cache / "models--Qwen--Qwen2.5-1.5B-Instruct" / "snapshots" / ("a" * 40)
    snapshot.mkdir(parents=True)
    secret = tmp_path / "outside"
    secret.write_text("not a model artifact", encoding="utf-8")
    (snapshot / "unexpected.bin").symlink_to(secret)
    with pytest.raises(ControllerError, match="outside the cache root"):
        model_snapshot_digest(cache, MODEL_ID, "a" * 40)


def test_approved_plan_validation_requires_two_actors_and_exact_manifests(tmp_path):
    _, _, _, record = _release_pair(tmp_path)
    plan, _, _ = approved_plan_from_json(record)
    assert plan.status == "APPROVED"
    record["plan"]["approved_by"] = record["plan"]["requester"]
    with pytest.raises(ControllerError, match="cannot approve"):
        approved_plan_from_json(record)


def test_approved_plan_rejects_unsafe_model_paths(tmp_path):
    champion, candidate, _, _ = _release_pair(tmp_path)
    champion = replace(champion, model_id="../escape")
    candidate = replace(candidate, model_id="../escape")
    plan = create_plan(
        environment="single-l4-lab",
        requester="release-requester",
        champion=champion,
        candidate=candidate,
    )
    approved = replace(plan, status="APPROVED", approved_by="release-reviewer")
    with pytest.raises(ControllerError, match="namespace/name"):
        approved_plan_from_json(
            {
                "plan": asdict(approved),
                "champion": asdict(champion),
                "candidate": asdict(candidate),
            }
        )


def test_release_api_token_is_never_sent_to_remote_cleartext_urls():
    with pytest.raises(ControllerError, match="HTTPS or a local loopback"):
        fetch_approved_plan(
            "http://release.example.test/gpu-release/v1",
            "12345678-1234-1234-1234-123456789012",
            "short-lived-token",
        )


def test_release_api_redirects_are_rejected():
    from urllib.request import Request

    request = Request(
        "https://release.example.test/gpu-release/v1/plans",
        headers={"Authorization": "Bearer do-not-forward"},
    )
    assert RejectRedirectHandler().redirect_request(
        request, None, 302, "Found", {}, "https://other.example.test/steal"
    ) is None


def test_update_environment_preserves_secrets_and_comments(tmp_path):
    _, candidate, _, _ = _release_pair(tmp_path)
    original = (
        "# operator-only section\n"
        "GRAFANA_ADMIN_PASSWORD=keep-this-private\n"
        "GPU_MODEL_ID=old/model\n"
        "GPU_MODEL_REVISION=" + "a" * 40 + "\n"
        "GPU_SERVED_MODEL_NAME=gpu-default\n"
        f"VLLM_IMAGE={IMAGE}\n"
        "GPU_DTYPE=float16\n"
        "GPU_MAX_MODEL_LEN=1024\n"
        "GPU_MAX_NUM_SEQS=1\n"
        "GPU_MAX_BATCHED_TOKENS=1024\n"
        "GPU_MEMORY_UTILIZATION=0.5\n"
        "GPU_TENSOR_PARALLEL_SIZE=1\n"
    )
    updated = update_environment(original, candidate)
    assert "# operator-only section\n" in updated
    assert "GRAFANA_ADMIN_PASSWORD=keep-this-private\n" in updated
    assert f"GPU_MODEL_REVISION={'e' * 40}\n" in updated
    assert "GPU_MAX_MODEL_LEN=8192\n" in updated
    assert "GPU_MEMORY_UTILIZATION=0.85\n" in updated


def test_atomic_write_is_private_without_changing_parent_permissions(tmp_path):
    destination = tmp_path / "existing" / ".env"
    destination.parent.mkdir()
    destination.parent.chmod(0o755)
    destination.write_text("PASSWORD=sample\n", encoding="utf-8")
    atomic_write_private(destination, b"PASSWORD=sample\n")
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o755


def test_running_container_must_match_the_active_manifest(tmp_path):
    champion, _, _, _ = _release_pair(tmp_path)
    inspect = {
        "State": {"Status": "running", "Health": {"Status": "healthy"}},
        "Mounts": [
            {
                "Type": "volume",
                "Name": "multi-tenant-ai-inference-platform-gpu-model-cache",
                "Destination": "/root/.cache/huggingface",
            }
        ],
        "Config": {
            "Image": IMAGE,
            "Cmd": [
                "--model", MODEL_ID,
                "--revision", "a" * 40,
                "--served-model-name", "gpu-default",
                "--dtype", "bfloat16",
                "--max-model-len", "8192",
                "--max-num-seqs", "2",
                "--max-num-batched-tokens", "8192",
                "--gpu-memory-utilization", "0.85",
                "--tensor-parallel-size", "1",
            ],
        },
    }
    verify_container_config(inspect, champion)
    inspect["Config"]["Image"] = "vllm/vllm-openai:latest"
    with pytest.raises(ControllerError, match="image does not match"):
        verify_container_config(inspect, champion)
    inspect["Config"]["Image"] = IMAGE
    inspect["Mounts"][0]["Name"] = "unverified-model-cache"
    with pytest.raises(ControllerError, match="verified model-cache volume"):
        verify_container_config(inspect, champion)


def test_host_readiness_checks_vllm_and_both_loopback_gateway_replicas(tmp_path, monkeypatch):
    champion = _manifest(
        tmp_path,
        alias="champion",
        revision="a" * 40,
        artifact_digest="b" * 64,
    )
    visited = []

    class Response:
        status = 200

        def __init__(self, url):
            self.url = url

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            if self.url.endswith("/v1/models"):
                return json.dumps({"data": [{"id": "gpu-default"}]}).encode()
            return b""

    def open_url(url, timeout):
        visited.append(url)
        return Response(url)

    monkeypatch.setattr("scripts.gpu_release_controller.urlopen", open_url)
    HostController(sleeper=lambda _: None)._check_http_ready(champion)
    assert DEFAULT_API_URL == "http://127.0.0.1:8081/gpu-release/v1"
    assert "http://127.0.0.1:8000/health" in visited
    assert "http://127.0.0.1:8000/v1/models" in visited
    assert "http://127.0.0.1:8081/healthz" in visited
    assert "http://127.0.0.1:8082/healthz" in visited


def test_recover_cli_prints_success_without_a_plan_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["gpu_release_controller.py", "recover"])
    monkeypatch.setattr(HostController, "recover", lambda self: None)
    assert main() == 0
    assert capsys.readouterr().out == "active champion was restored and verified\n"


@pytest.mark.parametrize("candidate_fails", [False, True])
def test_deploy_commits_candidate_or_restores_champion(tmp_path, monkeypatch, candidate_fails):
    champion, candidate, _, record = _release_pair(tmp_path)
    env_file = tmp_path / "deployments" / ".env"
    env_file.parent.mkdir()
    env_file.write_text(
        "GRAFANA_ADMIN_PASSWORD=do-not-log\n"
        f"GPU_MODEL_ID={MODEL_ID}\nGPU_MODEL_REVISION={'a' * 40}\n",
        encoding="utf-8",
    )
    state_file = tmp_path / ".local/gpu-release/active-release.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(
        json.dumps(
            {
                "manifest": asdict(champion),
                "manifest_sha256": champion.sha256,
            }
        ),
        encoding="utf-8",
    )
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    controller = HostController(
        repo=tmp_path,
        env_file=env_file,
        state_file=state_file,
        command_runner=runner,
        sleeper=lambda _: None,
    )
    monkeypatch.setattr("scripts.gpu_release_controller.fetch_approved_plan", lambda *args: record)
    monkeypatch.setattr(controller, "_verify_live", lambda manifest: None)
    monkeypatch.setattr(
        controller,
        "_snapshot_digest",
        lambda manifest: manifest.model_artifact_sha256,
    )
    monkeypatch.setattr(controller, "_wait_container_config", lambda manifest: None)

    def readiness(manifest):
        if candidate_fails and manifest.deployment_alias == "candidate":
            raise ControllerError("simulated readiness failure")

    monkeypatch.setattr(controller, "_check_http_ready", readiness)
    if candidate_fails:
        with pytest.raises(ControllerError, match="previous champion was restored"):
            controller.deploy("12345678-1234-1234-1234-123456789012", "not-logged")
        assert "GPU_MODEL_REVISION=" + "a" * 40 in env_file.read_text()
        transaction = next(state_file.parent.glob("transaction-*.json"))
        assert json.loads(transaction.read_text())["state"] == "ROLLED_BACK"
        assert json.loads(state_file.read_text())["manifest_sha256"] == champion.sha256
    else:
        controller.deploy("12345678-1234-1234-1234-123456789012", "not-logged")
        assert "GPU_MODEL_REVISION=" + "e" * 40 in env_file.read_text()
        transaction = next(state_file.parent.glob("transaction-*.json"))
        assert json.loads(transaction.read_text())["state"] == "DEPLOYED"
        active_record = json.loads(state_file.read_text())
        assert active_record["manifest"]["deployment_alias"] == "champion"
        assert active_record["manifest_sha256"] != candidate.sha256
    assert env_file.read_text().startswith("GRAFANA_ADMIN_PASSWORD=do-not-log\n")
    assert any(command[-1] == "vllm" for command in calls)


def test_restore_active_recovers_the_recorded_champion_after_candidate_evaluation(
    tmp_path, monkeypatch
):
    champion, _, _, _ = _release_pair(tmp_path)
    env_file = tmp_path / "deployments" / ".env"
    env_file.parent.mkdir()
    env_file.write_text(
        f"GPU_MODEL_ID={MODEL_ID}\nGPU_MODEL_REVISION={'e' * 40}\n",
        encoding="utf-8",
    )
    state_file = tmp_path / ".local/gpu-release/active-release.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(
        json.dumps({"manifest": asdict(champion), "manifest_sha256": champion.sha256}),
        encoding="utf-8",
    )
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    controller = HostController(
        repo=tmp_path,
        env_file=env_file,
        state_file=state_file,
        command_runner=runner,
        sleeper=lambda _: None,
    )
    monkeypatch.setattr(controller, "_wait_container_config", lambda manifest: None)
    monkeypatch.setattr(controller, "_check_http_ready", lambda manifest: None)
    monkeypatch.setattr(
        controller,
        "_snapshot_digest",
        lambda manifest: manifest.model_artifact_sha256,
    )

    controller.restore_active()

    assert "GPU_MODEL_REVISION=" + "a" * 40 in env_file.read_text()
    assert json.loads(state_file.read_text())["manifest_sha256"] == champion.sha256
    transaction = next(state_file.parent.glob("transaction-restore-*.json"))
    assert json.loads(transaction.read_text())["state"] == "RESTORED_TO_ACTIVE"
    assert any(command[-1] == "vllm" for command in calls)


def test_restore_active_refuses_to_overwrite_an_incomplete_transaction(tmp_path):
    state_dir = tmp_path / ".local/gpu-release"
    state_dir.mkdir(parents=True)
    (state_dir / "transaction-incomplete.json").write_text(
        json.dumps({"state": "APPLYING"}), encoding="utf-8"
    )
    controller = HostController(
        repo=tmp_path,
        env_file=tmp_path / "deployments/.env",
        state_file=state_dir / "active-release.json",
    )
    with pytest.raises(ControllerError, match="run recover first"):
        controller.restore_active()
