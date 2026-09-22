from __future__ import annotations

import asyncio
import os
from time import time_ns

import redis.asyncio as redis
from fastapi import HTTPException
from inference_gateway.limiting.redis_lua import ADMISSION_LUA, RELEASE_LUA, RELEASE_QUEUE_LUA
from inference_gateway.models import Tenant


class RedisTenantLimiter:
    """Shared, fail-closed admission with a bounded wait queue."""

    def __init__(self, url: str) -> None:
        self.client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        self.queue_capacity = int(os.getenv("INFERENCE_QUEUE_CAPACITY", "8"))
        self.queue_wait_seconds = float(os.getenv("INFERENCE_QUEUE_WAIT_SECONDS", "0.25"))

    @staticmethod
    def _keys(tenant_id: str) -> list[str]:
        prefix = f"inference:{{{tenant_id}}}"
        return [f"{prefix}:requests", f"{prefix}:tokens", f"{prefix}:active", f"{prefix}:daily", f"{prefix}:queued"]

    async def admit(self, tenant: Tenant, estimated_tokens: int) -> None:
        request_id = str(time_ns())
        queue_slot = False
        deadline = asyncio.get_running_loop().time() + self.queue_wait_seconds
        while True:
            try:
                result = await self.client.eval(
                    ADMISSION_LUA,
                    5,
                    *self._keys(tenant.id),
                    time_ns() // 1_000_000,
                    60_000,
                    tenant.quotas.requests_per_minute,
                    tenant.quotas.tokens_per_minute,
                    tenant.quotas.concurrent_requests,
                    tenant.quotas.daily_token_quota,
                    estimated_tokens,
                    request_id,
                    self.queue_capacity,
                    "1" if queue_slot else "0",
                )
            except redis.RedisError as error:
                raise HTTPException(503, "shared admission unavailable") from error
            allowed, reason = int(result[0]), str(result[1])
            if allowed:
                return
            if reason == "queued":
                queue_slot = True
            elif reason != "waiting_for_capacity":
                if queue_slot:
                    await self.release_queue_slot(tenant)
                raise HTTPException(429, f"tenant {reason} quota exceeded")
            if asyncio.get_running_loop().time() >= deadline:
                if queue_slot:
                    await self.release_queue_slot(tenant)
                raise HTTPException(429, "tenant queue wait exceeded", headers={"Retry-After": "1"})
            await asyncio.sleep(0.01)

    async def release(self, tenant: Tenant, actual_tokens: int) -> None:
        try:
            await self.client.eval(RELEASE_LUA, 1, self._keys(tenant.id)[2])
        except redis.RedisError:
            # The request has completed; do not turn an already-produced response into an error.
            return

    async def release_queue_slot(self, tenant: Tenant) -> None:
        try:
            await self.client.eval(RELEASE_QUEUE_LUA, 1, self._keys(tenant.id)[4])
        except redis.RedisError:
            return

    async def close(self) -> None:
        await self.client.aclose()
