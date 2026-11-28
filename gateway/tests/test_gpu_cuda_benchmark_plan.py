import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.cuda_performance.torch_matmul import (  # noqa: E402
    median_and_gflops,
    plan_record,
    validate_parameters,
)


def test_cuda_plan_is_static_and_reports_correct_workload_bounds():
    plan = plan_record([256, 512], warmups=3, repeats=10, max_runtime_seconds=600)

    assert plan["network_requests"] == 0
    assert plan["gpu_operations"] == 0
    assert plan["sizes"] == [256, 512]


def test_matrix_sizes_and_repeat_counts_are_bounded():
    validate_parameters([2048], warmups=0, repeats=1, max_runtime_seconds=600)

    try:
        validate_parameters([4096], warmups=1, repeats=1, max_runtime_seconds=600)
    except ValueError as error:
        assert "between 16 and 2048" in str(error)
    else:
        raise AssertionError("an unbounded matrix size was accepted")
    try:
        validate_parameters([1024], warmups=1, repeats=1, max_runtime_seconds=601)
    except ValueError as error:
        assert "between 1 and 600 seconds" in str(error)
    else:
        raise AssertionError("a benchmark runtime above the hard cap was accepted")


def test_median_and_gflops_use_synchronized_sample_median():
    metrics = median_and_gflops([2.0, 4.0, 6.0], size=100)

    assert metrics["median_ms"] == 4.0
    assert metrics["median_gflops"] == 0.5
