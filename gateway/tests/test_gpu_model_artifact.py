from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


def _verifier_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "verify_gpu_model_artifact.py"
    spec = importlib.util.spec_from_file_location("verify_gpu_model_artifact", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_snapshot_path_uses_pinned_repo_revision_and_filename(tmp_path):
    verifier = _verifier_module()

    assert verifier.snapshot_file(tmp_path) == (
        tmp_path
        / "models--Qwen--Qwen2.5-1.5B-Instruct"
        / "snapshots"
        / verifier.MODEL_REVISION
        / "model.safetensors"
    )


def test_verifier_checks_size_and_digest_without_loading_whole_file(tmp_path):
    verifier = _verifier_module()
    artifact = tmp_path / "model.safetensors"
    content = b"test artifact fixture"
    artifact.write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    assert verifier.verify_file(artifact, len(content), expected_hash) == {
        "size_bytes": len(content),
        "sha256": expected_hash,
    }


def test_verifier_follows_hugging_face_cache_symlink(tmp_path):
    verifier = _verifier_module()
    blob = tmp_path / "blobs" / "model-hash"
    blob.parent.mkdir()
    content = b"cached model artifact"
    blob.write_bytes(content)
    snapshot_entry = tmp_path / "snapshot-model.safetensors"
    snapshot_entry.symlink_to(blob)

    assert verifier.verify_file(
        snapshot_entry, len(content), hashlib.sha256(content).hexdigest()
    ) == {
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


@pytest.mark.parametrize(
    ("expected_size", "expected_hash", "message"),
    [
        (10, hashlib.sha256(b"fixture").hexdigest(), "bytes; expected"),
        (len(b"fixture"), "0" * 64, "SHA-256 does not match"),
    ],
)
def test_verifier_rejects_wrong_size_or_digest(tmp_path, expected_size, expected_hash, message):
    verifier = _verifier_module()
    artifact = tmp_path / "model.safetensors"
    artifact.write_bytes(b"fixture")

    with pytest.raises(ValueError, match=message):
        verifier.verify_file(artifact, expected_size, expected_hash)


def test_verifier_rejects_missing_artifact(tmp_path):
    verifier = _verifier_module()

    with pytest.raises(FileNotFoundError, match="missing or not a file"):
        verifier.verify_file(tmp_path / "missing.safetensors", 1, "0" * 64)
