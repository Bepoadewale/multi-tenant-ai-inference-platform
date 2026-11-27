import asyncio
import os
from uuid import uuid4

import pytest
from fastapi import HTTPException
from inference_gateway.limiting.redis_service import RedisTenantLimiter
from inference_gateway.limiting.service import AdmissionReservation
from inference_gateway.models import Tenant, TenantQuota

REDIS_URL = os.getenv("REDIS_TEST_URL")


def tenant_with_limits(**updates) -> Tenant:
    limits = {
        "requests_per_minute": 20,
        "tokens_per_minute": 100,
        "concurrent_requests": 1,
        "daily_token_quota": 500,
    }
    limits.update(updates)
    return Tenant(
        id=f"redis-test-{uuid4()}",
        allowed_models={"test-model"},
        quotas=TenantQuota(**limits),
        cost_center="tests",
    )


@pytest.mark.skipif(not REDIS_URL, reason="set REDIS_TEST_URL for real Redis Lua integration")
def test_replicas_share_reservations_and_reconcile_backend_usage(monkeypatch):
    monkeypatch.setenv("INFERENCE_QUEUE_WAIT_SECONDS", "0.01")
    monkeypatch.setenv("INFERENCE_RESERVATION_LEASE_SECONDS", "2")
    tenant = tenant_with_limits(tokens_per_minute=100, daily_token_quota=100)
    first, second = RedisTenantLimiter(REDIS_URL), RedisTenantLimiter(REDIS_URL)

    async def exercise():
        reservation = await first.admit(tenant, estimated_tokens=90, request_id="first")
        with pytest.raises(HTTPException) as rejected:
            await second.admit(tenant, estimated_tokens=20, request_id="blocked")
        assert rejected.value.status_code == 429
        assert await first.release(tenant, reservation, actual_tokens=5) is True
        assert await first.release(tenant, reservation, actual_tokens=5) is False
        replacement = await second.admit(tenant, estimated_tokens=20, request_id="second")
        assert replacement.request_id == "second"
        await second.release(tenant, replacement, actual_tokens=None)

    async def run():
        try:
            await exercise()
        finally:
            await first.close()
            await second.close()

    asyncio.run(run())


@pytest.mark.skipif(not REDIS_URL, reason="set REDIS_TEST_URL for real Redis Lua integration")
def test_active_lease_renewal_and_expiry_recover_crashed_requests(monkeypatch):
    monkeypatch.setenv("INFERENCE_QUEUE_WAIT_SECONDS", "0.01")
    monkeypatch.setenv("INFERENCE_RESERVATION_LEASE_SECONDS", "0.08")
    tenant = tenant_with_limits()
    first, second = RedisTenantLimiter(REDIS_URL), RedisTenantLimiter(REDIS_URL)

    async def exercise():
        active = await first.admit(tenant, estimated_tokens=3, request_id="leased")
        await asyncio.sleep(0.04)
        assert await first.renew(tenant, active) is True
        await asyncio.sleep(0.05)
        with pytest.raises(HTTPException) as rejected:
            await second.admit(tenant, estimated_tokens=1, request_id="still-blocked")
        assert rejected.value.status_code == 429
        assert await first.release(tenant, active, actual_tokens=3) is True
        accepted = await second.admit(tenant, estimated_tokens=1, request_id="after-release")
        await second.release(tenant, accepted, actual_tokens=None)

        crashed = await first.admit(tenant, estimated_tokens=2, request_id="crashed")
        assert isinstance(crashed, AdmissionReservation)
        await asyncio.sleep(0.1)
        recovered = await second.admit(tenant, estimated_tokens=1, request_id="recovered")
        assert recovered.request_id == "recovered"
        await first.release(tenant, crashed, actual_tokens=None)
        await second.release(tenant, recovered, actual_tokens=None)

    async def run():
        try:
            await exercise()
        finally:
            await first.close()
            await second.close()

    asyncio.run(run())
