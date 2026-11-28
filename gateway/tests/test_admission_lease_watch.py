import asyncio

import pytest
from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.service import AdmissionReservation
from inference_gateway.services.gateway import GatewayService


def test_unresponsive_lease_renewal_cancels_owner_before_lease_expiry():
    service = GatewayService()
    lease_seconds = 0.3
    renewal_cancelled = asyncio.Event()

    class UnresponsiveLimiter:
        def __init__(self):
            self.lease_seconds = lease_seconds

        async def renew(self, _tenant, _reservation):
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                renewal_cancelled.set()
                raise

    service.limiter = UnresponsiveLimiter()
    tenant = Catalog().tenant("team-search")
    reservation = AdmissionReservation("slow-renewal", estimated_tokens=1)

    async def exercise():
        async def wait_for_request_cancellation():
            await asyncio.Event().wait()

        owner_task = asyncio.create_task(wait_for_request_cancellation())
        started = asyncio.get_running_loop().time()
        lease_task = service._start_lease_watch(tenant, reservation, owner_task)

        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(owner_task, timeout=lease_seconds * 1.5)

        elapsed = asyncio.get_running_loop().time() - started
        await lease_task
        assert elapsed < lease_seconds
        assert renewal_cancelled.is_set()

    asyncio.run(exercise())
