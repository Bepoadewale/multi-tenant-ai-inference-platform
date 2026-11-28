# Single-L4 AI Inference Infrastructure Project Report

> **Status: PRE-GPU DRAFT — NOT THE FINAL PROJECT REPORT.** The repository has
> substantial local implementation, static AWS preparation, and CI evidence, but
> Read-only AWS checks now show 4.0 applied On-Demand G/VT vCPUs; this clears the
> quota threshold for one `g6.xlarge`, but the project remote state, lock table, and
> Budget are absent and no apply is authorized. No L4 host, CUDA computation, vLLM
> inference, GPU benchmark, live GPU incident, AWS bill, or cloud teardown has been
> recorded. Complete the empirical sections from real evidence after an authorized
> GPU batch; do not remove this banner before the final acceptance review.

## Report status and evidence labels

This draft collects project facts that can be explained before the L4 is available.
It is not a substitute for the benchmark report, incident reports, manual guide, or
evidence manifest. Use these labels in every chapter:

- **Implemented:** source code exists in the current reviewed branch.
- **Static/CI validated:** parsing, unit tests, mocks, or GitHub checks passed.
- **Local execution:** the feature ran on the local CPU or container stack.
- **AWS plan evidence:** read-only queries or a reviewed non-applying plan.
- **AWS execution:** a real cloud mutation or host operation occurred.
- **L4 execution:** actual NVIDIA L4 computation or model inference occurred.
- **Estimate:** calculated cost not yet verified against settled billing.

The current goal status is in the [persistent goal](../goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md),
[implementation status](IMPLEMENTATION_STATUS.md), [backlog](IMPLEMENTATION_BACKLOG.md),
[execution journal](EXECUTION_JOURNAL.md), and [evidence manifest](EVIDENCE_MANIFEST.md).

## Chapter 1 — Executive summary

**Prepared result:** the repository now contains an isolated single-L4 EC2 plan, a
manual Ubuntu/NVIDIA installation sequence, Ansible host automation, a dedicated
GPU Compose profile, multi-tenant gateway integration, observability configuration,
bounded benchmark/evaluation tools, governed sequential release controls, operator
runbooks, and learning documents. The existing CPU ONNX service remains the executed
inference path.

**Final outcome:** pending. The initial On-Demand G/VT request was denied, then the
existing case was closed with 4.0 vCPUs applied according to the 2026-11-28 read-only
check. This is sufficient by quota only. The project state/lock and Budget are absent,
a private alert recipient and exact saved-plan review are outstanding, and no apply is
authorized. The host has not been provisioned; no real L4 inference result exists.

Complete this summary only after recording the final GPU batch, remaining acceptance
gates, all-in cost estimate and billing status, teardown verification, and unresolved
limitations.

## Chapter 2 — Original repository baseline

The direct source audit describes the baseline in [repository audit](REPOSITORY_AUDIT.md).
It found a FastAPI gateway with signed identity, server-derived tenant authorization,
Redis-backed limits, streaming, telemetry, a CPU ONNX backend, and a vLLM adapter
boundary. The exercised local runtime used deterministic CPU ONNX fixtures. The
existing Terraform environment describes EKS and managed services and is preserved;
this project does not deploy it.

The local validation history is in [`../governance/VALIDATION.md`](../governance/VALIDATION.md).
The baseline dependency audit originally failed; PR #31 added shared dependency
constraints and recorded passing checks. Historical CPU clean-room evidence is not
proof of the separate AWS/L4 deployment.

## Chapter 3 — AI and machine-learning foundations

Use the project-specific [interview preparation](INTERVIEW_PREPARATION.md) and source
documentation to explain model parameters and weights, tokenization, embeddings,
transformer attention, prefill, decoding, sampling, context windows, and evaluation.
The distinction that matters operationally is that model weights occupy device
memory, while active sequences also need temporary attention state and compute.

**Add after L4 execution:** observed startup, prompt processing, token generation,
streaming, and cache behavior for the pinned Qwen model. Explain which facts were
confirmed from runtime metrics and which remain conceptual background.

## Chapter 4 — GPU hardware and accelerator engineering

The authorized design permits one NVIDIA L4 in one `g6.xlarge` EC2 instance. The
host is an EC2 virtual machine, not bare metal. The project does not claim Multi-
Instance GPU (MIG), physical tenant isolation, multi-GPU execution, or distributed
training.

Explain host driver, CUDA driver API, CUDA Toolkit, container runtime, GPU memory,
CUDA kernels, tensor cores, and data transfers using the [manual reproduction guide](MANUAL_REPRODUCTION_GUIDE.md)
and [CUDA performance preparation](../../benchmarks/cuda_performance/README.md).

**Pending evidence:** actual L4 discovery, driver/CUDA versions, available memory,
host/container device access, synchronized computation, utilization, and supported
profiling counters. Do not populate these values from a product specification alone.

## Chapter 5 — AWS infrastructure

The separate Terraform root plans one VPC, public subnet, route, internet gateway,
security group without ingress, least-privilege instance profile, one Ubuntu EC2
instance, and encrypted 100-GiB gp3 root volume. Systems Manager Session Manager is
the intended admin path. Guest systemd expiry and a one-time EventBridge Scheduler
target are independent termination safeguards. See the [Terraform environment](../../infrastructure/terraform/environments/gpu-ec2/README.md).

No resource has been applied for this lab. The pinned-AMI local-state preview is not
a locked remote-state plan and is not authorization to apply. Before apply, refresh
quota, AZ offering, software, current prices, tax and state-storage assumptions,
exact plan, runtime expiry, and the owner-approved resource/cost boundary.

**Final evidence table:** add account/region with public redaction, plan SHA-256,
resource counts, approved expiry, SSM status, provisioning output, destruction
output, and provider-side absence checks. Do not commit saved plans or state.

## Chapter 6 — Architecture and request flow

The proposed topology and flows are drawn in [architecture documentation](ARCHITECTURE.md)
and [single-GPU deployment documentation](../../deployments/single-gpu/README.md).
The intended path is client → signed identity and FastAPI gateway → tenant/model
authorization → shared Redis admission → vLLM OpenAI-compatible endpoint → one L4.
Prometheus, DCGM Exporter, Node Exporter, Grafana, Alertmanager, OpenTelemetry, Tempo,
and MLflow are local supporting services with private or loopback-bound ports.

Label diagrams as **proposed** until each link is exercised. Two gateway containers
on one host do not make an HA service; they share the host, network, Redis instance,
and GPU.

## Chapter 7 — Linux, drivers, and container GPU setup

The [manual reproduction guide](MANUAL_REPRODUCTION_GUIDE.md) deliberately teaches
manual setup before the Ansible role. The intended sequence verifies Ubuntu/kernel,
installs matching headers and the reviewed driver, reboots through SSM, checks
`nvidia-smi`, configures NVIDIA Container Toolkit, validates a CUDA container, and
runs real PyTorch device computation. Ansible should follow only after the manual
steps are understood.

**Pending:** actual output, package versions installed on the pinned AMI, reboot
result, Docker runtime state, CUDA container output, PyTorch device and numerical
verification, and a second Ansible run showing no unintended changes.

## Chapter 8 — CUDA and performance engineering

The preparation code contains a CUDA vector-add kernel, synchronized PyTorch matrix
experiments, and a bounded Triton vector-add exercise. The guide also prepares one
short Nsight Systems timeline and an optional Nsight Compute sample; profiler results
must be kept separate from unprofiled timings. The write-up must explain threads,
blocks, grids, warps, memory hierarchy, launch overhead, host/device transfers,
precision, and bottleneck analysis. The [CUDA lab guide](../../benchmarks/cuda_performance/README.md)
defines the dry-run and exact host commands.

**Pending:** compiled CUDA and Triton kernel output, CPU/GPU measurements, warm-up and
repetitions, precision comparisons, profile availability/results, hardware limits, and
charts generated from real runs. Local plans and source code are not performance
results.

## Chapter 9 — Language models and serving

The planned first model is `Qwen/Qwen2.5-1.5B-Instruct`; the runtime candidate is
pinned vLLM. Revision, license, weights, image digest, supported precision, context,
and memory requirements must be rechecked before model download. The [deployment
guide](../../deployments/single-gpu/README.md) keeps vLLM private and uses a stable
served alias.

**Pending:** manual startup, artifact digest from downloaded files, `/v1/models`,
real completion and stream, health/readiness, real GPU activity, cold start, and
graceful shutdown. Static image/model metadata is not inference evidence.

## Chapter 10 — Multi-tenant platform

The gateway verifies signed identities, derives tenant identity server-side, checks
model access, and uses Redis scripts and request-scoped leases for shared request,
token, concurrency, and bounded-queue decisions. The local executed path remains CPU
ONNX. Logical quotas do not reserve VRAM or isolate the physical GPU.

PR #58's CI verifies tenant spoof denial and local Redis recovery across the gateway
replicas; see the [incident report](incidents/INCIDENT-LOCAL-REDIS-001.md). The
authenticated GPU benchmark is prepared in the [benchmark guide](BENCHMARK_REPORT.md).

**Pending:** real vLLM accounting, GPU requests through each gateway replica,
tokenizer usage reconciliation, cancellation, failure cleanup, tenant contention,
and safe overload on the single L4.

## Chapter 11 — Model management and releases

The prepared release path binds model revision, artifact digest, runtime image and
configuration, evaluation report, suite digest, source commit, and independent
approval. A host-side controller checks active state and model snapshot files, then
restarts vLLM sequentially and attempts rollback if readiness fails. Its tests use
fakes; no running model has been switched.

**Pending:** real model evaluation, approval, candidate rejection, model-byte check,
sequential reload, actual inference verification, and recovery to the known-good
model on the L4. Do not describe this single-GPU approach as a zero-downtime canary.

## Chapter 12 — Observability

The Compose profile configures DCGM and host exporters, Prometheus, Grafana,
Alertmanager, OpenTelemetry, Tempo, Redis metrics, and vLLM/gateway metrics. Static
configuration validators have passed. Prompt and completion attributes are removed
by profile configuration as defense in depth; actual emitted spans still require
inspection.

**Pending:** real L4 metrics, metric names and units observed from the runtime,
dashboard panels under load, a controlled alert, request-correlated trace, metric
overhead, and sanitized screenshots or output.

## Chapter 13 — Benchmark methodology and results

The [benchmark report](BENCHMARK_REPORT.md) has the fixed workload matrix, metadata
schema, analysis questions, cost formulas, and empty results table. It separates
direct vLLM server behavior from the authenticated gateway path. Direct-versus-
gateway deltas are exploratory, not pure gateway overhead, and client-side semaphore
wait is not server queue time.

**Final results:** pending. Populate only from authorized run artifacts. Include
sample count, warm-up, repetitions, confidence limitations, latency percentiles,
token throughput, failure rates, VRAM, GPU/CPU/memory, and charts based on actual
data. Preserve failed and partial results.

## Chapter 14 — FinOps and costs

The current cost model is an estimate, with an initial project ceiling of USD $25.
It includes more than GPU time: public IPv4, encrypted disk, state/lock storage,
scheduled expiry, transfer, tax assumptions, and contingency. See [cost report](COST_REPORT.md).

**Final update required:** refresh prices and tax assumptions before apply; record
actual instance start/stop times, cumulative hours, estimate formula, AWS billing
evidence, and settlement delay. If billing has not settled, say so. Cost per token
must use a stated allocation method and actual measured tokens.

## Chapter 15 — Security

The prepared design uses signed identities, server-side tenant derivation, model
authorization, least-privilege roles, IMDSv2, encrypted gp3, no inbound security
group rules, private internal services, pinned images and artifacts, and sanitized
evidence. Redis limits are logical controls; two gateways share one host; there is
no hardware partitioning.

**Pending:** real IAM/SSM behavior, actual network exposure inspection, secret scan
of evidence, trace attribute inspection, and teardown checks. Do not publish instance
identifiers, keys, tokens, raw state, prompt text, or sensitive endpoints.

## Chapter 16 — Reliability and service objectives

The gateway maps known shared dependency failures to service-unavailable responses,
uses bounded queues and timeouts, and tracks request leases. Current dashboard
thresholds are laboratory diagnostics, not production SLOs. One EC2 host remains a
single point of failure.

**Pending:** measured latency/error baseline, justified lab objectives, alert
behavior, actual recovery duration, and restart recovery on EC2. Do not infer HA from
two containers.

## Chapter 17 — Incident history

The only substantive incident currently recorded is a real local CI Redis outage:
the gateway returned 500 instead of expected 503 because a rollout-state read raised
before admission error handling. The fix made the shared read fail closed and
persisted shared routing state before local mutation; CI verified 503 from both
gateways, Redis recovery, and readiness. See [incident 001](incidents/INCIDENT-LOCAL-REDIS-001.md).

This is a local CPU-stack incident, not an AWS, GPU, or production incident. Add each
future L4 failure and recovery from observed logs and telemetry, with timestamps,
root cause, failed approaches, fix, and measured recovery time.

## Chapter 18 — Infrastructure automation

Terraform contains a separate single-host root with account, region, AMI, type, tag,
expiry, encryption, and teardown guards. Ansible pins package candidates and configures
the host after manual learning. Compose runs vLLM, two gateways, Redis, and monitoring
on one node. Make commands offer preflight, plan, configure, deploy, smoke, benchmark,
evaluation, evidence, and teardown paths.

**Pending:** remote locked plan, actual apply, manual host install, Ansible convergence
twice, application deployment, and destroy/absence verification. Static validation
does not satisfy these gates.

## Chapter 19 — CI/CD

Ordinary PR workflows run local/static validation, security checks, image and config
validation, and CPU local end-to-end behavior. The dedicated GPU cloud steps are not
part of routine PR CI. Workflow run IDs and exact head commits are in the evidence
manifest and tickets.

**Final review:** verify every required PR is still open or merged as authorized,
required checks pass for the final head, no secret entered public Git history, and no
ordinary PR workflow can create billable GPU infrastructure.

## Chapter 20 — Clean-room reproduction

Historical clean-room records validate local CPU behavior; they do not recreate the
GPU environment. The project requires one complete final clean-room GPU reproduction
from a clean project state, after automation and documentation are ready. Do not
repeat it for routine documentation changes; repeat only if it fails or a material
fix needs verification.

**Pending:** exact preflight, approved plan/apply, manual driver pass, CUDA/PyTorch,
Compose deployment, authenticated inference, observability, representative benchmark,
evaluation, fault and recovery, evidence export, teardown, and independent absence
verification.

## Chapter 21 — Teardown

No project GPU resource has been created, so no GPU teardown has occurred. The
prepared Terraform destroy command is scoped to the isolated root and has a
destroy-plan digest guard. The guest and scheduled expiry are independent safeguards,
not reasons to omit planned destroy and verification.

**Pending:** run the exact reviewed destroy plan, verify EC2/EBS/network/IAM/scheduler
resource absence by project scope, identify retained state or artifacts, and check
billing settlement. Never use account-wide deletion.

## Chapter 22 — Engineering decisions and trade-offs

Current decisions include one EC2 host over Kubernetes to teach the device stack;
On-Demand over interruption-prone Spot for a bounded first run; loopback and SSM
access over public service ports; logical shared quotas over claims of physical
isolation; and sequential model release over an unverified concurrent canary. Revisit
these decisions using measured data, cost, and operational evidence.

## Chapter 23 — Production evolution

Discuss future multi-GPU placement, NCCL-backed tensor/pipeline parallelism, managed
or self-managed Kubernetes, model distribution, regional cells, capacity forecasting,
fleet-level quota, and distributed training as architectural options. They are
background only; this project implements one L4 and no distributed training.

## Chapter 24 — Limitations

Before quota approval: no AWS instance, L4 device access, driver installation,
PyTorch GPU computation, vLLM model load, real GPU tenant request, live DCGM metric,
inference benchmark, model release/rollback, GPU incident, actual AWS cost, or teardown
has been observed. The current local CI evidence does not change these boundaries.

Complete this chapter after execution with additional limitations discovered in the
actual run. Do not remove limitations to make the project appear more complete.

## Chapter 25 — Interview preparation

Use the [project-specific interview guide](INTERVIEW_PREPARATION.md) for more than
100 questions, design trade-offs, troubleshooting cases, and STAR examples. Update
answers that depend on measurements only after the corresponding evidence exists.

## Chapter 26 — Lessons learned

Known lessons include separating tenant policy from model execution, reserving shared
capacity atomically, letting failures surface as explicit dependency errors, using
bounded operations, and recording what tests do not prove. Add lessons from actual
L4 installation, serving, failure, performance, cost, and teardown; none should be
invented in advance.

## Chapter 27 — Glossary

Use the [AI infrastructure handbook](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/59)
and interview guide for the prepared glossary and concept explanations. Update the
handbook reference to a repository file link when PR #59's content is part of the
report's merged base.

## Chapter 28 — Evidence and implementation index

The [evidence manifest](EVIDENCE_MANIFEST.md) classifies artifacts and their limits.
At finalization, add the exact PRs, commit SHAs, CI runs, AWS plan digest, sanitized
screenshots/log summaries, benchmark result files, incident reports, evaluation
records, cost status, and teardown checks. Include evidence links near the claims
they support.

## Final completion checklist

- [ ] All 12 phase gates have truthful status and evidence.
- [ ] AWS and L4 execution is verified from actual command output and telemetry.
- [ ] Benchmark charts use retained measurements and show their limitations.
- [ ] Model evaluation, release, rejection, rollback, and recovery have real evidence.
- [ ] Every reported incident has genuine failure and recovery evidence.
- [ ] The final clean-room GPU reproduction succeeds once.
- [ ] Authorized resources are destroyed and independently checked absent.
- [ ] Final estimated and settled AWS costs are distinguished.
- [ ] Required PRs, CI, documentation, references, and PDF/Word exports are reviewed.
- [ ] The $25 cap and all remaining limitations are explicitly accounted for.

Until these checks pass, this file remains a draft rather than the final project
report.
