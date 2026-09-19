# Observability and SLOs

Gateway metrics cover requests/outcomes, prompt/completion tokens, throttles, active requests, end-to-end latency, and TTFT. vLLM `/metrics` and DCGM Exporter supply serving/GPU telemetry in GPU mode. Trace gateway admission, routing, backend call, and metering with request IDs using OpenTelemetry in deployment.

Example workload SLOs—not universal numbers: 99.9% successful requests, an agreed model-specific p95 TTFT objective, and low infrastructure-generated 5xx rate. Dashboard views should answer: who is throttled, where tail latency originates, which model is saturated, and what GPU memory/utilization says about capacity.
