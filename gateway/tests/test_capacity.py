import asyncio

import pytest
from fastapi import HTTPException
from inference_gateway.capacity.service import CapacityService
from inference_gateway.catalog.store import Catalog
from inference_gateway.models import CapacityDecision, ChatCompletionRequest, ChatMessage
from inference_gateway.services.gateway import GatewayService


def test_simulated_capacity_is_tenant_isolated_and_can_fallback_to_cpu():
    catalog = Catalog()
    service = CapacityService(pool_slots=2)
    search = catalog.tenant("team-search")
    payments = catalog.tenant("team-payments")
    analytics = catalog.tenant("team-analytics")
    gpu_model = catalog.model("chat-default")
    fallback_model = catalog.model("chat-cpu-fallback-demo")

    search_allocation = asyncio.run(service.admit(search, gpu_model))
    payments_allocation = asyncio.run(service.admit(payments, gpu_model))
    assert search_allocation.decision == CapacityDecision.SIMULATED_GPU_ADMITTED
    assert payments_allocation.decision == CapacityDecision.SIMULATED_GPU_ADMITTED

    with pytest.raises(HTTPException, match="tenant capacity quota"):
        asyncio.run(service.admit(search, gpu_model))

    fallback = asyncio.run(service.admit(analytics, fallback_model))
    assert fallback.decision == CapacityDecision.CPU_FALLBACK
    assert fallback.simulated_hardware is True

    asyncio.run(service.release(search, search_allocation))
    asyncio.run(service.release(payments, payments_allocation))


def test_cpu_fallback_still_uses_the_real_local_onnx_path():
    service = GatewayService()
    service.capacity = CapacityService(pool_slots=0)
    request = ChatCompletionRequest(
        model="chat-cpu-fallback-demo",
        messages=[ChatMessage(role="user", content="good")],
        max_tokens=4,
    )

    result = asyncio.run(service.chat(Catalog().tenant("team-analytics"), request))
    assert result["choices"][0]["message"]["content"]
    assert result["x_capacity"]["decision"] == "CPU_FALLBACK"
