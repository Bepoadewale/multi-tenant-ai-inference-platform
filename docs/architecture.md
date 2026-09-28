# Architecture

This is the executed foundation of the public flagship. Future release, capacity,
FinOps/SLO, remediation, secure-agent, edge and developer-platform capabilities attach
through narrow contracts described in [flagship direction](flagship-direction.md); they
do not replace the gateway or merge other repositories wholesale.

The gateway is the tenant boundary; a model runtime is not an authorization system. It resolves an authenticated credential to a tenant, checks model permission and atomic quota admission, chooses a healthy weighted deployment target, proxies compatible requests, and writes metadata-only usage records. The local stack executes this design through two CPU ONNX Runtime targets; shared pools maximize batching/utilization, while a dedicated pool contract exists for predictable isolation at higher cost.

Administrative API paths (`/platform/v1`) are deliberately separate from public `/v1` inference paths and require a stronger role. The local stack executes Ed25519 JWT verification, Redis Lua admission, and Redis metadata metering. vLLM, enterprise OIDC, durable PostgreSQL/outbox metering, and a model deployment controller remain production adapters or roadmap work.
