#!/usr/bin/env python3
"""Register local ONNX serving artifacts and fixture evidence in MLflow."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

import mlflow
import numpy as np
import onnxruntime as ort
from mlflow.tracking import MlflowClient

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "local-tiny-intent-classifier"
EXPERIMENT = "flagship-inference-models"
FIXTURE = [
    ([1.0, 0.0, 3.0, 0.0], 0),
    ([0.0, 1.0, 3.0, 0.0], 1),
    ([2.0, 0.0, 5.0, 1.0], 0),
    ([0.0, 2.0, 5.0, 1.0], 1),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(path: Path) -> dict[str, float]:
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    started = perf_counter()
    inputs = np.asarray([row[0] for row in FIXTURE], dtype=np.float32)
    labels = session.run(["label"], {"features": inputs})[0].tolist()
    elapsed_ms = (perf_counter() - started) * 1000
    expected = [row[1] for row in FIXTURE]
    return {
        "fixture_accuracy": sum(
            int(actual == predicted) for actual, predicted in zip(labels, expected, strict=True)
        )
        / len(expected),
        "fixture_inference_ms": elapsed_ms,
        "fixture_samples": float(len(expected)),
    }


def register(variant: str, path: Path, client: MlflowClient) -> dict[str, str]:
    artifact_digest = digest(path)
    metrics = evaluate(path)
    with mlflow.start_run(run_name=f"bootstrap-{variant}") as run:
        mlflow.set_tags(
            {
                "release.variant": variant,
                "artifact.sha256": artifact_digest,
                "input.schema": "float32[batch,4]",
                "runtime.provider": "CPUExecutionProvider",
            }
        )
        mlflow.log_params({"artifact": path.name, "runtime": "onnxruntime", "variant": variant})
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(path), artifact_path="onnx")
        source = mlflow.get_artifact_uri(f"onnx/{path.name}")
        version = client.create_model_version(MODEL_NAME, source, run_id=run.info.run_id)
        client.set_model_version_tag(MODEL_NAME, version.version, "release.variant", variant)
        client.set_model_version_tag(MODEL_NAME, version.version, "artifact.sha256", artifact_digest)
        client.set_model_version_tag(
            MODEL_NAME, version.version, "fixture.accuracy", str(metrics["fixture_accuracy"])
        )
        return {"variant": variant, "version": version.version, "artifact_sha256": artifact_digest}


def main() -> None:
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:15010"))
    mlflow.set_experiment(EXPERIMENT)
    client = MlflowClient()
    try:
        client.create_registered_model(MODEL_NAME)
    except Exception as exc:
        if "already exists" not in str(exc).lower() and "resource_already_exists" not in str(exc).lower():
            raise
    registered = [
        register("stable-v1", ROOT / "models" / "tiny-intent-classifier.onnx", client),
        register("candidate-v2", ROOT / "models" / "tiny-intent-classifier-v2.onnx", client),
    ]
    for model in registered:
        alias = "champion" if model["variant"] == "stable-v1" else "candidate"
        client.set_registered_model_alias(MODEL_NAME, alias, model["version"])
    destination = ROOT / ".local" / "mlflow" / "registry-evidence.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"model": MODEL_NAME, "versions": registered}, indent=2) + "\n")
    print(json.dumps({"registered": registered}, indent=2))


if __name__ == "__main__":
    main()
