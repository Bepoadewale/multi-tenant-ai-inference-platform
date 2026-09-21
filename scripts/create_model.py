#!/usr/bin/env python3
"""Create the deterministic CPU ONNX fixture used by the local platform demo."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper


def create_model(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    # Features: positive terms, negative terms, input length, question marks.
    weights = np.array([[1.5, -1.5], [-1.5, 1.5], [0.02, 0.01], [0.0, 0.0]], dtype=np.float32)
    bias = np.array([0.0, 0.0], dtype=np.float32)
    graph = helper.make_graph(
        [
            helper.make_node("Gemm", ["features", "weights", "bias"], ["scores"]),
            helper.make_node("ArgMax", ["scores"], ["label"], axis=1, keepdims=0),
        ],
        "tiny-intent-classifier",
        [helper.make_tensor_value_info("features", TensorProto.FLOAT, [None, 4])],
        [
            helper.make_tensor_value_info("scores", TensorProto.FLOAT, [None, 2]),
            helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
        ],
        [
            helper.make_tensor("weights", TensorProto.FLOAT, weights.shape, weights.flatten()),
            helper.make_tensor("bias", TensorProto.FLOAT, bias.shape, bias.flatten()),
        ],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 10
    onnx.checker.check_model(model)
    onnx.save(model, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("models/tiny-intent-classifier.onnx"))
    create_model(parser.parse_args().output)
