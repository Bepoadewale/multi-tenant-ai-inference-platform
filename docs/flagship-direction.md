# Flagship direction

`multi-tenant-ai-inference-platform` is the public flagship for this AI
Infrastructure / Platform Engineering portfolio. It preserves its executed core as a
governed multi-tenant inference platform, then grows through independently validated
vertical slices.

## Preserved core

The existing local proof remains non-negotiable:

```text
signed tenant identity -> Redis admission -> bounded queue -> weighted route
-> real CPU ONNX inference -> metadata-only metering -> metrics and traces
```

Every flagship integration must keep this path working and must not weaken tenant
isolation, privacy boundaries, clean-room reproducibility or the evidence labels for
GPU/cloud behavior.

## Integration model

The flagship consumes proven concepts through narrow contracts; it does not merge ten
repositories into one monolith.

| Reference project | Flagship vertical slice | Contract boundary |
| --- | --- | --- |
| Model Deployment Control Plane | registry, evaluation, canary, approval, promotion/rollback | verified release plan and traffic intent |
| GPU Scheduler Lab | simulated-GPU capacity/admission policy | Redis-shared simulated capacity decision; physical placement stays in the lab/production adapter |
| AI Observability + FinOps | traces, SLO evidence, cost attribution | telemetry and usage events |
| AI SRE Auto-Remediation | governed incident/remediation | evidence, plan, approval, bounded action |
| Secure MCP Gateway | secure agent platform-tool access | delegated tool invocation |
| Hybrid AI Edge Platform | narrow local-cloud routing adapter | signed device registration, metadata-only inventory, local-ONNX-or-policy-fallback contract; OTA/fleet rollout stays in the reference project |
| AI Developer Platform | self-service/golden paths | durable tenant/model-bound integration profile and token-free starter contract |
| Secure Agent Runtime | bounded agent execution | capability-scoped task contract |

## First integrated demonstration

```text
tenant request -> signed identity/quota -> simulated-capacity admission
-> verified candidate release -> local serving canary -> trace/SLO/cost evidence -> independent approval
-> champion promotion OR automatic rollback to the previous champion
```

The failure path is first-class: a candidate that is service-healthy but violates a
quality, artifact-integrity or latency gate must not become champion.

## Local-first boundary

The flagship runs locally with Docker, Redis, MLflow, ONNX CPU fixtures,
OpenTelemetry, Prometheus and Grafana. The current capacity slice uses `simulated-l40s`
as Redis quota accounting only; it never claims GPU placement or performance. kind,
real GPUs, paid clouds and external model APIs remain optional adapters, not
requirements for the core proof.

Commercial positioning, buyer strategy, pricing and hosted-product decisions are
deliberately absent from this public repository and retained in a private strategy
repository.

## Edge-adapter boundary

The executed flagship edge slice proves only the integration seam:

```text
signed device registration -> durable capability inventory
-> compatible device local ONNX OR constrained-device public fallback
-> restricted / LOCAL_ONLY denial -> restart recovery
```

It runs two independent device-agent containers. Their `laptop-high` and
`embedded-constrained` labels are **simulated profiles**, not device or benchmark
evidence. HTTP registration, SQLite persistence, signed device identities, local ONNX
execution, gateway fallback, policy denial, and control restart recovery are real.
Signed packages, desired-state reconciliation, staged fleet rollout/rollback, offline
telemetry buffering, and physical hardware remain in the standalone edge project or
future adapters.
