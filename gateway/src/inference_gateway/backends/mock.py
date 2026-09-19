import asyncio
from collections.abc import AsyncIterator

from inference_gateway.models import ChatCompletionRequest, Usage


class MockInferenceBackend:
    """Deterministic local backend: platform behavior only, never GPU-performance evidence."""

    async def complete(self, request: ChatCompletionRequest) -> tuple[str, Usage, float]:
        await asyncio.sleep(0.005)
        prompt_tokens = sum(len(message.content.split()) for message in request.messages)
        text = "local inference response"
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=len(text.split()),
            total_tokens=prompt_tokens + len(text.split()),
        )
        return text, usage, 5.0

    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[str]:
        for token in ["local", " inference", " response"]:
            await asyncio.sleep(0.002)
            yield token

    async def health(self) -> bool:
        return True
