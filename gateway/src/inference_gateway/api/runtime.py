"""Internal CPU inference runtime used by the two local routing targets."""

from fastapi import FastAPI
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.models import ChatCompletionRequest

app = FastAPI(title="CPU ONNX Runtime Fixture", version="0.1.0")
backend = OnnxRuntimeBackend()


@app.get("/health")
async def health():
    return {"status": "ok" if await backend.health() else "failed", "provider": "CPUExecutionProvider"}


@app.post("/v1/chat/completions")
async def chat(request: ChatCompletionRequest):
    text, usage, _ = await backend.complete(request)
    return {
        "id": "local-onnx-runtime",
        "object": "chat.completion",
        "model": request.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": usage.model_dump(),
    }
