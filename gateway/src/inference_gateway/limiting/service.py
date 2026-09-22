from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from inference_gateway.models import Tenant


class TenantLimiter:
    """Local deterministic limiter. Redis Lua scripts provide this atomically across replicas in production."""

    def __init__(self) -> None:
        self.requests: dict[str, deque[datetime]] = defaultdict(deque)
        self.tokens: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)
        self.active: dict[str, int] = defaultdict(int)
        self.daily: dict[str, int] = defaultdict(int)

    def admit(self, tenant: Tenant, estimated_tokens: int) -> None:
        now, floor = datetime.now(UTC), datetime.now(UTC) - timedelta(minutes=1)
        reqs, tokens = self.requests[tenant.id], self.tokens[tenant.id]
        while reqs and reqs[0] < floor:
            reqs.popleft()
        while tokens and tokens[0][0] < floor:
            tokens.popleft()
        if len(reqs) >= tenant.quotas.requests_per_minute:
            raise HTTPException(
                429, "tenant requests-per-minute quota exceeded", headers={"Retry-After": "60"}
            )
        if sum(value for _, value in tokens) + estimated_tokens > tenant.quotas.tokens_per_minute:
            raise HTTPException(
                429, "tenant tokens-per-minute quota exceeded", headers={"Retry-After": "60"}
            )
        if self.active[tenant.id] >= tenant.quotas.concurrent_requests:
            raise HTTPException(429, "tenant concurrent-request quota exceeded")
        if self.daily[tenant.id] + estimated_tokens > tenant.quotas.daily_token_quota:
            raise HTTPException(429, "tenant daily token quota exceeded")
        reqs.append(now)
        tokens.append((now, estimated_tokens))
        self.active[tenant.id] += 1
        self.daily[tenant.id] += estimated_tokens

    def release(self, tenant: Tenant, actual_tokens: int) -> None:
        self.active[tenant.id] = max(0, self.active[tenant.id] - 1)
        # Reserve the estimated daily budget at admission so concurrent requests cannot
        # oversubscribe it. Actual usage remains in the privacy-safe metering record.
