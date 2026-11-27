import asyncio
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

import benchmarks.gpu_inference.run_gateway_benchmark as benchmark
from benchmarks.gpu_inference.run_gateway_benchmark import percentile, request_one, summarize


def test_gateway_benchmark_summary_reports_admission_and_latency_only():
    rows = [
        {
            "tenant": "customer-support",
            "status": 200,
            "latency_ms": 10.0,
            "client_queue_wait_ms": 0.0,
            "prompt_tokens": 4,
            "completion_tokens": 2,
        },
        {
            "tenant": "research",
            "status": 429,
            "latency_ms": 30.0,
            "client_queue_wait_ms": 4.0,
        },
        {
            "tenant": "internal-engineering",
            "status": 200,
            "latency_ms": 20.0,
            "client_queue_wait_ms": 2.0,
            "prompt_tokens": 5,
            "completion_tokens": 3,
        },
    ]

    report = summarize(rows, elapsed_seconds=2.0)

    assert report["requests"] == 3
    assert report["successful"] == 2
    assert report["failed"] == 1
    assert report["status_counts"] == {"200": 2, "429": 1}
    assert report["successful_requests_per_second"] == 1.0
    assert report["reported_prompt_tokens"] == 9
    assert report["reported_completion_tokens"] == 5
    assert "READY" not in repr(report)
    assert "Bearer" not in repr(report)


def test_percentile_handles_empty_and_single_sample():
    assert percentile([], 0.5) is None
    assert percentile([7.25], 0.95) == 7.25
    assert percentile([0.0, 10.0], 0.95) == 9.5


def test_benchmark_client_discards_prompt_response_and_auth_header(monkeypatch):
    seen = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps(
                {
                "choices": [{"message": {"content": "private-completion-sentinel"}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2},
                }
            ).encode()

    class Opener:
        def open(self, request, timeout):
            seen["authorization"] = request.get_header("Authorization")
            seen["body"] = request.data.decode()
            seen["timeout"] = timeout
            return Response()

    def make_opener(handler):
        seen["handler"] = handler
        return Opener()

    monkeypatch.setattr(benchmark, "build_opener", make_opener)

    async def exercise():
        return await request_one(
                "https://gateway.example",
                "chat-default",
                "customer-support",
                "private-bearer-sentinel",
                asyncio.Semaphore(1),
                5,
            )

    row = asyncio.run(exercise())

    assert row["status"] == 200
    assert row["prompt_tokens"] == 4
    assert row["completion_tokens"] == 2
    assert seen["authorization"] == "Bearer private-bearer-sentinel"
    assert "Reply with the single word READY." in seen["body"]
    assert seen["timeout"] == 5
    assert isinstance(seen["handler"], benchmark.RejectRedirect)
    assert "private-bearer-sentinel" not in repr(row)
    assert "private-completion-sentinel" not in repr(row)


def test_redirect_handler_refuses_to_forward_tenant_token():
    request = Request("https://gateway.example/v1/chat/completions")

    with pytest.raises(HTTPError, match="redirect refused"):
        benchmark.RejectRedirect().redirect_request(
            request, None, 302, "Found", {}, "https://other.example/collect"
        )
