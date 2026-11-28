"""Run a deterministic, synthetic evaluation against an OpenAI-compatible API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_SUITE = Path(__file__).with_name("tasks.json")
DEFAULT_OUTPUT = Path("/var/tmp/gpu-lab/evaluation/results.json")
NUMBERED_LINE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+\S")
ALLOWED_CHECKS = {
    "exact_number",
    "json_object",
    "numbered_lines",
    "manual_review",
    "required_terms",
    "http_status",
}


class NoRedirectHandler(HTTPRedirectHandler):
    """Do not forward an evaluation bearer token to a redirect target."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


EVALUATION_OPENER = build_opener(NoRedirectHandler())


def load_suite(path: Path) -> dict:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema_version") != 1 or not suite.get("suite_id"):
        raise ValueError("evaluation suite must have schema_version 1 and a suite_id")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation suite must contain at least one case")
    seen = set()
    for case in cases:
        case_id = case.get("id")
        check = case.get("check", {})
        if not case_id or case_id in seen:
            raise ValueError("every evaluation case needs a unique id")
        if check.get("type") not in ALLOWED_CHECKS:
            raise ValueError(f"{case_id}: unsupported deterministic check")
        if case.get("request_kind") != "malformed_json" and not case.get("messages"):
            raise ValueError(f"{case_id}: messages are required")
        seen.add(case_id)
    return suite


def check_completion(text: str, check: dict) -> tuple[bool | None, str]:
    kind = check["type"]
    if kind == "manual_review":
        return None, "subjective response requires human review"
    if kind == "exact_number":
        number = re.escape(str(check["value"]))
        # A sign belongs to a numeric token, so `-4` must not satisfy expected `4`.
        passed = re.search(rf"(?<![\w.+-]){number}(?![\w]|\.\d)", text) is not None
        return passed, "expected number present" if passed else "expected number missing"
    if kind == "json_object":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return False, "response is not valid JSON"
        passed = isinstance(value, dict) and value == check["expected"]
        return passed, "JSON matches expected object" if passed else "JSON object differs"
    if kind == "numbered_lines":
        count = sum(bool(NUMBERED_LINE.match(line)) for line in text.splitlines())
        passed = count == int(check["count"])
        return passed, f"found {count} numbered/list lines"
    if kind == "required_terms":
        lowered = text.casefold()
        missing = [term for term in check["values"] if term.casefold() not in lowered]
        return not missing, "required terms present" if not missing else "required terms missing"
    raise ValueError(f"completion check does not support {kind}")


def evaluation_exit_code(report: dict) -> int:
    if report["automatic_gate"] != "pass":
        return 1
    return 2 if report["human_review_required"] else 0


def release_runtime_config() -> dict:
    """Read the exact vLLM settings shared by Compose and the evaluation report."""
    return {
        "served_model_name": os.getenv("GPU_EVAL_MODEL", "gpu-default"),
        "dtype": os.getenv("GPU_EVAL_DTYPE", "UNSET"),
        "max_model_len": int(os.getenv("GPU_EVAL_MAX_MODEL_LEN", "0")),
        "max_num_seqs": int(os.getenv("GPU_EVAL_MAX_NUM_SEQS", "0")),
        "max_num_batched_tokens": int(os.getenv("GPU_EVAL_MAX_BATCHED_TOKENS", "0")),
        "gpu_memory_utilization": float(os.getenv("GPU_EVAL_MEMORY_UTILIZATION", "0")),
        "tensor_parallel_size": int(os.getenv("GPU_EVAL_TENSOR_PARALLEL_SIZE", "0")),
    }


def runtime_config_digest(config: dict) -> str:
    return hashlib.sha256(
        json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def publish_report_to_mlflow(
    report_path: Path,
    report: dict,
    tracking_uri: str,
    experiment_name: str,
) -> str:
    """Store sanitized evaluation metadata and report without prompt text."""
    import mlflow

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"{report['suite_id']}-{report['started_at']}") as run:
        provenance = report["provenance"]
        mlflow.log_params(
            {
                "suite_id": report["suite_id"],
                "suite_sha256": report["suite_sha256"],
                "model": report["model"],
                "model_id": report["model_id"],
                "model_revision": report["model_revision"],
                "case_count": report["case_count"],
                "source_commit": provenance["source_commit"],
                "model_artifact_sha256": provenance["model_artifact_sha256"],
                "vllm_image": provenance["vllm_image"],
                "runtime_config_sha256": provenance["runtime_config_sha256"],
            }
        )
        mlflow.log_metrics(
            {
                "automatic_gate_pass": float(report["automatic_gate"] == "pass"),
                "human_review_required": float(report["human_review_required"]),
                "passed_count": float(report["passed_count"]),
                "failed_count": float(report["failed_count"]),
            }
        )
        mlflow.set_tags(
            {
                "runtime": "vllm",
                "content_policy": "prompt_and_completion_text_excluded",
                "report_schema_version": str(report["schema_version"]),
            }
        )
        mlflow.log_artifact(str(report_path), artifact_path="evaluation")
        return run.info.run_id


def request_case(
    base_url: str,
    model: str,
    case: dict,
    token: str,
    timeout: float,
    show_subjective_response: bool,
) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    if case.get("request_kind") == "malformed_json":
        request_body = b'{"model":'
        expected = case["check"]["accepted"]
    else:
        request_body = json.dumps(
            {
                "model": model,
                "messages": case["messages"],
                "temperature": 0,
                "max_tokens": 128,
                "stream": False,
            }
        ).encode("utf-8")
        expected = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=request_body, headers=headers, method="POST")
    started = time.perf_counter()
    status = 0
    body = b""
    try:
        with EVALUATION_OPENER.open(request, timeout=timeout) as response:
            status = response.status
            body = response.read()
    except HTTPError as error:
        status = error.code
        body = error.read()
    except (TimeoutError, URLError) as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "case_id": case["id"],
            "category": case["category"],
            "http_status": status or None,
            "passed": False,
            "manual_review_required": False,
            "latency_ms": elapsed_ms,
            "error_class": type(error).__name__,
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    if expected is not None:
        passed = status in expected
        return {
            "case_id": case["id"],
            "category": case["category"],
            "http_status": status,
            "passed": passed,
            "manual_review_required": False,
            "latency_ms": elapsed_ms,
            "check_summary": "malformed request rejected" if passed else "unexpected HTTP status",
        }
    if status < 200 or status >= 300:
        return {
            "case_id": case["id"],
            "category": case["category"],
            "http_status": status,
            "passed": False,
            "manual_review_required": False,
            "latency_ms": elapsed_ms,
            "error_class": "HTTPError",
        }
    try:
        payload = json.loads(body)
        completion = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return {
            "case_id": case["id"],
            "category": case["category"],
            "http_status": status,
            "passed": False,
            "manual_review_required": False,
            "latency_ms": elapsed_ms,
            "error_class": "InvalidCompletionSchema",
        }
    if usage is None:
        usage = {}
    token_fields = ("prompt_tokens", "completion_tokens")
    if (
        not isinstance(completion, str)
        or not isinstance(usage, dict)
        or any(
            usage.get(field) is not None
            and (
                not isinstance(usage[field], int)
                or isinstance(usage[field], bool)
                or usage[field] < 0
            )
            for field in token_fields
        )
    ):
        return {
            "case_id": case["id"],
            "category": case["category"],
            "http_status": status,
            "passed": False,
            "manual_review_required": False,
            "latency_ms": elapsed_ms,
            "error_class": "InvalidCompletionSchema",
        }
    if case["check"]["type"] == "manual_review" and show_subjective_response:
        print(f"\nHuman review only — {case['id']} (do not redirect this output):\n{completion}\n")
    passed, summary = check_completion(completion, case["check"])
    return {
        "case_id": case["id"],
        "category": case["category"],
        "http_status": status,
        "passed": passed,
        "manual_review_required": passed is None,
        "latency_ms": elapsed_ms,
        "completion_sha256": hashlib.sha256(completion.encode("utf-8")).hexdigest(),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "check_summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--base-url", default=os.getenv("GPU_EVAL_BASE_URL", "http://127.0.0.1:8000/v1"))
    parser.add_argument("--model", default=os.getenv("GPU_EVAL_MODEL", "gpu-default"))
    parser.add_argument("--model-revision", default=os.getenv("GPU_EVAL_MODEL_REVISION"))
    parser.add_argument("--mlflow-tracking-uri", default=os.getenv("MLFLOW_TRACKING_URI"))
    parser.add_argument(
        "--mlflow-experiment",
        default=os.getenv("GPU_EVAL_MLFLOW_EXPERIMENT", "single-l4-llm-evaluation"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=90)
    parser.add_argument(
        "--output", type=Path, default=os.getenv("GPU_EVAL_OUTPUT", str(DEFAULT_OUTPUT))
    )
    parser.add_argument(
        "--show-subjective-response",
        action="store_true",
        help="print the synthetic subjective response for interactive review; never redirect output",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        suite = load_suite(args.suite)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    if args.timeout_seconds <= 0:
        parser.error("timeout-seconds must be positive")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "suite_id": suite["suite_id"],
                    "case_count": len(suite["cases"]),
                    "model": args.model,
                    "model_revision": args.model_revision or "UNSET",
                    "network_requests": 0,
                    "report_path": str(args.output),
                },
                indent=2,
            )
        )
        return 0
    if not args.model_revision:
        parser.error("set GPU_EVAL_MODEL_REVISION or pass --model-revision before execution")
    output_path = args.output.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    if output_path.is_relative_to(repository_root):
        parser.error("evaluation output must be outside the public repository")
    token = os.getenv("GPU_EVAL_BEARER_TOKEN", "")
    started_at = datetime.now(UTC).isoformat()
    results = [
        request_case(
            args.base_url,
            args.model,
            case,
            token,
            args.timeout_seconds,
            args.show_subjective_response,
        )
        for case in suite["cases"]
    ]
    deterministic = [row["passed"] for row in results if not row["manual_review_required"]]
    report = {
        "schema_version": 1,
        "suite_id": suite["suite_id"],
        "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
        "model": args.model,
        "model_id": os.getenv("GPU_EVAL_MODEL_ID", "UNSET"),
        "model_revision": args.model_revision,
        "runtime_config": release_runtime_config(),
        "provenance": {
            "source_commit": os.getenv("GPU_EVAL_SOURCE_COMMIT", "UNSET"),
            "model_artifact_sha256": os.getenv("GPU_EVAL_MODEL_ARTIFACT_SHA256", "UNSET"),
            "vllm_image": os.getenv("GPU_EVAL_VLLM_IMAGE", "UNSET"),
            "runtime_config_sha256": "",
        },
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "automatic_gate": "pass" if deterministic and all(deterministic) else "fail",
        "human_review_required": any(row["manual_review_required"] for row in results),
        "case_count": len(results),
        "passed_count": sum(row["passed"] is True for row in results),
        "failed_count": sum(row["passed"] is False for row in results),
        "results": results,
        "content_policy": "prompts and completion text are not stored",
    }
    report["provenance"]["runtime_config_sha256"] = runtime_config_digest(
        report["runtime_config"]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(output_fd, 0o600)
    with os.fdopen(output_fd, "w", encoding="utf-8") as output_file:
        output_file.write(json.dumps(report, indent=2) + "\n")
    mlflow_run_id = None
    if args.mlflow_tracking_uri:
        mlflow_run_id = publish_report_to_mlflow(
            output_path, report, args.mlflow_tracking_uri, args.mlflow_experiment
        )
    summary = {key: report[key] for key in (
        "suite_id", "model", "automatic_gate", "human_review_required",
        "case_count", "passed_count", "failed_count"
    )}
    if mlflow_run_id:
        summary["mlflow_run_id"] = mlflow_run_id
    print(json.dumps(summary, indent=2))
    print(f"Sanitized evaluation report: {output_path}")
    if evaluation_exit_code(report) == 2:
        print("Automatic checks passed; human review is still required before release.")
    return evaluation_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
