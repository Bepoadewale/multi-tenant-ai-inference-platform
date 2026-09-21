import json
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from inference_gateway.backends.mock import MockInferenceBackend
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.backends.vllm import VllmBackend
from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.service import TenantLimiter
from inference_gateway.metering.service import Meter
from inference_gateway.models import (
    AdminAuditEvent,
    ChatCompletionRequest,
    RolloutWeights,
    Tenant,
    Usage,
    UsageRecord,
)
from inference_gateway.observability.metrics import (
    ACTIVE,
    LATENCY,
    REQUESTS,
    THROTTLES,
    TOKENS,
    TTFT,
)
from inference_gateway.routing.router import Router


class GatewayService:
    def __init__(self) -> None:
        self.catalog, self.limiter, self.router, self.backend, self.meter = (
            Catalog(),
            TenantLimiter(),
            Router(),
            MockInferenceBackend(),
            Meter(),
        )
        self.onnx_backend = OnnxRuntimeBackend()
        self.admin_audit: list[AdminAuditEvent] = []

    def backend_for(self, model, target):
        if target.backend_url:
            return VllmBackend(target.backend_url, model.model_id)
        if model.runtime == "onnx":
            return self.onnx_backend
        return self.backend

    def update_rollout(self, actor: str, alias: str, update: RolloutWeights):
        model = self.catalog.models.get(alias)
        if not model:
            raise HTTPException(404, "unknown model alias")
        targets = {target.name: target for target in model.targets}
        if set(update.weights) != set(targets) or sum(update.weights.values()) != 100:
            raise HTTPException(422, "weights must cover every target and sum to 100")
        if any(weight < 0 for weight in update.weights.values()):
            raise HTTPException(422, "weights must be non-negative")
        if any(not targets[name].healthy and weight > 0 for name, weight in update.weights.items()):
            raise HTTPException(409, "cannot route traffic to an unhealthy target")
        for name, weight in update.weights.items():
            targets[name].weight = weight
        self.admin_audit.append(
            AdminAuditEvent(
                actor=actor,
                action="rollout.weights.updated",
                model=alias,
                details={name: str(weight) for name, weight in update.weights.items()},
            )
        )
        return model

    async def chat(self, tenant: Tenant, request: ChatCompletionRequest):
        request_id, started = str(uuid4()), perf_counter()
        model = self.catalog.models.get(request.model)
        if not model:
            raise HTTPException(404, "unknown model alias")
        # Authorize before consuming an admission quota; rejected model access cannot
        # deliberately exhaust a tenant's valid workload budget.
        target = self.router.choose(tenant, model, request_id)
        backend = self.backend_for(model, target)
        estimate = (
            sum(len(message.content.split()) for message in request.messages) + request.max_tokens
        )
        try:
            self.limiter.admit(tenant, estimate)
            ACTIVE.labels(tenant.id).inc()
        except HTTPException as error:
            THROTTLES.labels(tenant.id, error.detail).inc()
            raise
        if request.stream:
            return self._stream(
                tenant, request, target.name, target.version, request_id, started, backend
            )
        try:
            text, usage, ttft_ms = await backend.complete(request)
            self._record(
                tenant,
                request.model,
                target.name,
                target.version,
                request_id,
                usage,
                started,
                ttft_ms,
                False,
                "success",
            )
            return {
                "id": f"chatcmpl-{request_id}",
                "object": "chat.completion",
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": usage.model_dump(),
                "x_backend": target.name,
            }
        except Exception as error:
            REQUESTS.labels(tenant.id, request.model, "error").inc()
            raise HTTPException(502, "inference backend failed") from error
        finally:
            ACTIVE.labels(tenant.id).dec()
            self.limiter.release(tenant, 0)

    def _stream(self, tenant, request, backend_name, version, request_id, started, backend):
        async def events():
            usage = Usage(
                prompt_tokens=sum(len(message.content.split()) for message in request.messages),
                completion_tokens=0,
                total_tokens=0,
            )
            try:
                async for token in backend.stream(request):
                    usage.completion_tokens += 1
                    usage.total_tokens += 1
                    payload = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "choices": [
                            {"index": 0, "delta": {"content": token}, "finish_reason": None}
                        ],
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                self._record(
                    tenant,
                    request.model,
                    backend_name,
                    version,
                    request_id,
                    usage,
                    started,
                    2.0,
                    True,
                    "success",
                )
                yield "data: [DONE]\n\n"
            finally:
                ACTIVE.labels(tenant.id).dec()
                self.limiter.release(tenant, usage.total_tokens)

        return StreamingResponse(
            events(), media_type="text/event-stream", headers={"X-Request-ID": request_id}
        )

    def _record(
        self,
        tenant,
        model,
        backend,
        version,
        request_id,
        usage,
        started,
        ttft_ms,
        streaming,
        outcome,
    ):
        latency_ms = (perf_counter() - started) * 1000
        self.meter.record(
            UsageRecord(
                request_id=request_id,
                tenant_id=tenant.id,
                model=model,
                backend=backend,
                deployment_version=version,
                usage=usage,
                latency_ms=latency_ms,
                ttft_ms=ttft_ms,
                streaming=streaming,
                outcome=outcome,
            )
        )
        REQUESTS.labels(tenant.id, model, outcome).inc()
        TOKENS.labels(tenant.id, model, "prompt").inc(usage.prompt_tokens)
        TOKENS.labels(tenant.id, model, "completion").inc(usage.completion_tokens)
        LATENCY.labels(model).observe(latency_ms / 1000)
        TTFT.labels(model).observe(ttft_ms / 1000)


service = GatewayService()
