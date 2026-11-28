import asyncio
import inspect
import json
import os
from contextlib import suppress
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from inference_gateway.backends.base import BackendStreamChunk
from inference_gateway.backends.mock import MockInferenceBackend
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.backends.vllm import VllmBackend
from inference_gateway.capacity.redis_service import RedisCapacityService
from inference_gateway.capacity.service import CapacityService
from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.redis_service import RedisTenantLimiter
from inference_gateway.limiting.service import AdmissionReservation, TenantLimiter
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
        # Persist shared intent first. A Redis outage must not leave this process
        # routing with weights that its peer replicas cannot see.
        self.rollouts.put(alias, update.weights)
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
        release_context = self._apply_shared_rollout(model)
        # Authorize before consuming an admission quota; rejected model access cannot
        # deliberately exhaust a tenant's valid workload budget.
        target = self.router.choose(tenant, model, request_id)
        backend = self.backend_for(model, target)
        uses_vllm_tokenizer = model.runtime == "vllm"
        if uses_vllm_tokenizer and not isinstance(backend, VllmBackend):
            raise HTTPException(503, "vLLM backend unavailable")
        if request.max_tokens > tenant.quotas.max_output_tokens:
            raise HTTPException(413, "tenant output-token limit exceeded")
        estimate = 0 if uses_vllm_tokenizer else (
            sum(len(message.content.split()) for message in request.messages) + request.max_tokens
        )
        allocation = await self._admit_capacity(tenant, model)
        try:
            reservation = await self._admit(tenant, estimate, request_id)
            ACTIVE.labels(tenant.id).inc()
        except HTTPException as error:
            await self._release_capacity(tenant, allocation)
            THROTTLES.labels(tenant.id, error.detail).inc()
            raise
        preflight_lease_task = (
            self._start_lease_watch(tenant, reservation) if uses_vllm_tokenizer else None
        )
        if uses_vllm_tokenizer:
            try:
                prompt_tokens, server_context_limit = await backend.count_tokens(request)
                if prompt_tokens > tenant.quotas.max_input_tokens:
                    raise HTTPException(413, "tenant input-token limit exceeded")
                context_limit = min(model.max_model_len, server_context_limit)
                if prompt_tokens + request.max_tokens > context_limit:
                    raise HTTPException(413, "prompt and requested output exceed model context")
                reservation = await self._reserve_usage(
                    tenant, reservation, prompt_tokens + request.max_tokens
                )
            except asyncio.CancelledError:
                ACTIVE.labels(tenant.id).dec()
                await self._stop_lease_watch(preflight_lease_task)
                try:
                    await self._release(tenant, reservation, 0)
                finally:
                    await self._release_capacity(tenant, allocation)
                raise
            except HTTPException as error:
                ACTIVE.labels(tenant.id).dec()
                await self._stop_lease_watch(preflight_lease_task)
                try:
                    await self._release(tenant, reservation, 0)
                finally:
                    await self._release_capacity(tenant, allocation)
                if error.status_code == 429:
                    THROTTLES.labels(tenant.id, error.detail).inc()
                raise
            except Exception as error:
                ACTIVE.labels(tenant.id).dec()
                await self._stop_lease_watch(preflight_lease_task)
                try:
                    await self._release(tenant, reservation, 0)
                finally:
                    await self._release_capacity(tenant, allocation)
                raise HTTPException(503, "model tokenizer unavailable") from error
        if preflight_lease_task is not None:
            await self._stop_lease_watch(preflight_lease_task)
        if request.stream:
            return self._stream(
                tenant,
                request,
                target.name,
                target.version,
                request_id,
                started,
                backend,
                reservation,
                allocation,
                release_context,
            )
        actual_tokens = None
        lease_task = self._start_lease_watch(tenant, reservation)
        try:
            text, usage, _backend_duration_ms = await backend.complete(request)
            usage_source = (
                "backend_reported" if isinstance(backend, VllmBackend) else "gateway_estimate"
            )
            if usage_source == "backend_reported":
                actual_tokens = usage.total_tokens
            record = await self._record(
                tenant,
                request.model,
                target.name,
                target.version,
                request_id,
                usage,
                started,
                None,
                False,
                "success",
                release_context,
                usage_source=usage_source,
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
                usage_source="gateway_estimate",
            )
            raise HTTPException(
                502,
                "inference backend failed",
                headers={"X-Request-ID": request_id},
            ) from error
        finally:
            ACTIVE.labels(tenant.id).dec()
            await self._stop_lease_watch(lease_task)
            try:
                await self._release(tenant, reservation, actual_tokens)
            finally:
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
        reservation,
        allocation,
        release_context,
    ):
        async def events():
            usage = Usage(
                prompt_tokens=sum(len(message.content.split()) for message in request.messages),
                completion_tokens=0,
                total_tokens=sum(len(message.content.split()) for message in request.messages),
            )
            output_parts: list[str] = []
            measured_usage = False
            usage_emitted = False
            ttft_ms = None
            recorded = False
            actual_tokens = None
            lease_task = self._start_lease_watch(
                tenant, reservation, asyncio.current_task()
            )

            def update_estimated_usage() -> None:
                if not measured_usage:
                    usage.completion_tokens = len("".join(output_parts).split())
                    usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

            async def record(outcome: str) -> None:
                nonlocal recorded
                if recorded:
                    return
                # Set before awaiting so a metering error cannot cause duplicate records.
                recorded = True
                update_estimated_usage()
                await self._record(
                    tenant,
                    request.model,
                    backend_name,
                    version,
                    request_id,
                    usage,
                    started,
                    ttft_ms,
                    True,
                    outcome,
                    release_context,
                    usage_source=(
                        "backend_reported" if measured_usage else "gateway_estimate"
                    ),
                )

            try:
                async for event in backend.stream(request):
                    if isinstance(event, BackendStreamChunk):
                        if event.usage is not None:
                            usage = event.usage
                            measured_usage = True
                            actual_tokens = usage.total_tokens
                            if request.stream_options and request.stream_options.include_usage:
                                payload = {
                                    "id": f"chatcmpl-{request_id}",
                                    "object": "chat.completion.chunk",
                                    "choices": [],
                                    "usage": usage.model_dump(),
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
                                usage_emitted = True
                        content = event.content or ""
                    else:
                        content = event
                    if not content:
                        continue
                    output_parts.append(content)
                    if ttft_ms is None:
                        ttft_ms = (perf_counter() - started) * 1000
                    payload = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "choices": [
                            {"index": 0, "delta": {"content": content}, "finish_reason": None}
                        ],
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                await record("success")
                if (
                    request.stream_options
                    and request.stream_options.include_usage
                    and not usage_emitted
                ):
                    payload = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "choices": [],
                        "usage": usage.model_dump(),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                yield "data: [DONE]\n\n"
            except asyncio.CancelledError:
                await record("cancelled")
                raise
            except GeneratorExit:
                await record("cancelled")
                raise
            except Exception as error:
                await record("stream_error")
                raise RuntimeError("inference stream failed") from error
            finally:
                update_estimated_usage()
                ACTIVE.labels(tenant.id).dec()
                await self._stop_lease_watch(lease_task)
                try:
                    await self._release(tenant, reservation, actual_tokens)
                finally:
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

    async def _admit(
        self, tenant: Tenant, estimate: int, request_id: str
    ) -> AdmissionReservation:
        started = perf_counter()
        reservation = self.limiter.admit(tenant, estimate, request_id)
        if inspect.isawaitable(reservation):
            reservation = await reservation
        QUEUE.labels(tenant.id).set(0)
        QUEUE_WAIT.labels(tenant.id).observe(perf_counter() - started)
        return reservation

    async def _reserve_usage(
        self, tenant: Tenant, reservation: AdmissionReservation, estimated_tokens: int
    ) -> AdmissionReservation:
        result = self.limiter.reserve_usage(tenant, reservation, estimated_tokens)
        return await result if inspect.isawaitable(result) else result

    async def _release(
        self,
        tenant: Tenant,
        reservation: AdmissionReservation,
        actual_tokens: int | None,
    ) -> None:
        result = self.limiter.release(tenant, reservation, actual_tokens)
        if inspect.isawaitable(result):
            await result

    def _start_lease_watch(
        self,
        tenant: Tenant,
        reservation: AdmissionReservation,
        owner_task: asyncio.Task | None = None,
    ) -> asyncio.Task:
        owner_task = owner_task or asyncio.current_task()
        if owner_task is None:
            raise RuntimeError("admitted inference request has no owning asyncio task")
        return asyncio.create_task(self._maintain_lease(tenant, reservation, owner_task))

    async def _maintain_lease(
        self,
        tenant: Tenant,
        reservation: AdmissionReservation,
        owner_task: asyncio.Task,
    ) -> None:
        renew = getattr(self.limiter, "renew", None)
        if renew is None:
            return
        interval = float(self.limiter.lease_seconds) / 3
        while True:
            await asyncio.sleep(interval)
            try:
                renewed = renew(tenant, reservation)
                if inspect.isawaitable(renewed):
                    # A blocked Redis command must not outlive the lease it renews.
                    # Sleep plus this deadline uses at most two thirds of the lease,
                    # leaving time to cancel the owner before another gateway can
                    # safely reuse the expired concurrency slot.
                    renewed = await asyncio.wait_for(renewed, timeout=interval)
            except Exception:
                owner_task.cancel()
                return
            if not renewed:
                owner_task.cancel()
                return

    @staticmethod
    async def _stop_lease_watch(lease_task: asyncio.Task | None) -> None:
        if lease_task is None:
            return
        lease_task.cancel()
        with suppress(asyncio.CancelledError):
            await lease_task

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
        usage_source="gateway_estimate",
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
            usage_source=usage_source,
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

    async def readiness(self) -> dict[str, object]:
        """Check the routed inference backend and shared admission state."""
        model = self.catalog.model("chat-default")
        target = next((item for item in model.targets if item.healthy and item.weight > 0), None)
        backend_ready = False
        if target is not None:
            backend = self.backend_for(model, target)
            health = getattr(backend, "health", None)
            if health is not None:
                result = health()
                backend_ready = await result if inspect.isawaitable(result) else bool(result)
            else:
                backend_ready = True
        try:
            await self.capacity_snapshot()
            admission_ready = True
        except HTTPException:
            admission_ready = False
        ready = backend_ready and admission_ready
        return {
            "status": "ok" if ready else "not_ready",
            "runtime": model.runtime,
            "model": model.model_id,
            "backend_ready": backend_ready,
            "admission_ready": admission_ready,
        }

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
