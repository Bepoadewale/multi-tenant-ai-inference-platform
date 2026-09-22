# Inference performance

Prefill processes the prompt and dominates **TTFT** (time to first token); decode produces each output token and determines **TPOT** (time per output token). Continuous batching can improve aggregate tokens/sec while increasing queueing/TTFT. KV cache stores attention state: its memory pressure, context length, concurrency, and GPU memory allocation directly affect admission and OOM risk. Prefix caching can reduce repeated-prefill work.

Quantization reduces memory and can improve fit/throughput but changes quality/performance trade-offs. Tensor parallelism splits a model across GPUs; data parallelism adds replicas. High GPU utilization is not automatically good user latency—queueing and tail TTFT matter. The executed CPU ONNX fixture validates routing and admission behavior, not production model performance; the separate mock benchmark must never be compared to GPU vLLM results.
