import asyncio

from inference_gateway.catalog.store import Catalog
from inference_gateway.models import ChatCompletionRequest, ChatMessage
from inference_gateway.services.gateway import GatewayService


def test_usage_summary_does_not_store_prompt_content():
    service = GatewayService()
    asyncio.run(
        service.chat(
            Catalog().tenant("team-search"),
            ChatCompletionRequest(
                model="chat-default",
                messages=[ChatMessage(role="user", content="private prompt must not be metered raw")],
            ),
        )
    )
    summary = asyncio.run(service.tenant_usage("team-search"))
    assert summary["requests"] == 1
    assert "prompt" not in str(summary).lower()
