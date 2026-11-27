"""OpenAI-compatible vLLM adapter; tenant policy remains exclusively in the gateway."""

import json
import os
from collections.abc import AsyncIterator
from time import perf_counter

import httpx
from inference_gateway.backends.base import BackendStreamChunk
from inference_gateway.models import ChatCompletionRequest, Usage


class VllmBackend:
    def __init__(self, base_url: str, model_id: str, timeout_seconds: float | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("INFERENCE_BACKEND_TIMEOUT_SECONDS", "30")
        )

    def _payload(self, request: ChatCompletionRequest, stream: bool) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [message.model_dump() for message in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": stream,
        }
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=3) as client:
                return (await client.get("/health")).is_success
        except httpx.HTTPError:
            return False

    async def complete(self, request: ChatCompletionRequest) -> tuple[str, Usage, float]:
        started = perf_counter()
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout_seconds
            ) as client:
                response = await client.post(
                    "/v1/chat/completions", json=self._payload(request, False)
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise RuntimeError("vLLM request failed") from error
        payload = response.json()
        usage = Usage(**payload["usage"])
        content = payload["choices"][0]["message"]["content"]
        # vLLM non-streaming does not expose true TTFT; record it only from streaming instrumentation.
        return content, usage, (perf_counter() - started) * 1000

    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[BackendStreamChunk]:
        # Streaming is intentionally not retried: a client can have received partial output.
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout_seconds
            ) as client:
                async with client.stream(
                    "POST", "/v1/chat/completions", json=self._payload(request, True)
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if data == "[DONE]":
                            break
                        payload = json.loads(data)
                        raw_usage = payload.get("usage")
                        usage = Usage(**raw_usage) if raw_usage is not None else None
                        if usage is not None:
                            yield BackendStreamChunk(usage=usage)
                        choices = payload.get("choices", [])
                        if choices:
                            content = choices[0].get("delta", {}).get("content")
                            if content:
                                yield BackendStreamChunk(content=content)
        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ) as error:
            raise RuntimeError("vLLM stream failed") from error
