from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import onnxruntime as ort


def _create_model_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "create_model.py"
    spec = importlib.util.spec_from_file_location("create_model", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_artifact_has_a_distinct_digest_and_valid_onnx_contract(tmp_path):
    create_model = _create_model_module().create_model
    stable, candidate = tmp_path / "stable.onnx", tmp_path / "candidate.onnx"
    create_model(stable)
    create_model(candidate, candidate=True)
    assert hashlib.sha256(stable.read_bytes()).hexdigest() != hashlib.sha256(
        candidate.read_bytes()
    ).hexdigest()
    for artifact in (stable, candidate):
        session = ort.InferenceSession(str(artifact), providers=["CPUExecutionProvider"])
        labels = session.run(["label"], {"features": np.asarray([[1, 0, 3, 0]], dtype=np.float32)})
        assert labels[0].shape == (1,)
