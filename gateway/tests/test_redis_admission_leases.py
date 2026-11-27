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
    tenant = tenant_with_limits(
        tokens_per_minute=100, daily_token_quota=100, concurrent_requests=2
    )
    first, second = RedisTenantLimiter(REDIS_URL), RedisTenantLimiter(REDIS_URL)

    async def exercise():
        reservation = await first.admit(tenant, estimated_tokens=0, request_id="first")
        second_reservation = await second.admit(
            tenant, estimated_tokens=0, request_id="second"
        )
        reservation = await first.reserve_usage(tenant, reservation, estimated_tokens=90)
        with pytest.raises(HTTPException) as rejected:
            await second.reserve_usage(tenant, second_reservation, estimated_tokens=20)
        assert rejected.value.status_code == 429
        assert await first.release(tenant, reservation, actual_tokens=5) is True
        assert await first.release(tenant, reservation, actual_tokens=5) is False
        second_reservation = await second.reserve_usage(
            tenant, second_reservation, estimated_tokens=20
        )
        assert second_reservation.request_id == "second"
        await second.release(tenant, second_reservation, actual_tokens=None)

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

        keys = first._keys(tenant.id)
        crashed = await first.admit(tenant, estimated_tokens=2, request_id="crashed-renew")
        assert isinstance(crashed, AdmissionReservation)
        await asyncio.sleep(0.1)
        assert await first.renew(tenant, crashed) is False
        assert await first.client.hget(keys[5], "crashed-renew") is None
        recovered = await second.admit(tenant, estimated_tokens=1, request_id="recovered")
        assert recovered.request_id == "recovered"
        assert await first.release(tenant, crashed, actual_tokens=None) is False
        await second.release(tenant, recovered, actual_tokens=None)

        for index in range(3):
            request_id = f"orphan-{index}"
            crashed = await first.admit(tenant, estimated_tokens=2, request_id=request_id)
            await asyncio.sleep(0.1)
            recovered = await second.admit(
                tenant, estimated_tokens=1, request_id=f"recovered-{index}"
            )
            assert await second.client.hget(keys[5], request_id) is None
            assert await first.release(tenant, crashed, actual_tokens=None) is False
            await second.release(tenant, recovered, actual_tokens=None)
        assert await first.client.hlen(keys[5]) == 0

    async def run():
        try:
            await exercise()
        finally:
            await first.close()
            await second.close()

    asyncio.run(run())
