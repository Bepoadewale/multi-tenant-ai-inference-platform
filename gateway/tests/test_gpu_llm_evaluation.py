import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluations.gpu_llm.run_evaluation import (  # noqa: E402
    check_completion,
    evaluation_exit_code,
    load_suite,
    publish_report_to_mlflow,
)


def test_gpu_evaluation_suite_has_versioned_synthetic_cases():
    suite = load_suite(Path("evaluations/gpu_llm/tasks.json"))

    assert suite["schema_version"] == 1
    assert len(suite["cases"]) == 7
    assert any(case.get("request_kind") == "malformed_json" for case in suite["cases"])


def test_exact_number_requires_a_whole_numeric_token():
    check = {"type": "exact_number", "value": "4"}

    assert check_completion("The answer is 4.", check)[0] is True
    assert check_completion("The answer is 14.", check)[0] is False
    assert check_completion("The answer is 4.5.", check)[0] is False


def test_json_output_gate_checks_the_expected_object():
    check = {"type": "json_object", "expected": {"name": "Ada", "role": "engineer"}}

    assert check_completion('{"name":"Ada","role":"engineer"}', check)[0] is True
    assert check_completion("not json", check)[0] is False


def test_subjective_summary_is_left_for_human_review():
    assert check_completion("The service recovered.", {"type": "manual_review"}) == (
        None,
        "subjective response requires human review",
    )


def test_pending_human_review_cannot_look_like_a_fully_approved_evaluation():
    assert evaluation_exit_code(
        {"automatic_gate": "pass", "human_review_required": True}
    ) == 2
    assert evaluation_exit_code(
        {"automatic_gate": "fail", "human_review_required": False}
    ) == 1
    assert evaluation_exit_code(
        {"automatic_gate": "pass", "human_review_required": False}
    ) == 0


def test_mlflow_publication_logs_only_sanitized_evaluation_metadata(tmp_path, monkeypatch):
    calls = []

    class Run:
        info = types.SimpleNamespace(run_id="run-123")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    fake_mlflow = types.SimpleNamespace(
        set_tracking_uri=lambda uri: calls.append(("tracking_uri", uri)),
        set_experiment=lambda name: calls.append(("experiment", name)),
        start_run=lambda **kwargs: (calls.append(("start_run", kwargs)) or Run()),
        log_params=lambda values: calls.append(("params", values)),
        log_metrics=lambda values: calls.append(("metrics", values)),
        set_tags=lambda values: calls.append(("tags", values)),
        log_artifact=lambda path, artifact_path: calls.append(
            ("artifact", Path(path).read_text(encoding="utf-8"), artifact_path)
        ),
    )
    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    artifact = tmp_path / "results.json"
    artifact.write_text('{"content_policy":"prompts and completion text are not stored"}')
    report = {
        "suite_id": "suite-v1",
        "suite_sha256": "suite-digest",
        "model": "gpu-default",
        "model_revision": "revision-123",
        "case_count": 7,
        "automatic_gate": "pass",
        "human_review_required": True,
        "passed_count": 6,
        "failed_count": 0,
        "schema_version": 1,
        "started_at": "2026-11-27T00:00:00+00:00",
    }

    run_id = publish_report_to_mlflow(artifact, report, "http://mlflow:5000", "lab")

    assert run_id == "run-123"
    assert ("tracking_uri", "http://mlflow:5000") in calls
    assert ("experiment", "lab") in calls
    assert any(item[0] == "params" and item[1]["model_revision"] == "revision-123" for item in calls)
    assert any(item[0] == "artifact" and "completion text are not stored" in item[1] for item in calls)
    assert all("prompt text" not in repr(item) for item in calls)
