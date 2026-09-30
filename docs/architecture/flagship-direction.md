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

Future cloud infrastructure is a separate, Terraform-managed delivery path: Terraform
must provision and tear down pilot resources with reviewed plans, protected state, and
post-destroy verification. It is not part of the executed local proof.

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
| Flagship operator console | unified browser operations | local backend-for-frontend over existing scoped APIs |

## First integrated demonstration

```text
tenant request -> signed identity/quota -> simulated-capacity admission
-> verified candidate release -> local serving canary -> trace/SLO/cost evidence -> independent approval
-> champion promotion OR automatic rollback to the previous champion
```

The failure path is first-class: a candidate that is service-healthy but violates a
quality, artifact-integrity or latency gate must not become champion.

## Executed cumulative proof

The project-level `make demo-flagship` command runs the preserved tenant-inference
story plus every currently scoped vertical slice against one Compose stack: admission
and overload, routing and metering, observability, backend failure/timeout and restart
recovery, MLflow release control, simulated-capacity policy, evidence/remediation,
developer self-service, delegated tools, edge policy, and bounded sandbox execution.
Two clean-room cycles executed `make install`, `make bootstrap-local`, `make smoke`,
`make demo-flagship`, `make verify`, and project-scoped `make clean-local` on
2026-09-29. See [validation evidence](../governance/VALIDATION.md); this proof does not change the
production/hardware boundaries below.

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

## Sandboxed-agent boundary

The sandbox slice is intentionally narrow. A short-lived signed delegated agent can
request only one of two named fixture tasks: make a bounded patch to an immutable
fixture repository, or perform a controlled outbound-network probe. It cannot submit
an arbitrary shell command, choose an image, mount a host path, select a Docker
network, access platform credentials, approve a release, or call the remediation
executor.

```text
signed delegated agent -> fixed task kind -> trusted sandbox controller
-> disposable non-root child container -> patch/containment evidence -> destroy
```

The trusted controller has Docker API access solely to create labelled child
containers. The untrusted child is run with a read-only root filesystem, dropped
capabilities, no-new-privileges, CPU/memory/PID bounds, no Docker socket, no host bind
mount, and `network=none`. It is not a claim of gVisor, Firecracker, Kubernetes pod
sandboxing, or general arbitrary-agent-code execution; those remain separate
production/standalone-runtime concerns.

## Operator-console boundary

The local operator console is the unified entry point for the executed flagship demo:

```text
browser -> operator-console backend -> fixed service API calls -> existing policy,
approval, audit, release, and sandbox controls
```

It aggregates live evidence from the gateway, Redis-backed capacity, MLflow, release
control, remediation, delegated-agent audit, sandbox control, developer self-service,
edge inventory, and Prometheus. Its only mutation routes are fixed release transitions
and the two already-allowlisted sandbox fixture tasks; it cannot submit arbitrary
commands, alter tenant identity, access Redis/Docker credentials, or bypass the
underlying release approval checks. Browser clients never receive the synthetic local
tokens. The server-side token bundle is a **local demo convenience**, not production
authentication. A production console requires enterprise SSO, per-user authorization,
CSRF/session protections, and a scoped backend-for-frontend credential exchange.
