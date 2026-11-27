import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.gpu_inference.run_vllm_matrix import (
    benchmark_command,
    benchmark_container_name,
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
        "model_alias": "Qwen",
        "num_prompts": 100,
        "num_warmups": 5,
    }
    command = benchmark_command(case, matrix, repetition, {}, tmp_path)

    assert name == "gpu-lab-bench-short-c4-r3"
    assert command[command.index("--name") + 1] == name
