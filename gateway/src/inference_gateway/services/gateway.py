import inspect
import json
import os
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from inference_gateway.backends.mock import MockInferenceBackend
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.backends.vllm import VllmBackend
from inference_gateway.capacity.redis_service import RedisCapacityService
from inference_gateway.capacity.service import CapacityService
from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.redis_service import RedisTenantLimiter
from inference_gateway.limiting.service import TenantLimiter
from inference_gateway.metering.redis_service import RedisMeter
from inference_gateway.metering.service import Meter
from inference_gateway.models import (
    AdminAuditEvent,
    CapacityAllocation,
    ChatCompletionRequest,
    RolloutWeights,
    Tenant,
    Usage,
    UsageRecord,
)
from inference_gateway.observability.metrics import (
    ACTIVE,
    CAPACITY_ALLOCATED,
    CAPACITY_DECISIONS,
    CAPACITY_QUEUE,
    CAPACITY_TENANT_ALLOCATED,
    ESTIMATED_COST,
    LATENCY,
    QUEUE,
    QUEUE_WAIT,
    RELEASE_CORRELATED_REQUESTS,
    REQUESTS,
    SLO_EVALUATIONS,
    THROTTLES,
    TOKENS,
    TTFT,
)
from inference_gateway.operations.service import analyse, estimate_cost, evaluate_slo
from inference_gateway.routing.rollout_store import RolloutStore
from inference_gateway.routing.router import Router
from opentelemetry import trace


class GatewayService:
    def __init__(self) -> None:
        self.catalog = Catalog()
        redis_url = os.getenv("REDIS_URL")
        self.limiter = RedisTenantLimiter(redis_url) if redis_url else TenantLimiter()
        self.capacity = RedisCapacityService(redis_url) if redis_url else CapacityService()
        self.router, self.backend = Router(), MockInferenceBackend()
        self.rollouts = RolloutStore(redis_url)
        self.meter = RedisMeter(redis_url) if redis_url else Meter()
        self.onnx_backend = OnnxRuntimeBackend()
        self.admin_audit: list[AdminAuditEvent] = []

    def backend_for(self, model, target):
        if target.backend_url:
            return VllmBackend(target.backend_url, model.model_id, target.timeout_seconds)
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
        self.rollouts.put(alias, update.weights)
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
        release_context = self._apply_shared_rollout(model)
        # Authorize before consuming an admission quota; rejected model access cannot
        # deliberately exhaust a tenant's valid workload budget.
        target = self.router.choose(tenant, model, request_id)
        backend = self.backend_for(model, target)
        estimate = (
            sum(len(message.content.split()) for message in request.messages) + request.max_tokens
        )
        allocation = await self._admit_capacity(tenant, model)
        try:
            await self._admit(tenant, estimate)
            ACTIVE.labels(tenant.id).inc()
        except HTTPException as error:
            await self._release_capacity(tenant, allocation)
            THROTTLES.labels(tenant.id, error.detail).inc()
            raise
        if request.stream:
            return self._stream(
                tenant,
                request,
                target.name,
                target.version,
                request_id,
                started,
                backend,
                allocation,
                release_context,
            )
        try:
            text, usage, ttft_ms = await backend.complete(request)
            record = await self._record(
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
                release_context,
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
                "x_capacity": allocation.model_dump(),
                "x_observability": {
                    "request_id": request_id,
                    "trace_id": record.trace_id,
                    "release_plan_id": record.release_plan_id,
                },
            }
        except Exception as error:
            failure_usage = Usage(
                prompt_tokens=sum(len(message.content.split()) for message in request.messages),
                completion_tokens=0,
                total_tokens=sum(len(message.content.split()) for message in request.messages),
            )
            await self._record(
                tenant,
                request.model,
                target.name,
                target.version,
                request_id,
                failure_usage,
                started,
                None,
                False,
                "backend_error",
                release_context,
            )
            raise HTTPException(
                502,
                "inference backend failed",
                headers={"X-Request-ID": request_id},
            ) from error
        finally:
            ACTIVE.labels(tenant.id).dec()
            await self._release(tenant, 0)
            await self._release_capacity(tenant, allocation)

    def _stream(
        self,
        tenant,
        request,
        backend_name,
        version,
        request_id,
        started,
        backend,
        allocation,
        release_context,
    ):
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
                await self._record(
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
                    release_context,
                )
                yield "data: [DONE]\n\n"
            finally:
                ACTIVE.labels(tenant.id).dec()
                await self._release(tenant, usage.total_tokens)
                await self._release_capacity(tenant, allocation)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={
                "X-Request-ID": request_id,
                "X-Capacity-Decision": allocation.decision,
                "X-Capacity-Hardware": "simulated" if allocation.simulated_hardware else "cpu",
            },
        )

    async def _admit_capacity(self, tenant: Tenant, model) -> CapacityAllocation:
        try:
            result = self.capacity.admit(tenant, model)
            allocation = await result if inspect.isawaitable(result) else result
        except HTTPException as error:
            CAPACITY_DECISIONS.labels(tenant.id, model.gpu_type or "cpu", "REJECTED").inc()
            raise error
        pool = allocation.pool or "cpu"
        CAPACITY_DECISIONS.labels(tenant.id, pool, allocation.decision).inc()
        if allocation.decision.value == "SIMULATED_GPU_ADMITTED":
            CAPACITY_ALLOCATED.labels(pool).inc(allocation.slots)
            CAPACITY_TENANT_ALLOCATED.labels(tenant.id, pool).inc(allocation.slots)
        if allocation.queued:
            CAPACITY_DECISIONS.labels(tenant.id, pool, "QUEUED").inc()
            CAPACITY_QUEUE.labels(pool).set(0)
        return allocation

    async def _release_capacity(self, tenant: Tenant, allocation: CapacityAllocation) -> None:
        result = self.capacity.release(tenant, allocation)
        if inspect.isawaitable(result):
            await result
        if allocation.decision.value == "SIMULATED_GPU_ADMITTED":
            CAPACITY_ALLOCATED.labels(allocation.pool).dec(allocation.slots)
            CAPACITY_TENANT_ALLOCATED.labels(tenant.id, allocation.pool).dec(allocation.slots)

    async def _admit(self, tenant: Tenant, estimate: int) -> None:
        started = perf_counter()
        result = self.limiter.admit(tenant, estimate)
        if inspect.isawaitable(result):
            await result
        QUEUE.labels(tenant.id).set(0)
        QUEUE_WAIT.labels(tenant.id).observe(perf_counter() - started)

    async def _release(self, tenant: Tenant, actual_tokens: int) -> None:
        result = self.limiter.release(tenant, actual_tokens)
        if inspect.isawaitable(result):
            await result

    async def _record(
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
        release_context=None,
    ):
        latency_ms = (perf_counter() - started) * 1000
        trace_context = trace.get_current_span().get_span_context()
        trace_id = f"{trace_context.trace_id:032x}" if trace_context.is_valid else None
        record = UsageRecord(
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
            trace_id=trace_id,
            release_plan_id=(release_context or {}).get("release_plan_id"),
            release_phase=(release_context or {}).get("release_phase"),
        )
        result = self.meter.record(record)
        if inspect.isawaitable(result):
            await result
        REQUESTS.labels(tenant.id, model, outcome).inc()
        TOKENS.labels(tenant.id, model, "prompt").inc(usage.prompt_tokens)
        TOKENS.labels(tenant.id, model, "completion").inc(usage.completion_tokens)
        LATENCY.labels(model).observe(latency_ms / 1000)
        if ttft_ms is not None:
            TTFT.labels(model).observe(ttft_ms / 1000)
        cost = estimate_cost(record)
        ESTIMATED_COST.labels(tenant.id, model, cost["pricing_version"]).inc(
            float(cost["total_cost_usd"])
        )
        slo = evaluate_slo(record)
        SLO_EVALUATIONS.labels(model, slo["status"]).inc()
        if record.release_plan_id:
            RELEASE_CORRELATED_REQUESTS.labels(model, record.release_phase or "UNKNOWN").inc()
        return record

    async def tenant_usage(self, tenant_id: str) -> dict:
        result = self.meter.tenant_summary(tenant_id)
        return await result if inspect.isawaitable(result) else result

    async def capacity_snapshot(self) -> dict:
        result = self.capacity.snapshot()
        return await result if inspect.isawaitable(result) else result

    async def request_analysis(self, request_id: str) -> dict | None:
        result = self.meter.get_request(request_id)
        record = await result if inspect.isawaitable(result) else result
        return analyse(record) if record else None

    def _apply_shared_rollout(self, model) -> dict[str, object] | None:
        """Read validated release intent immediately before routing live traffic."""
        weights = self.rollouts.get(model.name)
        if weights is None:
            return None
        targets = {target.name: target for target in model.targets}
        if set(weights) != set(targets) or sum(weights.values()) != 100:
            return None
        if any(weight < 0 or (weight > 0 and not targets[name].healthy) for name, weight in weights.items()):
            return None
        for name, weight in weights.items():
            targets[name].weight = weight
        return self.rollouts.get_context(model.name)


service = GatewayService()
