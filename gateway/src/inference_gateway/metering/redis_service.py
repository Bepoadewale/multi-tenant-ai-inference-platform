from __future__ import annotations

import redis.asyncio as redis
from inference_gateway.models import Usage, UsageRecord


class RedisMeter:
    """Durable, metadata-only usage store shared by local gateway replicas."""

    def __init__(self, url: str) -> None:
        self.client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)

    @staticmethod
    def _summary_key(tenant_id: str) -> str:
        return f"inference:usage:{tenant_id}"

    @staticmethod
    def _request_key(request_id: str) -> str:
        return f"inference:usage-request:{request_id}"

    async def record(self, record: UsageRecord) -> None:
        fields = {
            "request_id": str(record.request_id),
            "tenant_id": record.tenant_id,
            "model": record.model,
            "backend": record.backend,
            "version": record.deployment_version,
            "timestamp": record.timestamp.isoformat(),
            "prompt_tokens": str(record.usage.prompt_tokens),
            "completion_tokens": str(record.usage.completion_tokens),
            "total_tokens": str(record.usage.total_tokens),
            "latency_ms": f"{record.latency_ms:.3f}",
            "ttft_ms": "" if record.ttft_ms is None else f"{record.ttft_ms:.3f}",
            "streaming": str(record.streaming).lower(),
            "outcome": record.outcome,
            "trace_id": record.trace_id or "",
            "release_plan_id": record.release_plan_id or "",
            "release_phase": record.release_phase or "",
        }
        pipeline = self.client.pipeline(transaction=True)
        pipeline.xadd("inference:usage-events", fields, maxlen=10_000, approximate=True)
        pipeline.hset(self._request_key(str(record.request_id)), mapping=fields)
        pipeline.expire(self._request_key(str(record.request_id)), 7 * 24 * 60 * 60)
        pipeline.hincrby(self._summary_key(record.tenant_id), "requests", 1)
        pipeline.hincrby(self._summary_key(record.tenant_id), "tokens", record.usage.total_tokens)
        pipeline.hset(self._summary_key(record.tenant_id), "tenant", record.tenant_id)
        await pipeline.execute()

    async def get_request(self, request_id: str) -> UsageRecord | None:
        fields = await self.client.hgetall(self._request_key(request_id))
        if not fields:
            return None
        return UsageRecord(
            request_id=fields["request_id"],
            tenant_id=fields["tenant_id"],
            model=fields["model"],
            backend=fields["backend"],
            deployment_version=fields["version"],
            timestamp=fields["timestamp"],
            usage=Usage(
                prompt_tokens=int(fields["prompt_tokens"]),
                completion_tokens=int(fields["completion_tokens"]),
                total_tokens=int(fields["total_tokens"]),
            ),
            latency_ms=float(fields["latency_ms"]),
            ttft_ms=float(fields["ttft_ms"]) if fields.get("ttft_ms") else None,
            streaming=fields.get("streaming") == "true",
            outcome=fields["outcome"],
            trace_id=fields.get("trace_id") or None,
            release_plan_id=fields.get("release_plan_id") or None,
            release_phase=fields.get("release_phase") or None,
        )

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
