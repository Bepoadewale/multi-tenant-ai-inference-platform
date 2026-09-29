# Architecture

This is the executed foundation of the public flagship. Release, simulated capacity,
request-level FinOps/SLO evidence, and governed canary remediation attach through
narrow contracts described in [flagship direction](flagship-direction.md). Secure-agent
tools, developer self-service, edge routing, and bounded sandbox execution are narrow
services. None replaces the gateway or merges another repository wholesale.

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

## Developer self-service contract

`developer-self-service` is a separate FastAPI process with a SQLite profile store. A
signed human principal with `developer.self_service` can request one named service,
owner, environment, and model alias. The service derives the tenant from the JWT,
checks the static local catalog assignment, binds the request to a tenant-scoped
idempotency key, and emits a durable integration profile plus generated token-free
starter files. The generated client calls the public gateway API and obtains a workload
token at runtime; it has no direct dependency on Redis, MLflow, model runtimes, or
rollout controls. Profiles are tenant-isolated and survive service restart. Delegated
agent identities are intentionally denied: agent assistance belongs behind the bounded
agent-tools contract, not a self-provisioning path.

## Narrow edge-routing adapter

`edge-control` has its own SQLite device registry, while `edge-device-search` and
`edge-device-constrained` are independently running FastAPI agents. Both use signed
device-only JWTs to register their simulated profile and heartbeat metadata. A caller
still presents a normal signed tenant identity to the device agent. The capable device
loads an independent local ONNX Runtime session for `chat-default`; the constrained
device advertises no local model and forwards only public requests to the existing
gateway. Restricted, `LOCAL_ONLY`, and `PRIVACY_FIRST` requests without a local model
stop at the device. Artifact distribution and desired-state rollout remain outside the
narrow adapter.

## Bounded sandboxed-agent execution

`sandbox-control` is a separate FastAPI service with a durable SQLite task store. It
accepts only a signed, short-lived delegated agent identity and two fixed task kinds:
fixture patching and a containment probe. The trusted controller has Docker API access
only to create labelled child containers. Those children get a Docker-managed workspace
volume, clone the fixture repository from their immutable image, run as UID 65532 with
read-only root filesystem, dropped capabilities, no-new-privileges, CPU/memory/PID
bounds, no Docker socket, no host bind mounts, and no network. The controller collects
only patch hash/hardening metadata and removes every child container and workspace.
