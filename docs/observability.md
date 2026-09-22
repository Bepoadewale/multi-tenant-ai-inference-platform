# Observability and SLOs

Gateway metrics cover requests/outcomes, prompt/completion tokens, throttles, active requests, queue wait, end-to-end latency, and TTFT. Local Compose exports OTLP through the Collector to Tempo and exposes Prometheus metrics; generated demo traffic is queryable in both systems. vLLM `/metrics` and DCGM Exporter would supply serving/GPU telemetry in GPU mode, which is not executed here. Gateway traces cover admission, routing, backend call, and metering with request IDs.

Example workload SLOs—not universal numbers: 99.9% successful requests, an agreed model-specific p95 TTFT objective, and low infrastructure-generated 5xx rate. Dashboard views should answer: who is throttled, where tail latency originates, which model is saturated, and what GPU memory/utilization says about capacity.
