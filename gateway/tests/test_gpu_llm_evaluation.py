import json
import sys
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluations.gpu_llm.run_evaluation import (  # noqa: E402
    check_completion,
    evaluation_exit_code,
    load_suite,
    publish_report_to_mlflow,
    request_case,
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
    assert check_completion("The answer is -4.", check)[0] is False
    assert check_completion("The answer is +4.", check)[0] is False


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


@pytest.mark.parametrize(
    "payload",
    [
        {"choices": [{"message": {"content": None}}], "usage": {}},
        {"choices": [{"message": {"content": ["4"]}}], "usage": {}},
        {"choices": [{"message": {"content": "4"}}], "usage": []},
        {
            "choices": [{"message": {"content": "4"}}],
            "usage": {"prompt_tokens": "1"},
        },
    ],
)
def test_invalid_success_response_types_become_a_failed_case(payload):
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = json.dumps(payload).encode("utf-8")
    case = {
        "id": "factual-arithmetic",
        "category": "factual-question-answering",
        "messages": [{"role": "user", "content": "What is 2 + 2?"}],
        "check": {"type": "exact_number", "value": "4"},
    }

    with patch(
        "evaluations.gpu_llm.run_evaluation.EVALUATION_OPENER.open",
        return_value=response,
    ):
        result = request_case(
            "http://127.0.0.1:8081/v1", "chat-default", case, "", 1, False
        )

    assert result["passed"] is False
    assert result["error_class"] == "InvalidCompletionSchema"


def test_evaluator_does_not_forward_bearer_token_across_redirect():
    forwarded_requests = []

    class DestinationHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            forwarded_requests.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *_args):
            pass

    destination = ThreadingHTTPServer(("127.0.0.1", 0), DestinationHandler)
    destination_thread = Thread(target=destination.serve_forever, daemon=True)
    destination_thread.start()

    destination_url = f"http://127.0.0.1:{destination.server_port}/collect"

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(307)
            self.send_header("Location", destination_url)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args):
            pass

    redirector = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    redirector_thread = Thread(target=redirector.serve_forever, daemon=True)
    redirector_thread.start()
    case = {
        "id": "redirect-check",
        "category": "security",
        "messages": [{"role": "user", "content": "synthetic"}],
        "check": {"type": "exact_number", "value": "1"},
    }

    try:
        result = request_case(
            f"http://127.0.0.1:{redirector.server_port}/v1",
            "gpu-default",
            case,
            "synthetic-test-token",
            timeout=3,
            show_subjective_response=False,
        )
    finally:
        redirector.shutdown()
        destination.shutdown()
        redirector.server_close()
        destination.server_close()
        redirector_thread.join(timeout=3)
        destination_thread.join(timeout=3)

    assert result["http_status"] == 307
    assert result["error_class"] == "HTTPError"
    assert forwarded_requests == []


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
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "schema_version": 1,
        "started_at": "2026-11-27T00:00:00+00:00",
        "provenance": {
            "source_commit": "a" * 40,
            "model_artifact_sha256": "b" * 64,
            "vllm_image": "vllm/vllm-openai@sha256:" + "c" * 64,
            "runtime_config_sha256": "d" * 64,
        },
    }

    run_id = publish_report_to_mlflow(artifact, report, "http://mlflow:5000", "lab")

    assert run_id == "run-123"
    assert ("tracking_uri", "http://mlflow:5000") in calls
    assert ("experiment", "lab") in calls
    assert any(item[0] == "params" and item[1]["model_revision"] == "revision-123" for item in calls)
    assert any(item[0] == "artifact" and "completion text are not stored" in item[1] for item in calls)
    assert all("prompt text" not in repr(item) for item in calls)
