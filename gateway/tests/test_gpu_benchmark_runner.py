import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.gpu_inference.run_vllm_matrix import (
    benchmark_command,
    benchmark_container_name,
    main,
)


def test_benchmark_command_and_cleanup_share_the_exact_container_name(tmp_path):
    case = {
        "name": "short",
        "input_tokens": 256,
        "output_tokens": 64,
        "concurrency": 4,
    }
    repetition = 3

    name = benchmark_container_name(case, repetition)
    matrix = {
        "model_alias": "gpu-default",
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "num_prompts": 100,
        "num_warmups": 5,
    }
    command = benchmark_command(case, matrix, repetition, {}, tmp_path)

    assert name == "gpu-lab-bench-short-c4-r3"
    assert command[command.index("--name") + 1] == name
    assert command[command.index("--model") + 1] == "gpu-default"
    assert command[command.index("--tokenizer") + 1] == "Qwen/Qwen2.5-1.5B-Instruct"


@pytest.mark.parametrize(
    ("failure", "expected_exit"),
    [("timeout", 124), ("interrupt", 130)],
)
def test_failed_first_run_stops_its_own_container(
    tmp_path, monkeypatch, failure, expected_exit
):
    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model_alias": "gpu-default",
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "context_length": 8192,
                "num_prompts": 1,
                "num_warmups": 0,
                "repetitions": 1,
                "workloads": [
                    {
                        "name": "short",
                        "input_tokens": 8,
                        "output_tokens": 2,
                        "concurrency": [1],
                    },
                    {
                        "name": "long-context",
                        "input_tokens": 64,
                        "output_tokens": 4,
                        "concurrency": [4],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_vllm_matrix.py",
            "--matrix",
            str(matrix_path),
            "--output-dir",
            str(tmp_path / "results"),
            "--region",
            "us-east-1",
            "--instance-type",
            "g6.xlarge",
            "--model-revision",
            "a" * 40,
            "--max-runtime-minutes",
            "1",
        ],
    )
    monkeypatch.setattr(
        "benchmarks.gpu_inference.run_vllm_matrix.base_metadata", lambda _: {}
    )
    stopped = []

    class FakeProcess:
        pid = 123

        def __init__(self, *_args, **_kwargs):
            self.wait_calls = 0

        def wait(self, timeout=None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                if failure == "timeout":
                    raise subprocess.TimeoutExpired("benchmark", timeout)
                raise KeyboardInterrupt
            return 0

    monkeypatch.setattr(subprocess, "Popen", FakeProcess)
    monkeypatch.setattr("benchmarks.gpu_inference.run_vllm_matrix.os.killpg", lambda *_: None)
    monkeypatch.setattr(
        "benchmarks.gpu_inference.run_vllm_matrix.stop_benchmark_container",
        stopped.append,
    )

    assert main() == expected_exit
    assert stopped == ["gpu-lab-bench-short-c1-r1"]
