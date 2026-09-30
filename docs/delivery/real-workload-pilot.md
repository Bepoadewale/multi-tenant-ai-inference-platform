# Real-Workload Pilot Guide

This guide defines the next phase after the executed local-first flagship: a small,
controlled cloud pilot that produces **real workload evidence** without pretending a
portfolio demo is production-ready.

Nothing in this document is executed evidence yet. GPU, cloud cost, managed services,
and public hosting remain unexecuted until recorded in
[validation evidence](../governance/VALIDATION.md).

Terraform is the required authority for future cloud infrastructure provisioning and
teardown. Do not create or delete pilot resources manually after account bootstrap:
review a Terraform plan before apply, record its state backend/locking configuration,
and use Terraform destroy plus provider verification at the end of each experiment.

## Pilot objective

Prove the same governed path against a real model runtime and real infrastructure:

```text
authenticated tenant -> shared admission -> real GPU model runtime -> metering
-> metrics/traces -> canary -> gate -> promotion or rollback
```

Start with a single GPU virtual machine and synthetic traffic. Move to Kubernetes only
after that path is measured and cost-controlled.

## Local-first readiness versus production evidence

| Concern | Current local evidence | Before a production claim |
| --- | --- | --- |
| tenant inference | two signed gateways, Redis admission, CPU ONNX responses | enterprise identity, durable production stores, capacity test |
| model release | MLflow fixtures, digests, independent approval, canary/promotion/rollback | real model evaluation policy and protected delivery path |
| capacity | Redis simulated-pool accounting | actual runtime, GPU metrics, scheduling, and measured saturation |
| observability/FinOps | OTel, Tempo, Prometheus, Grafana, Decimal fixture pricing | retained production telemetry and cloud billing reconciliation |
| operator console | local BFF with synthetic fixture identities | SSO/session/CSRF controls, per-user policy, audit retention |
| infrastructure | Terraform contracts statically validated | reviewed Terraform apply, smoke, rollback, destroy, cost evidence |

The local implementation is a completed control-loop demonstration, not a claim that
these production conditions have been executed. This table must be updated with
measured evidence—not marketing language—after a pilot.

## Accounts and prerequisites

Create or obtain access to the following. Do not give passwords, access keys, private
keys, recovery codes, or API tokens to Codex.

| Resource | Purpose | Pilot guidance |
| --- | --- | --- |
| Dedicated cloud account | Isolate billing and blast radius | Use a non-root administrator, MFA, and a separate `pilot` environment. |
| Billing budget | Bound spend | Alert at 50%, 75%, 90%, and 100%; set a low GPU service quota. |
| GitHub Actions OIDC role | CI deployment identity | Prefer short-lived role assumption over stored AWS keys. |
| Container registry | Immutable images | Amazon ECR is the AWS option; use least-privilege push/pull roles. |
| Object storage | Model artifacts and MLflow artifacts | Use an encrypted, versioned bucket with lifecycle expiry. |
| Domain and Cloudflare account | Later protected public demo | A temporary Quick Tunnel is not a stable deployment. |
| Terraform state backend | Reproducible cloud lifecycle | Encrypt state, restrict access, and enable locking before any apply. |
| Model source | Open-weight model artifact | Check licence, size, and any gated-download requirements before use. |

## Cheapest credible progression

### Phase 1 — local and temporary public view

Keep the existing local Docker Compose stack. The supported launcher installs
`cloudflared` with Homebrew when needed, starts the local stack, creates a temporary
Cloudflare Quick Tunnel, and prints the operator-console URL:

```console
make public-demo
```

Quick Tunnel URLs are temporary and public. Do not place them in README files or use
them for a persistent product demo. The local console includes bounded actions, so do
not share one broadly without a read-only mode or access protection. `Ctrl-C` stops
the tunnel; run `make clean-local` separately to remove project-owned local services.

### Phase 2 — one real GPU VM

Use one GPU VM, Docker, NVIDIA drivers/container toolkit, a real runtime such as vLLM
or Triton, and a small permissively licensed model. Point the existing gateway at the
runtime through a narrowly configured backend adapter. Generate only synthetic,
non-sensitive traffic with k6 or Locust.

This phase proves real model memory, latency, throughput, timeout behaviour, and GPU
runtime telemetry. It is substantially cheaper and easier to destroy than a complete
managed Kubernetes environment.

Use a time-boxed experiment window, instance tags, budget alerts, and immediate
shutdown after each test. Spot capacity can lower compute cost but is interruptible;
design the experiment to tolerate termination rather than treating Spot as reliable
production capacity.

### Phase 3 — managed Kubernetes pilot

Only after Phase 2 succeeds, create one small managed Kubernetes cluster:

```text
EKS control plane
├── small CPU system node group
├── one GPU node group, scaled to zero outside test windows
├── ECR image registry
├── S3 model/MLflow artifacts
├── PostgreSQL and Redis
├── OpenTelemetry / Prometheus / Grafana
└── Kueue and workload admission experiments
```

EKS incurs a control-plane fee even without worker nodes, and worker instances,
storage, public IP addresses, data transfer, and managed dependencies are charged
separately. Do not leave a cluster running between experiments unless its cost is an
intentional decision.

## Pilot resource checklist

### Required for the first real GPU experiment

- [ ] Cloud account with MFA, budget alarms, and GPU service quota.
- [ ] One region selected after confirming GPU capacity and price.
- [ ] One GPU VM with encrypted block storage and minimal inbound security group.
- [ ] Docker, NVIDIA driver, NVIDIA Container Toolkit, and pinned model-runtime image.
- [ ] One documented model with licence review and SHA-256 artifact digest.
- [ ] ECR or another trusted container registry.
- [ ] S3/object storage for model artifacts and evidence reports.
- [ ] Synthetic tenant identities and synthetic prompts only.
- [ ] Separate load generator and a bounded load-test plan.
- [ ] Scheduled shutdown and teardown verification.

### Add for the Kubernetes pilot

- [ ] Terraform-managed VPC, subnets, security groups, encrypted remote state, and locking.
- [ ] EKS cluster, CPU nodes, GPU node pool, and node autoscaling policy.
- [ ] PostgreSQL with backup/recovery plan; Redis with persistence/failover decision.
- [ ] Ingress/TLS, DNS, and an authenticated operator-console boundary.
- [ ] Secret manager/KMS; no application secrets in GitHub Actions or manifests.
- [ ] OTel Collector, metrics, traces, logs, and a retention/cost policy.
- [ ] Kueue admission policy and real GPU workload tests.
- [ ] GitHub Actions OIDC role, image provenance/SBOM, and protected deployment path.
- [ ] Disaster/rollback test and project-scoped teardown runbook.
- [ ] Reviewed Terraform destroy plan and post-destroy provider verification.

## Real tests to execute

1. Normal multi-tenant inference against the GPU runtime.
2. Noisy-neighbour burst: tenant A exhausts its allocation while tenant B remains
   within its own limits.
3. Bounded queue and timeout behaviour under genuine GPU pressure.
4. Candidate canary with actual request latency/error evidence.
5. Bad candidate rollback due to quality or latency regression.
6. GPU workload admission/rejection with Kueue after the Kubernetes phase begins.
7. Node/runtime interruption and controlled recovery.
8. Cost report that separates measured cloud usage from local fixture estimates.

## GPU scheduling and autoscaling in the pilot

The local `simulated-l40s` pool is Redis quota accounting, not a Kubernetes scheduler.
For real GPU placement, use the completed
[GPU Scheduler Lab](https://github.com/Bepoadewale/gpu-scheduler-lab) as the reference
for Kueue/Volcano experiments with explicitly simulated resources, then validate actual
device-plugin/GPU Operator/DCGM behavior only on a real NVIDIA environment.

HPA/KEDA scales serving pods; node groups or Karpenter scale the underlying GPU
capacity. They act on different delays and must be tested separately. Candidate signals
include active requests, queue depth/wait, token rate, latency, and—only on real
hardware—GPU/KV-cache pressure. Keep warm replicas for latency-sensitive models and
record cold-start behavior. A real multi-GPU model additionally needs an explicit
tensor-parallel/topology plan, compatible SKU labels, affinity, and an NVLink review.

## Cost and safety rules

- Do not use a personal/root cloud account for experiments.
- Do not expose the operator console as a persistent public service without
  authentication or a read-only public mode. The documented `make public-demo` Quick
  Tunnel is a brief, operator-controlled exception for a local walkthrough only.
- Tag every resource: `Project=multi-tenant-ai-platform`, `Environment=pilot`,
  `Owner=bepoadewale`, and an expiry/TTL tag.
- Use one region, one environment, one GPU at a time, and scale GPU capacity to zero
  when idle.
- Prefer documented teardown over broad account-level deletion commands.
- Terraform is the sole provision/teardown path for pilot cloud resources: review
  `terraform plan`, apply approved changes, then use `terraform destroy` and verify
  that tagged resources and billable dependencies are gone.
- Record actual instance type, region, model, runtime, driver, traffic, duration, and
  billable resources before publishing any performance or cost claim.

## Free and low-cost choices

| Choice | Suitable for | Boundary |
| --- | --- | --- |
| Local Docker + ONNX fixtures | Core control-loop development | No real GPU performance evidence. |
| Cloudflare Quick Tunnel | Short controlled walkthrough | Temporary public URL; local machine must remain running. |
| Oracle Always Free compute | Lightweight control plane, docs, or static demo | No free GPU; idle instances may be reclaimed. |
| One time-boxed GPU VM | First real runtime validation | Not free; stop/terminate immediately after evidence capture. |
| Spot GPU capacity | Interruptible experiments | Never assume availability or use without recovery handling. |
| EKS pilot | Real Kubernetes/GPU scheduling validation | Control-plane and dependent-resource costs continue while provisioned. |

## Official references

- [AWS EKS pricing](https://aws.amazon.com/eks/pricing/) — cluster and separately
  billed worker-resource model.
- [AWS EC2 pricing and Spot overview](https://aws.amazon.com/ec2/pricing/) —
  on-demand, Spot, and Savings Plan trade-offs.
- [Amazon ECR private registry](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Registries.html)
  — image registry/permission model.
- [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
  — current free compute allocation and idle-reclamation conditions.
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
  — temporary public local-development tunnel.

## Completion evidence for this future phase

Do not change project maturity based on this guide. A real-workload claim requires a
new validation record with: cloud/provider, region, instance type, model/runtime,
identity boundary, exact commands, observed metrics, failure/rollback result,
cost evidence, and verified teardown.
