from collections.abc import AsyncIterator
from typing import Protocol

from inference_gateway.models import ChatCompletionRequest, Usage


class InferenceBackend(Protocol):
    async def complete(self, request: ChatCompletionRequest) -> tuple[str, Usage, float]: ...
    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[str]: ...
    async def health(self) -> bool: ...
