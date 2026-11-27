import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluations.gpu_llm.run_evaluation import (  # noqa: E402
    check_completion,
    evaluation_exit_code,
    load_suite,
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
