# Flagship Cloud-Pilot Program

## Purpose

The flagship has a completed local proof: signed tenants share real CPU ONNX inference
through Redis admission, model-release controls, telemetry, remediation, delegated
tools, developer self-service, edge routing, sandbox tasks, and a scoped Operator
Console.

This program prepares a **separate AWS pilot**. It does not change local proof into an
AWS runtime claim. An authenticated no-apply Terraform plan has been reviewed, but no
AWS resource has been created.

In plain English, the future pilot will check that the same rules still hold when the
platform runs on cloud infrastructure: one tenant cannot consume another tenant's
limits, a release cannot bypass review, agents cannot acquire operator power, and the
platform can be observed and removed safely.

## Current baseline

| Area | Current fact | Cloud-pilot gap |
| --- | --- | --- |
| Inference | Two gateway containers call real CPU ONNX runtimes. | EKS workload, real runtime compatibility, optional GPU hardware. |
| Admission | Redis Lua limits are shared by two gateways. | Durable production stores, Kubernetes-aware scaling and capacity evidence. |
| Release control | Local MLflow, SQLite plans, canary, approval, promotion and rollback run. | Cloud MLflow/artifact store, protected delivery and real workload metrics. |
| Observability | OTel, Tempo, Prometheus and Grafana receive local traffic. | Cloud runtime telemetry, retention, alerts, cost evidence and a bounded cloud drill. |
| Operator Console | Local BFF has synthetic server-side fixture identities. | Trusted browser identity, exact cloud origin and server-side credential exchange. |
| Capacity | Redis tracks a clearly simulated accelerator pool. | Optional, separately budgeted GPU node/runtime validation. |

## Design principles inherited from Project 1

- Terraform alone creates and destroys AWS foundation resources.
- State is encrypted, versioned, locked, project-scoped, and separate from every
  other portfolio repository.
- No long-lived cloud credential belongs in GitHub. Future automation uses GitHub OIDC
  and a least-privilege role.
- Private services remain private. If a browser entry point is required, an ALB routes
  only the Console, API, and identity paths.
- Every cloud claim needs exact plan, apply, smoke, failure, observability, cost, and
  destroy evidence. Early Cost Explorer values are estimates, not settled billing.
- Hardware and performance remain unclaimed until measured on the named environment.

## Delivery sequence

### CP0 — Baseline inventory

Record the current local proof and identify the cloud gaps. This documentation-only
slice is complete when its links and evidence labels are reviewed; it is not a
cloud-execution milestone.

### CP1 — Cloud story and topology

Add the concise cloud README section, icon-based AWS topology, trust-boundary diagram,
cloud operations guide, security model, and production-evolution page. The diagram
must show the actual intended gateway, runtime, stores, delivery, identity, and
observability paths for this repository.

**Status: complete as documentation/static validation only.** See the
[cloud architecture](../cloud-architecture.md), [cloud operations contract](../cloud-operations.md),
and [production evolution boundary](../production-evolution.md). No AWS resources
were created for CP1.

### CP2 — Terraform foundation

Define a separate bootstrap root for a dedicated encrypted/versioned S3 state bucket,
DynamoDB locking, required tags, and a cost-budget alarm. Define a pilot root for a
private VPC, EKS, ECR, IAM/IRSA, and only the shared AWS services required below.
Validate with `terraform init -backend=false`, formatting, validation, and reviewed
non-applying plan output.

**Status: implemented, statically validated, and read-only planned.** The separate
[`bootstrap/`](../../infrastructure/terraform/bootstrap/README.md) root contains the
state/lock/tag/budget contract. An authenticated plan proposed seven resources. No
bucket, lock table, budget, or other resource has been created from this repository.

### CP3 — State and security boundaries

Add Terraform modules and cloud contracts for the services the platform actually uses:
RDS PostgreSQL for durable control state, ElastiCache Redis for admission, S3 for MLflow
artifacts, ECR image delivery, Secrets Manager/External Secrets, and least-privilege
IRSA. Define tenant-safe NetworkPolicies, probes, PDBs, non-root execution, and
resource limits. Optional GPU infrastructure is isolated and disabled by default.

**Status: implemented, statically validated, and read-only planned.** The pilot root now contracts
private VPC/EKS, immutable ECR repositories, encrypted RDS PostgreSQL and ElastiCache
Redis, versioned private artifact storage, empty Secrets Manager containers, and a
service-account-bound gateway IRSA role. An authenticated plan proposed 36 resources;
it did not apply or create anything.

### CP4 — Delivery and narrow browser access

Define Helm/Kustomize runtime delivery, Argo CD or equivalent GitOps contracts,
immutable ECR image references, and cloud bootstrap/smoke scripts. When a browser
review path is needed, use an ALB for the Console, API, and identity provider only;
Redis, MLflow, Prometheus, Grafana, Tempo, Kubernetes, and databases stay private.

**Status: delivery contracts implemented and statically validated only.** The Helm
chart has an IRSA annotation hook, PDB, immutable-image field, and opt-in ALB Ingress;
the Argo CD Application is deliberately unconnected. No image was pushed, cluster
bootstrapped, Argo application synced, ALB created, or smoke/destroy command run.

### CP5 — Operations and automation

Add OTel, Prometheus, Tempo, Grafana, release/admission metrics, audit evidence,
failure/rollback drills, bounded-load checks, cost-query instructions, and a
provider-side teardown checklist. Add a manually dispatched GitHub OIDC workflow with
`plan`, confirmation-gated `apply`, and confirmation-gated `destroy`.

**Status: operations and automation contracts are implemented/static only.** Existing
local OTel/Prometheus/Tempo/Grafana and release/remediation demos define the expected
cloud evidence. The repository now has account-guarded scripts and a manual GitHub
OIDC workflow. A local operator completed an authenticated read-only plan; no GitHub
OIDC role has been assumed, and no apply/destroy, cloud telemetry, or Cost Explorer
query has run.

### CP6 — Separately authorized cloud pilot

Only after CP0–CP5 merge and a budget/owner authorization, execute a time-boxed
Terraform create → bootstrap → success/failure proof → observability/cost query →
destroy cycle. Record exact evidence in
[`docs/governance/VALIDATION.md`](../governance/VALIDATION.md). This is the only step
that may change the cloud maturity label.

## Intended AWS scope

```text
Internet (narrow browser path only)
        ↓
ALB → Operator Console / API / identity provider
        ↓
Private EKS
  ├─ signed multi-tenant gateway
  ├─ CPU model runtimes by default
  ├─ model release / remediation / agent-tool / self-service services
  ├─ OTel Collector, Prometheus, Tempo, Grafana
  └─ GitOps controllers where adopted
        ↓
RDS PostgreSQL · ElastiCache Redis · S3 model artifacts · ECR · Secrets Manager
```

This is the intended architecture, not an assertion that it has run. The first cloud
pilot should remain CPU-first. A GPU node group and runtime are a distinct,
cost-approved experiment after the CPU cloud control loop is validated.

## Acceptance boundary

Cloud-pilot readiness means the architecture is reviewable and static validation
passes. It does **not** mean AWS deployment, GPU execution, cloud throughput, managed
MLflow, ALB routing, browser SSO, cost, or teardown has been proven.

See [`real-workload-pilot.md`](real-workload-pilot.md) for hardware/runtime research;
this document is the authoritative staged engineering sequence.
