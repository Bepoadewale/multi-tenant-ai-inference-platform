import asyncio

import pytest
from fastapi import HTTPException
from inference_gateway.catalog.store import Catalog
from inference_gateway.models import ChatCompletionRequest, ChatMessage
from inference_gateway.services.gateway import GatewayService


def request(model="chat-default", max_tokens=5):
    return ChatCompletionRequest(
        model=model,
        messages=[ChatMessage(role="user", content="hello platform")],
        max_tokens=max_tokens,
    )


def test_authorized_completion_is_metered():
    service = GatewayService()
    result = asyncio.run(service.chat(Catalog().tenant("team-search"), request()))
    assert result["usage"]["total_tokens"] > 0
    assert service.meter.tenant_summary("team-search")["requests"] == 1


def test_model_authorization_is_tenant_scoped():
    with pytest.raises(HTTPException, match="not authorized"):
        asyncio.run(GatewayService().chat(Catalog().tenant("team-payments"), request("embeddings")))


def test_one_tenant_limit_does_not_affect_another():
    service, catalog = GatewayService(), Catalog()
    payments = catalog.tenant("team-payments")
    for _ in range(payments.quotas.requests_per_minute):
        asyncio.run(service.chat(payments, request()))
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.chat(payments, request()))
    assert error.value.status_code == 429
    assert (
        asyncio.run(service.chat(catalog.tenant("team-search"), request()))["object"]
        == "chat.completion"
    )


def test_unhealthy_backends_fail_closed():
    service = GatewayService()
    service.catalog.models["chat-default"].targets[0].healthy = False
    service.catalog.models["chat-default"].targets[1].healthy = False
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.chat(Catalog().tenant("team-search"), request()))
    assert error.value.status_code == 503
