# Architecture

This is the executed foundation of the public flagship. Release, simulated capacity,
request-level FinOps/SLO evidence, and governed canary remediation attach through
narrow contracts described in [flagship direction](flagship-direction.md). Secure-agent,
edge and developer-platform capabilities remain future slices; none replace the gateway
or merge other repositories wholesale.

The gateway is the tenant boundary; a model runtime is not an authorization system. It resolves an authenticated credential to a tenant, checks model permission and atomic quota admission, chooses a healthy weighted deployment target, proxies compatible requests, and writes metadata-only usage records. The local stack executes this design through two CPU ONNX Runtime targets; shared pools maximize batching/utilization, while a dedicated pool contract exists for predictable isolation at higher cost.

Administrative API paths (`/platform/v1`) are deliberately separate from public `/v1`
inference paths and require a stronger role. The local stack executes Ed25519 JWT
verification, Redis Lua admission, metadata metering, and request analysis that
correlates Tempo trace ID, release context, local SLO result and a versioned fixture
token-cost estimate. vLLM, enterprise OIDC, durable PostgreSQL/outbox metering, and a
model deployment controller remain production adapters or roadmap work.

## Governed canary remediation

`remediation-control` is a separate FastAPI process with its own SQLite incident,
plan, guard, and timeline store. It reads only the gateway's existing metadata-only
Redis usage record. An incident is eligible only when it records a failed
`chat-default` request in an active `CANARY` release context. The controller produces
an immutable plan for one allowlisted action: `ROLLBACK_CANARY_TO_STABLE`.

The requester cannot approve that plan. Before execution, the controller rechecks the
release-plan ID, `CANARY` phase, exact Redis weights, and SQLite release state. It then
uses a per-model cooldown/action budget, changes only the shared rollout weights to
stable=100/candidate=0, transitions the release state, and verifies the result. It has
no generic shell, Docker, Kubernetes, cloud, model-registry, or tenant-request
capability. Prometheus scrapes its incident, plan, action, and verification metrics;
its audit timeline survives a controller restart.
