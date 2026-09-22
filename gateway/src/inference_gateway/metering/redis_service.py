from __future__ import annotations

import redis.asyncio as redis
from inference_gateway.models import UsageRecord


class RedisMeter:
    """Durable, metadata-only usage store shared by local gateway replicas."""

    def __init__(self, url: str) -> None:
        self.client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)

    @staticmethod
    def _summary_key(tenant_id: str) -> str:
        return f"inference:usage:{tenant_id}"

    async def record(self, record: UsageRecord) -> None:
        fields = {
            "request_id": str(record.request_id),
            "tenant_id": record.tenant_id,
            "model": record.model,
            "backend": record.backend,
            "version": record.deployment_version,
            "total_tokens": str(record.usage.total_tokens),
            "latency_ms": f"{record.latency_ms:.3f}",
            "outcome": record.outcome,
        }
        pipeline = self.client.pipeline(transaction=True)
        pipeline.xadd("inference:usage-events", fields, maxlen=10_000, approximate=True)
        pipeline.hincrby(self._summary_key(record.tenant_id), "requests", 1)
        pipeline.hincrby(self._summary_key(record.tenant_id), "tokens", record.usage.total_tokens)
        pipeline.hset(self._summary_key(record.tenant_id), "tenant", record.tenant_id)
        await pipeline.execute()

    async def tenant_summary(self, tenant_id: str) -> dict:
        summary = await self.client.hgetall(self._summary_key(tenant_id))
        tokens = int(summary.get("tokens", "0"))
        return {
            "tenant": tenant_id,
            "requests": int(summary.get("requests", "0")),
            "tokens": tokens,
            "estimated_cost_usd": round(tokens / 1_000_000 * 0.80, 6),
            "note": "estimate only; metadata-only local usage record, not a billing record",
        }
