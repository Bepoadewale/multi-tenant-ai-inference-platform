from __future__ import annotations

import asyncio
import os

import redis.asyncio as redis
from fastapi import HTTPException

from inference_gateway.capacity.redis_lua import ADMIT_LUA, RELEASE_LUA, RELEASE_QUEUE_LUA
from inference_gateway.models import (
    CapacityAllocation,
    CapacityDecision,
    CapacityPolicy,
    ModelDefinition,
    Tenant,
)


class RedisCapacityService:
    """Fail-closed capacity accounting shared by every local gateway replica.

    `simulated-l40s` is an accounting label only. The local runtime remains ONNX CPU.
    """

    def __init__(self, url: str) -> None:
        self.client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        self.pool = os.getenv("SIMULATED_GPU_POOL", "simulated-l40s")
        self.pool_slots = int(os.getenv("SIMULATED_GPU_POOL_SLOTS", "2"))
        self.queue_capacity = int(os.getenv("SIMULATED_GPU_QUEUE_CAPACITY", "2"))
        self.queue_wait_seconds = float(os.getenv("SIMULATED_GPU_QUEUE_WAIT_SECONDS", "0.50"))

    def _keys(self, tenant_id: str) -> list[str]:
        prefix = f"inference:capacity:{{{self.pool}}}"
        return [
            f"{prefix}:allocated",
            f"{prefix}:tenant:{tenant_id}:allocated",
            f"{prefix}:queued",
        ]

    async def admit(self, tenant: Tenant, model: ModelDefinition) -> CapacityAllocation:
        if model.capacity_policy == CapacityPolicy.CPU_ONLY or model.gpu_count == 0:
            return CapacityAllocation(decision=CapacityDecision.CPU_ONLY)
        queue_slot = False
        deadline = asyncio.get_running_loop().time() + self.queue_wait_seconds
        while True:
            try:
                result = await self.client.eval(
                    ADMIT_LUA,
                    3,
                    *self._keys(tenant.id),
                    self.pool_slots,
                    tenant.quotas.simulated_gpu_slots,
                    model.gpu_count,
                    "1" if model.capacity_policy == CapacityPolicy.ALLOW_CPU_FALLBACK else "0",
                    self.queue_capacity,
                    "1" if queue_slot else "0",
                )
            except redis.RedisError as error:
                raise HTTPException(503, "shared simulated GPU capacity unavailable") from error
            allowed, reason = int(result[0]), str(result[1])
            if allowed:
                break
            if reason == "queued":
                queue_slot = True
            elif reason == "tenant_quota":
                raise HTTPException(429, "simulated GPU tenant capacity quota exceeded")
            elif reason == "queue_full":
                raise HTTPException(429, "simulated GPU capacity queue full", headers={"Retry-After": "1"})
            if asyncio.get_running_loop().time() >= deadline:
                if queue_slot:
                    await self.release_queue_slot()
                raise HTTPException(429, "simulated GPU capacity queue wait exceeded", headers={"Retry-After": "1"})
            await asyncio.sleep(0.01)
        decision = (
            CapacityDecision.CPU_FALLBACK
            if reason == "cpu_fallback"
            else CapacityDecision.SIMULATED_GPU_ADMITTED
        )
        return CapacityAllocation(
            decision=decision,
            pool=self.pool,
            slots=model.gpu_count,
            simulated_hardware=True,
            queued=queue_slot,
        )

    async def release(self, tenant: Tenant, allocation: CapacityAllocation) -> None:
        if allocation.decision != CapacityDecision.SIMULATED_GPU_ADMITTED:
            return
        try:
            await self.client.eval(RELEASE_LUA, 2, *self._keys(tenant.id)[:2], allocation.slots)
        except redis.RedisError:
            # Inference already completed. Record the request rather than replacing its result.
            return

    async def release_queue_slot(self) -> None:
        try:
            await self.client.eval(RELEASE_QUEUE_LUA, 1, self._keys("_pool")[2])
        except redis.RedisError:
            return

    async def snapshot(self) -> dict:
        try:
            keys = self._keys("_pool")
            allocated = int(await self.client.get(keys[0]) or 0)
            queued = int(await self.client.get(keys[2]) or 0)
        except redis.RedisError as error:
            raise HTTPException(503, "shared simulated GPU capacity unavailable") from error
        return {
            "mode": "SIMULATED_HARDWARE_QUOTA_ACCOUNTING",
            "pools": [
                {
                    "name": self.pool,
                    "total_slots": self.pool_slots,
                    "allocated_slots": allocated,
                    "available_slots": max(0, self.pool_slots - allocated),
                    "queued_requests": queued,
                }
            ],
        }
