import json
import stat
import subprocess
from pathlib import Path

import pytest

from scripts import gpu_ec2_evidence, gpu_ec2_host_guard, gpu_ec2_smoke

IDENTITY = {
    "account_id": "123456789012",
    "instance_id": "i-0123456789abcdef0",
    "instance_type": "g6.xlarge",
    "region": "us-east-1",
}


def test_host_guard_matches_explicit_account_and_instance(monkeypatch):
    monkeypatch.setattr(gpu_ec2_host_guard, "instance_identity", lambda: IDENTITY.copy())

    result = gpu_ec2_host_guard.verify_host(
        expected_account_id=IDENTITY["account_id"],
        expected_instance_id=IDENTITY["instance_id"],
    )

    assert result["instance_type"] == "g6.xlarge"
    assert "account_id" in result


@pytest.mark.parametrize(
    "expected_account,expected_instance",
    [("000000000000", IDENTITY["instance_id"]), (IDENTITY["account_id"], "i-other")],
)
def test_host_guard_rejects_wrong_account_or_instance(
    monkeypatch, expected_account, expected_instance
):
    monkeypatch.setattr(gpu_ec2_host_guard, "instance_identity", lambda: IDENTITY.copy())

    with pytest.raises(ValueError):
        gpu_ec2_host_guard.verify_host(
            expected_account_id=expected_account,
            expected_instance_id=expected_instance,
        )


def test_host_guard_requires_exactly_one_l4(monkeypatch):
    monkeypatch.setattr(gpu_ec2_host_guard, "instance_identity", lambda: IDENTITY.copy())
    monkeypatch.setattr(
        gpu_ec2_host_guard.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "NVIDIA L4\n", ""),
    )

    result = gpu_ec2_host_guard.verify_host(
        expected_account_id=IDENTITY["account_id"],
        expected_instance_id=IDENTITY["instance_id"],
        require_l4=True,
    )

    assert result["gpu"] == "NVIDIA L4"


def test_host_guard_rejects_wrong_gpu_count_or_type(monkeypatch):
    monkeypatch.setattr(gpu_ec2_host_guard, "instance_identity", lambda: IDENTITY.copy())
    monkeypatch.setattr(
        gpu_ec2_host_guard.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "NVIDIA L4\nNVIDIA L4\n", ""),
    )

    with pytest.raises(ValueError, match="exactly one visible NVIDIA L4"):
        gpu_ec2_host_guard.verify_host(
            expected_account_id=IDENTITY["account_id"],
            expected_instance_id=IDENTITY["instance_id"],
            require_l4=True,
        )


def _token_file(tmp_path: Path) -> Path:
    path = tmp_path / "tokens.json"
    path.write_text(json.dumps({
        "customer_support": "support-secret",
        "internal_engineering": "engineering-secret",
        "research": "research-secret",
    }))
    path.chmod(0o600)
    return path


def test_gpu_smoke_checks_readiness_tenant_permissions_and_inference(monkeypatch, tmp_path):
    monkeypatch.setattr(gpu_ec2_smoke, "verify_host", lambda **_kwargs: IDENTITY.copy())
    success = {
        "choices": [{"message": {"content": "OK"}}],
        "x_backend": "vllm-single-l4",
        "usage": {"total_tokens": 4},
    }
    outcomes = [
        (200, b"{}", "application/json"),
        (200, b"{}", "application/json"),
        (200, b"{}", "application/json"),
        (200, b'{"data":[{"id":"chat-default"}]}', "application/json"),
        (401, b"", "application/json"),
        (403, b"", "application/json"),
        *[(200, json.dumps(success).encode(), "application/json") for _ in range(3)],
        (200, b"data: {}\n\ndata: [DONE]\n\n", "text/event-stream"),
    ]
    requests = []

    def fake_request(url, **kwargs):
        requests.append((url, kwargs))
        return outcomes.pop(0)

    monkeypatch.setattr(gpu_ec2_smoke, "_request", fake_request)

    result = gpu_ec2_smoke.run_smoke(token_file=_token_file(tmp_path))

    assert result["passed"] is True
    assert result["inference_requests"] == 4
    assert len(requests) == 10
    assert all("secret" not in str(request) for request in result)


def test_gpu_smoke_requires_private_tenant_token_file(tmp_path):
    path = _token_file(tmp_path)
    path.chmod(0o640)

    with pytest.raises(ValueError, match="owner-only"):
        gpu_ec2_smoke._tokens(path)


def test_gpu_smoke_caps_response_body(monkeypatch):
    class Response:
        status = 200
        headers = {"Content-Type": "text/event-stream"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            return b"x" * limit

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(gpu_ec2_smoke, "OPENER", Opener())

    with pytest.raises(RuntimeError, match="bounded body size"):
        gpu_ec2_smoke._request("http://127.0.0.1:8081/v1/chat/completions")


def test_gpu_smoke_readiness_only_makes_no_inference_request(monkeypatch, tmp_path):
    monkeypatch.setattr(gpu_ec2_smoke, "verify_host", lambda **_kwargs: IDENTITY.copy())
    calls = []
    monkeypatch.setattr(
        gpu_ec2_smoke,
        "_request",
        lambda url, **kwargs: calls.append(url) or (200, b"{}", "application/json"),
    )

    result = gpu_ec2_smoke.run_smoke(token_file=_token_file(tmp_path), readiness_only=True)

    assert result["inference_requests"] == 0
    assert len(calls) == 3


def test_evidence_collection_uses_private_new_directory_and_sanitized_fields(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(gpu_ec2_evidence, "verify_host", lambda **_kwargs: IDENTITY | {"gpu": "NVIDIA L4"})

    def fake_run(command, **_kwargs):
        if command[-1] == "json":
            return {"ok": True, "output": '{"Service":"vllm","State":"running","Health":"healthy"}'}
        return {"ok": True, "output": "safe-version-or-host-value"}

    monkeypatch.setattr(gpu_ec2_evidence, "_run", fake_run)
    destination = tmp_path / "evidence"

    output = gpu_ec2_evidence.collect(destination)
    record = json.loads(output.read_text())

    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert record["commands"]["compose_services"]["services"] == [
        {"service": "vllm", "state": "running", "health": "healthy"}
    ]
    assert "prompt" not in output.read_text().lower()


def test_evidence_collection_refuses_public_repository_destination(monkeypatch):
    monkeypatch.setattr(gpu_ec2_evidence, "verify_host", lambda **_kwargs: IDENTITY | {"gpu": "NVIDIA L4"})

    with pytest.raises(ValueError, match="outside the public repository"):
        gpu_ec2_evidence.collect(gpu_ec2_evidence.ROOT / ".local" / "test-evidence")
