import asyncio

from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.models import ChatCompletionRequest, ChatMessage


def test_cpu_onnx_runtime_executes_real_model():
    backend = OnnxRuntimeBackend()
    result, usage, latency_ms = asyncio.run(
        backend.complete(
            ChatCompletionRequest(
                model="chat-default",
                messages=[ChatMessage(role="user", content="this is good and safe")],
            )
        )
    )
    assert "classification=positive" in result
    assert usage.total_tokens > 0
    assert latency_ms >= 0
    assert asyncio.run(backend.health())
