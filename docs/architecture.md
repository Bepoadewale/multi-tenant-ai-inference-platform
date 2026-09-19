# Architecture

The gateway is the tenant boundary; vLLM is a model runtime, not an authorization system. It resolves an authenticated credential to a tenant, checks model permission and atomic quota admission, chooses a healthy weighted deployment target, proxies compatible requests, and writes metadata-only usage records. Shared pools maximize batching/utilization; a dedicated pool contract exists for predictable isolation at higher cost.

Administrative API paths (`/platform/v1`) are deliberately separate from public `/v1` inference paths. Production adds OIDC, Redis Lua admission, durable metering/outbox, and a model deployment controller.
