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
| GPU Scheduler Lab | simulated-GPU capacity/admission policy | capacity and placement decision |
| AI Observability + FinOps | traces, SLO evidence, cost attribution | telemetry and usage events |
| AI SRE Auto-Remediation | governed incident/remediation | evidence, plan, approval, bounded action |
| Secure MCP Gateway | secure agent platform-tool access | delegated tool invocation |
| Hybrid AI Edge Platform | optional edge artifact/routing extension | fleet/artifact and local-cloud routing contract |
| AI Developer Platform | self-service/golden paths | service/request contract |
| Secure Agent Runtime | bounded agent execution | capability-scoped task contract |

## First integrated demonstration

```text
tenant request -> signed identity/quota/policy -> verified candidate release
-> local serving canary -> trace/SLO/cost evidence -> independent approval
-> champion promotion OR automatic rollback to the previous champion
```

The failure path is first-class: a candidate that is service-healthy but violates a
quality, artifact-integrity or latency gate must not become champion.

## Local-first boundary

The flagship must run with Docker/kind, Redis/Postgres where needed, MLflow, ONNX CPU
fixtures, OpenTelemetry, Prometheus and Grafana. Real GPUs, paid clouds and external
model APIs are optional adapters, not requirements for the core proof.

Commercial positioning, buyer strategy, pricing and hosted-product decisions are
deliberately absent from this public repository and retained in a private strategy
repository.
