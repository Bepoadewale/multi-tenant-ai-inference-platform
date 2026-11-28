import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from inference_gateway.backends import vllm
from inference_gateway.backends.base import BackendStreamChunk
from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.service import TenantLimiter
from inference_gateway.metering.redis_service import RedisMeter
from inference_gateway.models import (
    ChatCompletionRequest,
    ChatMessage,
    StreamOptions,
    Usage,
    UsageRecord,
)
from inference_gateway.services.gateway import GatewayService


def chat_request(stream: bool = True, include_usage: bool = False) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model="chat-default",
        messages=[ChatMessage(role="user", content="hello platform")],
        max_tokens=8,
        stream=stream,
        stream_options=StreamOptions(include_usage=include_usage) if include_usage else None,
    )


def use_vllm_backend(service: GatewayService, backend: vllm.VllmBackend) -> None:
    service.catalog.models["chat-default"].runtime = "vllm"
    service.backend_for = lambda _model, _target: backend


def test_vllm_stream_requests_and_parses_final_usage(monkeypatch):
    seen = {}
    response_body = "".join(
        [
            'data: {"choices":[{"delta":{"content":"hello "}}]}\n\n',
            'data: {"choices":[{"delta":{"content":"world"}}]}\n\n',
            'data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2,"total_tokens":5}}\n\n',
            "data: [DONE]\n\n",
        ]
    )

    async def handle(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=response_body,
        )

    real_async_client = httpx.AsyncClient

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(vllm.httpx, "AsyncClient", client_with_mock)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def collect():
        return [event async for event in backend.stream(chat_request())]

    events = asyncio.run(collect())
    assert seen["payload"]["stream_options"] == {"include_usage": True}
    assert [event.content for event in events if event.content] == ["hello ", "world"]
    assert events[-1].usage == Usage(prompt_tokens=3, completion_tokens=2, total_tokens=5)


def test_vllm_stream_rejects_malformed_server_event(monkeypatch):
    async def handle(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"data: {not-json}\n\n",
        )

    real_async_client = httpx.AsyncClient

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(vllm.httpx, "AsyncClient", client_with_mock)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def collect():
        return [event async for event in backend.stream(chat_request())]

    with pytest.raises(RuntimeError, match="vLLM stream failed"):
        asyncio.run(collect())


def test_vllm_stream_rejects_upstream_error_event(monkeypatch):
    async def handle(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
                b'data: {"error":{"message":"engine failed"}}\n\n'
            ),
        )

    real_async_client = httpx.AsyncClient

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(vllm.httpx, "AsyncClient", client_with_mock)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")
    events = []

    async def collect():
        async for event in backend.stream(chat_request()):
            events.append(event)

    with pytest.raises(RuntimeError, match="vLLM stream failed"):
        asyncio.run(collect())
    assert [event.content for event in events if event.content] == ["partial"]


def test_gateway_uses_final_usage_and_measures_first_content_time():
    service = GatewayService()

    class UsageBackend:
        async def stream(self, _request):
            yield BackendStreamChunk(content="hello ")
            yield BackendStreamChunk(content="world")
            yield BackendStreamChunk(
                usage=Usage(prompt_tokens=3, completion_tokens=2, total_tokens=5)
            )

    service.backend_for = lambda _model, _target: UsageBackend()
    tenant = Catalog().tenant("team-search")

    async def consume():
        response = await service.chat(tenant, chat_request(include_usage=True))
        return [chunk async for chunk in response.body_iterator]

    chunks = asyncio.run(consume())
    record = service.meter.records[-1]
    assert "hello " in "".join(chunks)
    assert record.usage == Usage(prompt_tokens=3, completion_tokens=2, total_tokens=5)
    assert record.ttft_ms is not None
    assert record.outcome == "success"
    assert record.usage_source == "backend_reported"
    assert '"choices": [], "usage": {"prompt_tokens": 3' in "".join(chunks)


def test_gateway_records_cancelled_stream_and_releases_local_slots():
    service = GatewayService()

    class WaitingBackend:
        async def stream(self, _request):
            yield BackendStreamChunk(content="partial")
            await asyncio.Event().wait()

    service.backend_for = lambda _model, _target: WaitingBackend()
    tenant = Catalog().tenant("team-search")

    async def cancel_after_first_chunk():
        response = await service.chat(tenant, chat_request())
        stream = response.body_iterator
        await stream.__anext__()
        pending = asyncio.create_task(stream.__anext__())
        await asyncio.sleep(0)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        return service.meter.records[-1]

    record = asyncio.run(cancel_after_first_chunk())
    assert record.outcome == "cancelled"
    assert record.usage.completion_tokens == 1
    assert not service.limiter.active[tenant.id]


def test_gateway_records_stream_failure_and_releases_local_slots():
    service = GatewayService()

    class FailingBackend:
        async def stream(self, _request):
            yield BackendStreamChunk(content="partial output")
            raise RuntimeError("upstream connection ended")

    service.backend_for = lambda _model, _target: FailingBackend()
    tenant = Catalog().tenant("team-search")

    async def consume_until_failure():
        response = await service.chat(tenant, chat_request())
        async for _chunk in response.body_iterator:
            pass

    with pytest.raises(RuntimeError, match="inference stream failed"):
        asyncio.run(consume_until_failure())

    assert service.meter.records[-1].outcome == "stream_error"
    assert service.meter.records[-1].usage_source == "gateway_estimate"
    assert not service.limiter.active[tenant.id]


def test_gateway_hides_usage_chunk_when_client_did_not_request_it():
    service = GatewayService()

    class UsageBackend:
        async def stream(self, _request):
            yield BackendStreamChunk(content="hello")
            yield BackendStreamChunk(
                usage=Usage(prompt_tokens=3, completion_tokens=1, total_tokens=4)
            )

    service.backend_for = lambda _model, _target: UsageBackend()
    tenant = Catalog().tenant("team-search")

    async def consume():
        response = await service.chat(tenant, chat_request())
        return "".join([chunk async for chunk in response.body_iterator])

    body = asyncio.run(consume())
    assert '"usage":' not in body
    assert service.meter.records[-1].usage_source == "backend_reported"


def test_gateway_emits_estimated_usage_for_string_stream_backend():
    service = GatewayService()

    class StringBackend:
        async def stream(self, _request):
            yield "hello "
            yield "world"

    service.backend_for = lambda _model, _target: StringBackend()
    tenant = Catalog().tenant("team-search")

    async def consume():
        response = await service.chat(tenant, chat_request(include_usage=True))
        return "".join([chunk async for chunk in response.body_iterator])

    body = asyncio.run(consume())
    assert body.count('"choices": [], "usage":') == 1
    assert body.index('"choices": [], "usage":') < body.index("data: [DONE]")
    record = service.meter.records[-1]
    assert record.usage_source == "gateway_estimate"
    assert record.usage.completion_tokens == 2


def test_redis_meter_persists_usage_source():
    class Pipeline:
        def __init__(self):
            self.request_fields = None

        def xadd(self, _key, fields, **_kwargs):
            self.event_fields = fields

        def hset(self, key, mapping=None, *_args):
            if key.startswith("inference:usage-request:"):
                self.request_fields = mapping

        def expire(self, *_args):
            pass

        def hincrby(self, *_args):
            pass

        async def execute(self):
            return []

    class RedisClient:
        def __init__(self):
            self.commands = Pipeline()

        def pipeline(self, **_kwargs):
            return self.commands

    meter = RedisMeter.__new__(RedisMeter)
    meter.client = RedisClient()
    record = UsageRecord(
        tenant_id="team-search",
        model="chat-default",
        backend="vllm",
        deployment_version="candidate-1",
        usage=Usage(prompt_tokens=3, completion_tokens=1, total_tokens=4),
        usage_source="backend_reported",
        latency_ms=8.0,
        ttft_ms=2.0,
        streaming=True,
        outcome="success",
    )

    asyncio.run(meter.record(record))

    assert meter.client.commands.request_fields["usage_source"] == "backend_reported"
    assert meter.client.commands.event_fields["usage_source"] == "backend_reported"


def test_non_stream_backend_duration_is_not_reported_as_ttft():
    service = GatewayService()
    tenant = Catalog().tenant("team-search")

    asyncio.run(service.chat(tenant, chat_request(stream=False)))

    record = service.meter.records[-1]
    assert record.ttft_ms is None
    assert record.usage_source == "gateway_estimate"


def test_vllm_tokenizer_uses_chat_template_and_validates_response(monkeypatch):
    seen = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"count": 7, "max_model_len": 4096, "tokens": []})

    real_async_client = httpx.AsyncClient

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(vllm.httpx, "AsyncClient", client_with_mock)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    assert asyncio.run(backend.count_tokens(chat_request())) == (7, 4096)
    assert seen["url"].endswith("/tokenize")
    assert seen["payload"]["model"] == "qwen-test"
    assert seen["payload"]["messages"] == [{"role": "user", "content": "hello platform"}]
    assert seen["payload"]["add_generation_prompt"] is True
    assert seen["payload"]["return_token_strs"] is False


def test_vllm_tokenizer_rejects_malformed_response(monkeypatch):
    async def handle(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": "seven", "max_model_len": 4096})

    real_async_client = httpx.AsyncClient

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(vllm.httpx, "AsyncClient", client_with_mock)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    with pytest.raises(RuntimeError, match="vLLM tokenization request failed"):
        asyncio.run(backend.count_tokens(chat_request()))


def test_gateway_reserves_exact_prompt_and_output_cap_before_vllm_inference():
    service = GatewayService()
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def count_tokens(_request):
        return 11, 4096

    async def complete(_request):
        return "answer", Usage(prompt_tokens=11, completion_tokens=3, total_tokens=14), 1.0

    backend.count_tokens = count_tokens
    backend.complete = complete
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")

    response = asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert response["usage"]["total_tokens"] == 14
    assert sum(value for _, _, value in service.limiter.tokens[tenant.id]) == 14
    assert not service.limiter.active[tenant.id]


def test_onnx_model_with_http_target_does_not_call_vllm_tokenizer():
    """Only a model declared as vLLM needs the vLLM-specific tokenizer route."""
    service = GatewayService()
    backend = vllm.VllmBackend("http://onnx-runtime.test", "fixture-model")
    tokenizer_called = False

    async def count_tokens(_request):
        nonlocal tokenizer_called
        tokenizer_called = True
        raise RuntimeError("ONNX target has no vLLM tokenizer route")

    async def complete(_request):
        return (
            "classification=positive",
            Usage(prompt_tokens=2, completion_tokens=1, total_tokens=3),
            1.0,
        )

    backend.count_tokens = count_tokens
    backend.complete = complete
    service.backend_for = lambda _model, _target: backend
    tenant = Catalog().tenant("team-search")

    response = asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert response["choices"][0]["message"]["content"] == "classification=positive"
    assert tokenizer_called is False


def test_gateway_rejects_context_overflow_and_releases_preflight_reservation():
    service = GatewayService()
    service.catalog.models["chat-default"].max_model_len = 16
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def count_tokens(_request):
        return 11, 4096

    backend.count_tokens = count_tokens
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")

    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert rejected.value.status_code == 413
    assert sum(value for _, _, value in service.limiter.tokens[tenant.id]) == 0
    assert not service.limiter.active[tenant.id]
    assert service.capacity.pool_allocated == 0


def test_gateway_renews_admission_lease_during_slow_tokenizer_preflight():
    service = GatewayService()
    service.limiter = TenantLimiter(lease_seconds=0.03)
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def count_tokens(_request):
        await asyncio.sleep(0.1)
        return 2, 4096

    async def complete(_request):
        return "answer", Usage(prompt_tokens=2, completion_tokens=1, total_tokens=3), 1.0

    backend.count_tokens = count_tokens
    backend.complete = complete
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")

    response = asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert response["usage"]["total_tokens"] == 3
    assert not service.limiter.active[tenant.id]
    assert not service.limiter.reservations[tenant.id]


def test_gateway_fails_closed_when_vllm_tokenizer_is_unavailable():
    service = GatewayService()
    backend = vllm.VllmBackend("http://model.test", "qwen-test")

    async def fail_tokenizer(_request):
        raise RuntimeError("tokenizer endpoint unavailable")

    backend.count_tokens = fail_tokenizer
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")

    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert rejected.value.status_code == 503
    assert sum(value for _, _, value in service.limiter.tokens[tenant.id]) == 0
    assert not service.limiter.active[tenant.id]
    assert service.capacity.pool_allocated == 0


def test_gateway_enforces_tenant_prompt_limit_before_inference():
    service = GatewayService()
    backend = vllm.VllmBackend("http://model.test", "qwen-test")
    completed = False

    async def count_tokens(_request):
        return 21, 4096

    async def complete(_request):
        nonlocal completed
        completed = True
        return "answer", Usage(prompt_tokens=21, completion_tokens=1, total_tokens=22), 1.0

    backend.count_tokens = count_tokens
    backend.complete = complete
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")
    tenant.quotas.max_input_tokens = 20

    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert rejected.value.status_code == 413
    assert completed is False
    assert len(service.limiter.requests[tenant.id]) == 1
    assert sum(value for _, _, value in service.limiter.tokens[tenant.id]) == 0
    assert not service.limiter.active[tenant.id]
    assert service.capacity.pool_allocated == 0


def test_gateway_rejects_exact_token_reservation_before_inference():
    service = GatewayService()
    backend = vllm.VllmBackend("http://model.test", "qwen-test")
    completed = False

    async def count_tokens(_request):
        return 11, 4096

    async def complete(_request):
        nonlocal completed
        completed = True
        return "answer", Usage(prompt_tokens=11, completion_tokens=1, total_tokens=12), 1.0

    backend.count_tokens = count_tokens
    backend.complete = complete
    use_vllm_backend(service, backend)
    tenant = Catalog().tenant("team-search")
    tenant.quotas.tokens_per_minute = 18

    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert rejected.value.status_code == 429
    assert completed is False
    assert len(service.limiter.requests[tenant.id]) == 1
    assert sum(value for _, _, value in service.limiter.tokens[tenant.id]) == 0
    assert not service.limiter.active[tenant.id]
    assert service.capacity.pool_allocated == 0


def test_gateway_enforces_tenant_output_limit_before_admission():
    service = GatewayService()
    tenant = Catalog().tenant("team-search")
    tenant.quotas.max_output_tokens = 4

    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.chat(tenant, chat_request(stream=False)))

    assert rejected.value.status_code == 413
    assert not service.limiter.requests[tenant.id]
    assert service.capacity.pool_allocated == 0
