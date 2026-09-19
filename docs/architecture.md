# Architecture

The gateway is the tenant boundary; vLLM is a model runtime, not an authorization system. It resolves an authenticated credential to a tenant, checks model permission and atomic quota admission, chooses a healthy weighted deployment target, proxies compatible requests, and writes metadata-only usage records. Shared pools maximize batching/utilization; a dedicated pool contract exists for predictable isolation at higher cost.

Administrative API paths (`/platform/v1`) are deliberately separate from public `/v1` inference paths and require a stronger role. The repository now includes a vLLM OpenAI-compatible adapter and a Redis Lua admission contract; production still needs OIDC/JWKS validation, Redis wiring, durable PostgreSQL metering/outbox, and a model deployment controller.
