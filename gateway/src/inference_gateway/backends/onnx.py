"""A real, lightweight ONNX Runtime backend for the local-first platform path."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
from time import perf_counter

import numpy as np
import onnxruntime as ort
from inference_gateway.models import ChatCompletionRequest, Usage


class OnnxRuntimeBackend:
    def __init__(self, model_path: str | Path | None = None) -> None:
        configured = model_path or os.getenv("ONNX_MODEL_PATH", "models/tiny-intent-classifier.onnx")
        self.model_path = Path(configured)
        self.session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])

    @staticmethod
    def _features(request: ChatCompletionRequest) -> np.ndarray:
        text = " ".join(message.content.lower() for message in request.messages)
        words = text.split()
        positive = sum(word.strip(".,!?") in {"good", "great", "safe", "yes", "allow"} for word in words)
        negative = sum(word.strip(".,!?") in {"bad", "fail", "unsafe", "no", "deny"} for word in words)
        return np.array([[positive, negative, len(words), text.count("?")]], dtype=np.float32)

    async def complete(self, request: ChatCompletionRequest) -> tuple[str, Usage, float]:
        started = perf_counter()
        scores, labels = await asyncio.to_thread(
            self.session.run, ["scores", "label"], {"features": self._features(request)}
        )
        label = "positive" if int(labels[0]) == 0 else "negative"
        confidence = float(np.exp(scores[0]).max() / np.exp(scores[0]).sum())
        text = f"classification={label}; confidence={confidence:.3f}"
        prompt_tokens = sum(len(message.content.split()) for message in request.messages)
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=len(text.split()),
            total_tokens=prompt_tokens + len(text.split()),
        )
        return text, usage, (perf_counter() - started) * 1000

    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[str]:
        text, _, _ = await self.complete(request)
        for token in text.split(" "):
            yield f"{token} "

    async def health(self) -> bool:
        return self.model_path.exists() and "CPUExecutionProvider" in self.session.get_providers()
