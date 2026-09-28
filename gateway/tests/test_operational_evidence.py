import asyncio

from inference_gateway.catalog.store import Catalog
from inference_gateway.models import ChatCompletionRequest, ChatMessage, Usage, UsageRecord
from inference_gateway.operations.service import analyse, estimate_cost, evaluate_slo
from inference_gateway.services.gateway import GatewayService


def _record(**overrides) -> UsageRecord:
    values = {
        "tenant_id": "team-search",
        "model": "chat-default",
        "backend": "onnx-candidate-v2",
        "deployment_version": "v2",
        "usage": Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        "latency_ms": 120.0,
        "ttft_ms": 80.0,
        "streaming": False,
        "outcome": "success",
        "trace_id": "a" * 32,
        "release_plan_id": "release-123",
        "release_phase": "CANARY",
    }
    values.update(overrides)
    return UsageRecord(**values)


def test_request_analysis_is_release_aware_and_keeps_content_private():
    analysis = analyse(_record())
    assert analysis["release"] == {"plan_id": "release-123", "phase_at_request": "CANARY"}
    assert analysis["trace_id"] == "a" * 32
    assert analysis["slo"]["status"] == "SATISFIED"
    assert analysis["privacy"] == {
        "raw_prompt_stored": False,
        "raw_completion_stored": False,
        "record_type": "metadata-only",
    }
    assert "messages" not in str(analysis)


def test_cost_estimate_uses_versioned_decimal_fixture_prices():
    cost = estimate_cost(_record())
    assert cost["pricing_version"] == "local-fixture-2026-09-v1"
    assert cost["prompt_cost_usd"] == "0.00002000"
    assert cost["completion_cost_usd"] == "0.00004000"
    assert cost["total_cost_usd"] == "0.00006000"


def test_backend_failure_violates_the_local_request_slo():
    slo = evaluate_slo(_record(outcome="backend_error", ttft_ms=None))
    assert slo["status"] == "VIOLATED"
    assert slo["reasons"] == ["outcome=backend_error"]


def test_in_memory_gateway_exposes_completed_request_evidence():
    service = GatewayService()
    response = asyncio.run(
        service.chat(
            Catalog().tenant("team-search"),
            ChatCompletionRequest(
                model="chat-default",
                messages=[ChatMessage(role="user", content="metadata-only analysis")],
            ),
        )
    )
    request_id = response["x_observability"]["request_id"]
    analysis = asyncio.run(service.request_analysis(request_id))
    assert analysis is not None
    assert analysis["request_id"] == request_id
    assert analysis["cost"]["kind"] == "ESTIMATED_LOCAL_TOKEN_ALLOCATION"
