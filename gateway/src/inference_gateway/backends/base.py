from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from inference_gateway.models import ChatCompletionRequest, Usage


@dataclass(frozen=True)
class BackendStreamChunk:
    """Internal content or final-usage event from a streaming inference backend."""

    content: str | None = None
    usage: Usage | None = None


class InferenceBackend(Protocol):
    async def complete(self, request: ChatCompletionRequest) -> tuple[str, Usage, float]: ...
    async def stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[str | BackendStreamChunk]: ...
    async def health(self) -> bool: ...
