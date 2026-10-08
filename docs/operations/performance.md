# Performance and benchmarking

## In simple terms

This project proves that the gateway can control who uses a model and how requests are
handled. It does **not** prove laptop or CPU-fixture performance represents a real GPU
service. Treat the local load tool as a repeatable regression check, not a production
benchmark.

Flagship context: benchmark evidence must remain tied to the exact local runtime;
planned registry, capacity and FinOps slices do not turn CPU fixture results into GPU claims.

`make load-test` is a deterministic **mock-backend** benchmark client. It writes JSON, CSV, and
Markdown metadata/results and explicitly labels its output `local-mock`; its figures are useful for
gateway smoke/regression work only. They are not measurements of the Dockerized ONNX Runtime path,
model quality, GPU execution, TTFT, TPOT, or production throughput.

The primary local platform demo is different: `make bootstrap-local` and `make demo-local` execute
two CPU ONNX Runtime targets through two gateways and Redis-backed admission. GPU reports must
record model/revision, vLLM settings, hardware/SKU, GPU count, driver/runtime, date,
prompt/output distributions, concurrency, and cold/warm state.

Demo: A normal `team-search` request succeeds and meters usage. B `team-payments` requesting embeddings gets 403. C repeated payments traffic gets 429 while search remains healthy. D setting all targets unhealthy returns 503. E catalog weights demonstrate canary routing. F KEDA manifest shows demand scaling. G usage endpoint reports per-tenant tokens and estimated cost.

## Inference performance concepts

Prefill processes the prompt and dominates **TTFT** (time to first token); decode
produces each output token and determines **TPOT** (time per output token). Continuous
batching can improve aggregate tokens/sec while increasing queueing/TTFT. KV cache
stores attention state: its memory pressure, context length, concurrency, and GPU
memory allocation directly affect admission and OOM risk. Prefix caching can reduce
repeated-prefill work.

Quantization reduces memory and can improve fit/throughput but changes
quality/performance trade-offs. Tensor parallelism splits a model across GPUs; data
parallelism adds replicas. High GPU utilization is not automatically good user
latency—queueing and tail TTFT matter. The executed CPU ONNX fixture validates routing
and admission behavior, not production model performance; the separate mock benchmark
must never be compared to GPU vLLM results.

## Runtime support matrix

| Runtime / capability | Status | What the repository actually proves |
| --- | --- | --- |
| ONNX Runtime `CPUExecutionProvider` | ✅ EXECUTED LOCALLY | Two Dockerized runtime targets load the generated ONNX fixture and serve real gateway traffic. |
| OpenAI-compatible chat and SSE | ✅ EXECUTED LOCALLY | Gateway returns non-streaming and streaming fixture responses. |
| weighted gateway routing | ✅ EXECUTED LOCALLY | Shared Redis weights direct live requests to stable/candidate CPU targets. |
| vLLM | 📐 ARCHITECTURE / CONTRACT ONLY | Adapter/configuration exists; no vLLM process, GPU, or benchmark ran. |
| Triton Inference Server | 📋 ROADMAP | Candidate for a future real-runtime pilot; not installed or validated here. |
| SGLang | 📋 ROADMAP | Candidate for a future real-runtime pilot; not installed or validated here. |
| GPU/DCGM/KV-cache telemetry | 🔵 SIMULATED / UNEXECUTED | Redis capacity accounting is explicitly not physical hardware telemetry. |

Supported version statements are limited to the versions constrained in
`pyproject.toml`, `docker-compose.yml`, and the current lock/image references. A
runtime becomes “supported” only after a reproducible local or pilot validation record
names the environment, command, model, result, and failure boundary.
