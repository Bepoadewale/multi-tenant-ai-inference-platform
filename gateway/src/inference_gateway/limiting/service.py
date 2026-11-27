from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from inference_gateway.models import Tenant


@dataclass(frozen=True)
class AdmissionReservation:
    request_id: str
    estimated_tokens: int


class TenantLimiter:
    """Local deterministic limiter. Redis Lua scripts provide this atomically across replicas in production."""

    def __init__(self, lease_seconds: float = 120) -> None:
        self.lease_seconds = lease_seconds
        self.requests: dict[str, deque[tuple[datetime, str]]] = defaultdict(deque)
        self.tokens: dict[str, deque[tuple[datetime, str, int]]] = defaultdict(deque)
        self.active: dict[str, set[str]] = defaultdict(set)
        self.reservations: dict[str, dict[str, tuple[int, datetime]]] = defaultdict(dict)
        self.daily: dict[str, deque[tuple[datetime, str, int]]] = defaultdict(deque)

    def _prune(self, tenant_id: str, now: datetime) -> None:
        floor = now - timedelta(minutes=1)
        day_floor = now - timedelta(days=1)
        reqs, tokens = self.requests[tenant_id], self.tokens[tenant_id]
        while reqs and reqs[0][0] < floor:
            reqs.popleft()
        while tokens and tokens[0][0] < floor:
            tokens.popleft()
        daily = self.daily[tenant_id]
        while daily and daily[0][0] < day_floor:
            daily.popleft()
        expired = [
            request_id
            for request_id, (_estimate, expires_at) in self.reservations[tenant_id].items()
            if expires_at <= now
        ]
        for request_id in expired:
            self.reservations[tenant_id].pop(request_id, None)
            self.active[tenant_id].discard(request_id)

    def admit(
        self, tenant: Tenant, estimated_tokens: int, request_id: str | None = None
    ) -> AdmissionReservation:
        now = datetime.now(UTC)
        self._prune(tenant.id, now)
        request_id = request_id or str(uuid4())
        reqs, tokens = self.requests[tenant.id], self.tokens[tenant.id]
        if len(reqs) >= tenant.quotas.requests_per_minute:
            raise HTTPException(
                429, "tenant requests-per-minute quota exceeded", headers={"Retry-After": "60"}
            )
        if sum(value for _, _, value in tokens) + estimated_tokens > tenant.quotas.tokens_per_minute:
            raise HTTPException(
                429, "tenant tokens-per-minute quota exceeded", headers={"Retry-After": "60"}
            )
        if len(self.active[tenant.id]) >= tenant.quotas.concurrent_requests:
            raise HTTPException(429, "tenant concurrent-request quota exceeded")
        if sum(value for _, _, value in self.daily[tenant.id]) + estimated_tokens > tenant.quotas.daily_token_quota:
            raise HTTPException(429, "tenant daily token quota exceeded")
        reqs.append((now, request_id))
        tokens.append((now, request_id, estimated_tokens))
        self.daily[tenant.id].append((now, request_id, estimated_tokens))
        self.active[tenant.id].add(request_id)
        self.reservations[tenant.id][request_id] = (
            estimated_tokens,
            now + timedelta(seconds=self.lease_seconds),
        )
        return AdmissionReservation(request_id, estimated_tokens)

    def renew(self, tenant: Tenant, reservation: AdmissionReservation) -> bool:
        current = self.reservations[tenant.id].get(reservation.request_id)
        if current is None:
            return False
        self.reservations[tenant.id][reservation.request_id] = (
            current[0],
            datetime.now(UTC) + timedelta(seconds=self.lease_seconds),
        )
        return True

    def reserve_usage(
        self, tenant: Tenant, reservation: AdmissionReservation, estimated_tokens: int
    ) -> AdmissionReservation:
        if estimated_tokens < 0:
            raise ValueError("estimated_tokens must not be negative")
        now = datetime.now(UTC)
        self._prune(tenant.id, now)
        current = self.reservations[tenant.id].get(reservation.request_id)
        if current is None:
            raise HTTPException(503, "admission reservation expired")

        minute_entries, daily_entries = self.tokens[tenant.id], self.daily[tenant.id]
        minute_total = sum(value for _, _, value in minute_entries) - self._amount(
            minute_entries, reservation.request_id
        )
        if minute_total + estimated_tokens > tenant.quotas.tokens_per_minute:
            raise HTTPException(429, "tenant tokens-per-minute quota exceeded")
        daily_total = sum(value for _, _, value in daily_entries) - self._amount(
            daily_entries, reservation.request_id
        )
        if daily_total + estimated_tokens > tenant.quotas.daily_token_quota:
            raise HTTPException(429, "tenant daily token quota exceeded")

        self._set_amount(minute_entries, reservation.request_id, estimated_tokens, now)
        self._set_amount(daily_entries, reservation.request_id, estimated_tokens, now)
        self.reservations[tenant.id][reservation.request_id] = (
            estimated_tokens,
            current[1],
        )
        return AdmissionReservation(reservation.request_id, estimated_tokens)

    def release(
        self,
        tenant: Tenant,
        reservation: AdmissionReservation,
        actual_tokens: int | None = None,
    ) -> bool:
        estimate = self.reservations[tenant.id].pop(reservation.request_id, None)
        if estimate is None:
            return False
        self.active[tenant.id].discard(reservation.request_id)
        if actual_tokens is not None and actual_tokens >= 0:
            self._reconcile(self.tokens[tenant.id], reservation.request_id, actual_tokens)
            self._reconcile(self.daily[tenant.id], reservation.request_id, actual_tokens)
        return True

    @staticmethod
    def _reconcile(
        entries: deque[tuple[datetime, str, int]], request_id: str, actual_tokens: int
    ) -> None:
        for index, (when, entry_id, _reserved) in enumerate(entries):
            if entry_id == request_id:
                if actual_tokens > 0:
                    entries[index] = (when, request_id, actual_tokens)
                else:
                    del entries[index]
                return

    @staticmethod
    def _amount(entries: deque[tuple[datetime, str, int]], request_id: str) -> int:
        return next((amount for _, entry_id, amount in entries if entry_id == request_id), 0)

    @staticmethod
    def _set_amount(
        entries: deque[tuple[datetime, str, int]],
        request_id: str,
        amount: int,
        now: datetime,
    ) -> None:
        for index, (when, entry_id, _old_amount) in enumerate(entries):
            if entry_id == request_id:
                entries[index] = (when, request_id, amount)
                return
        entries.append((now, request_id, amount))
