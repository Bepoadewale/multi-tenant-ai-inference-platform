import asyncio
from inference_gateway.catalog.store import Catalog
from inference_gateway.models import ChatCompletionRequest, ChatMessage
from inference_gateway.services.gateway import GatewayService


async def main():
    service, catalog = GatewayService(), Catalog()
    normal = await service.chat(
        catalog.tenant("team-search"),
        ChatCompletionRequest(
            model="chat-default", messages=[ChatMessage(role="user", content="hello")], max_tokens=8
        ),
    )
    print("A normal inference:", normal["usage"])
    try:
        await service.chat(
            catalog.tenant("team-payments"),
            ChatCompletionRequest(
                model="embeddings", messages=[ChatMessage(role="user", content="denied")]
            ),
        )
    except Exception as error:
        print("B authorization denied:", error)
    payments = catalog.tenant("team-payments")
    for _ in range(5):
        await service.chat(
            payments,
            ChatCompletionRequest(
                model="chat-default",
                messages=[ChatMessage(role="user", content="load")],
                max_tokens=1,
            ),
        )
    try:
        await service.chat(
            payments,
            ChatCompletionRequest(
                model="chat-default",
                messages=[ChatMessage(role="user", content="throttle")],
                max_tokens=1,
            ),
        )
    except Exception as error:
        print("C tenant throttled:", error)
    print("G cost/usage:", service.meter.tenant_summary("team-payments"))


asyncio.run(main())
