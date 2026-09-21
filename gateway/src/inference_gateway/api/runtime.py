"""Internal CPU inference runtime used by the two local routing targets."""

import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.models import ChatCompletionRequest

app = FastAPI(title="CPU ONNX Runtime Fixture", version="0.1.0")
backend = OnnxRuntimeBackend()


@app.get("/health")
async def health():
    return {"status": "ok" if await backend.health() else "failed", "provider": "CPUExecutionProvider"}


@app.post("/v1/chat/completions")
async def chat(request: ChatCompletionRequest):
    if request.stream:
        async def events():
            async for token in backend.stream(request):
                payload = {
                    "id": "local-onnx-runtime",
                    "object": "chat.completion.chunk",
                    "choices": [
                        {"index": 0, "delta": {"content": token}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(payload)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    text, usage, _ = await backend.complete(request)
    return {
        "id": "local-onnx-runtime",
        "object": "chat.completion",
        "model": request.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": usage.model_dump(),
    }
