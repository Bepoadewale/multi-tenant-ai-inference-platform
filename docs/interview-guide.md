# Interview guide

This platform treats inference as a latency-sensitive, shared accelerator service. Discuss why vLLM supplies efficient continuous batching/OpenAI compatibility while the gateway owns identity/fairness/metering. Explain TTFT (prefill/user wait), TPOT (decode cadence), KV cache pressure, throughput-versus-tail-latency, and why CPU autoscaling is insufficient.

Discuss integer GPU scheduling, tensor parallelism for models that do not fit one GPU, GPU cold starts/model distribution, DCGM telemetry, KEDA pod demand versus Karpenter node capacity, and shared versus dedicated pools. Explain quotas as tenant-scoped request/token/concurrency protection, aliases as safe rollout indirection, and metadata-only telemetry for prompt privacy.

At hundreds of GPUs add durable control-plane state, fleet capacity forecasting, placement/topology-aware scheduling, and regional routing. At thousands add cell-based fleet isolation, multi-region control planes, global quota policy, capacity reservations, and model artifact distribution. Training infrastructure optimizes data/checkpoints/jobs; inference optimizes serving latency, batching, cache, and availability.
