# Single-L4 GPU Infrastructure Goal

**Status: ACTIVE — Phase 2, isolated EC2 infrastructure (static preparation only)**
**Source of truth:** this document, the linked execution journal, pull requests, and evidence records.  
**Last updated:** 2026-11-27
**Current branch:** `codex/gpu-ec2-foundation` (stacked on PR #30)
**Registration PR:** [#30 — docs: register single-L4 GPU infrastructure goal](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/30) (open; current head `04cb564`, required checks passed). **PR #32** is being prepared against that branch.
**Baseline repair PR:** [#31 — fix: apply audited dependency constraints](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/31) (open; head `9710932`, required checks passed).
**GPU quota:** 4-vCPU On-Demand G/VT increase requested in `us-east-1`; AWS status is **PENDING**. Request ID is recorded in the execution journal and evidence manifest. This does not authorize infrastructure creation.

## Project objective

Extend `Bepoadewale/multi-tenant-ai-inference-platform` into a reproducible, production-oriented learning lab for a logically multi-tenant language-model service backed by exactly one NVIDIA L4 GPU on AWS EC2. Carry the work from source audit and official research through isolated Terraform infrastructure, manual then automated Ubuntu/NVIDIA/CUDA setup, GPU experiments, vLLM model serving, gateway integration, observability, benchmarks, evaluation and governed releases, incident response, CI, clean-room reproduction, evidence export, and verified teardown.

The project is also a hands-on learning resource. Its documentation must explain the concepts, decisions, commands, expected results, failure modes, diagnosis, recovery, and larger-production implications in plain English so an engineer can reproduce the system without an AI coding agent. Do not involve DavDeploy and do not create another repository.

## Current repository baseline

The audited starting revision is `c8f02ed` (`docs: explain the flagship in plain English (#29)`) on a clean `main` tracking `origin/main`. The repository guide requires small PRs, no direct pushes to `main`, honest hardware claims, and executed clean-room evidence before an implementation PR is called ready for human review.

Direct source inspection confirms; see the [repository audit](../gpu-lab/REPOSITORY_AUDIT.md) for the file-by-file evidence and gaps:

- `gateway/` contains FastAPI APIs, Ed25519 identity verification, server-derived tenant and role, model authorization, Redis Lua-backed shared admission/metering, routing, streaming, OpenTelemetry, and ONNX and vLLM backend adapters.
- `GatewayService` selects vLLM when a routed target has a `backend_url`; the existing catalog and executed local service use CPU ONNX fixtures. The existing vLLM adapter is a boundary, not evidence that vLLM has run.
- The current streaming gateway counts emitted chunks as completion tokens and supplies a fixed streaming TTFT value; token reservation uses a word-count estimate. These are concrete integration items to audit and improve without weakening the CPU path.
- Tests cover authentication, tenant isolation, quotas, ONNX, API streaming, and other local controls. Existing validation records two clean-room local CPU cycles and static/authenticated read-only AWS plan evidence, not GPU execution.
- `infrastructure/terraform/environments/aws/` is the separate planned EKS/managed-services contract. Its optional GPU node module is not the requested EC2 environment. `platform/kubernetes/vllm-gpu-deployment.yaml` uses a mutable `latest` image and a different model. Preserve this future EKS contract; do not deploy it or reuse it as the EC2 implementation.
- Docker Compose, Prometheus, Grafana, Tempo, and local gateway dashboards exist. A GPU dashboard file and Kubernetes GPU manifests are contracts, not live GPU telemetry.
- Existing local scope is reported complete; GPU/vLLM, DCGM, cloud model hosting, and EKS execution remain unexecuted.

**AWS resource inventory:** on 2026-11-26, read-only calls using the designated key profile confirmed the configured account matches the expected account. `resourcegroupstaggingapi get-resources` with the exact project tag and `ec2 describe-instances` with the exact project tag both returned empty lists in `us-east-1`. This is not proof that no untagged or differently tagged resource exists; historical records also say the EKS-oriented plan was no-apply. No AWS mutation occurred.

**Quota request:** after the user asked to submit it immediately, the authenticated
`ai-platform-pilot-key` identity was verified and the current quota/history were
checked to avoid a duplicate. AWS accepted a request for 4 On-Demand G/VT vCPUs for
one `g6.xlarge`; its current status is **PENDING**. The applied quota remains 0, so a
GPU launch remains blocked. No compute resource or spend was created.

**GitHub state:** `gh auth status` identified the authenticated account as Bepoadewale. PRs #30 and #31 are open; neither has been merged. Required checks pass on PR #30 head `04cb564` and PR #31 head `9710932`. PR #32's Phase 2 infrastructure package is being prepared as a stacked PR based on #30.

The current package sequence and spending/authorization gates are in the [GPU lab
implementation backlog](../gpu-lab/IMPLEMENTATION_BACKLOG.md), with the current
provisional price envelope in the [cost report](../gpu-lab/COST_REPORT.md) and
evidence classification in the [evidence manifest](../gpu-lab/EVIDENCE_MANIFEST.md).
The execution journal retains failed attempts and session history; this goal remains
the durable status page.

## Scope and architectural constraints

- AWS only for cloud infrastructure; preferred region `us-east-1`. Use a standard Ubuntu AMI and learn/install the NVIDIA stack manually before writing idempotent Ansible automation.
- One NVIDIA L4 GPU EC2 instance at a time; start at `g6.xlarge`, consider `g6.2xlarge` only with measured CPU or system-memory justification. No T4, A10G, A100, H100, other accelerator, EKS, self-managed Kubernetes, multi-GPU, RDS, ElastiCache, NAT Gateway, persistent load balancer, or expensive managed monitoring in this project.
- Keep the local CPU ONNX inference path, its evidence, and the existing EKS contract intact. Add an isolated EC2 GPU profile and adapt shared gateway components only through narrow interfaces.
- Target model begins with `Qwen/Qwen2.5-1.5B-Instruct`; verify official license, revision, artifact integrity, compatibility, and memory needs before deployment. Try larger/quantized variants only after the first model is stable and within budget.
- Use Terraform for AWS create/destroy; Ansible for repeatable host configuration after manual learning; Docker Compose for the single-host application stack. Prefer Systems Manager Session Manager and no public inbound service ports. Enforce IMDSv2, encryption, project tags, account/region/instance guards, exact reviewed plans, and independent teardown verification.
- Tenant identity remains server-side. Redis quotas are logical admission controls, not physical GPU isolation. Never claim GPU partitioning, high availability, distributed computing, zero-downtime releases, bare-metal administration, or production reliability without corresponding evidence.
- No prompts, completions, credentials, keys, session tokens, raw state, saved plans, or unreviewed environment dumps in public Git. Keep model artifacts and large/raw evidence outside the repository when necessary; publish sanitized summaries and references.
- Do not use or involve DavDeploy.

## Phases and acceptance gates

Each phase remains incomplete until its execution evidence is recorded. Static code or a diagram alone does not satisfy an execution gate.

1. **Repository audit, research, architecture:** inspect source, tests, Compose, Terraform, runtime abstractions, gateway, admission, identity, registry, telemetry, CI, docs, and historical evidence; run existing validation and record baseline failures; research current official documentation; produce proposed topology, data-flow/security/release/teardown diagrams, risk register, and actionable backlog. Gate: baseline and gaps evidenced; references and decisions recorded.
2. **Isolated AWS EC2 infrastructure:** separate Terraform root for one L4, minimum VPC/subnet/routes/security/IAM/instance profile, encrypted gp3, IMDSv2, tags, SSM, expiry guard, reviewed exact saved plan, and account/region/instance/one-GPU guards. Gate: within approved spend/time boundary, one authorized L4 is reachable privately through SSM and its exact resources can be destroyed and independently checked.
3. **Ubuntu, drivers, CUDA, containers:** manually install and verify compatible pinned Ubuntu/kernel/driver/CUDA/Docker/NVIDIA Container Toolkit/PyTorch versions; run a real CUDA container and synchronized PyTorch GPU computation; then implement and repeat Ansible for idempotency. Gate: L4 is visible and real host/container GPU computation succeeds; versions and troubleshooting are recorded.
4. **GPU performance lab:** repeatable CPU/GPU vector and matrix workloads, transfer/memory/precision/batch experiments, synchronization-correct timing and profiling; Triton/Nsight only if compatible and useful. Gate: actual measurements and profiler evidence, no fabricated numbers.
5. **vLLM model serving:** pin vLLM and model revision; manually fetch/verify and serve Qwen 1.5B first, then make Docker deployment reproducible; validate real API, stream, health/readiness, startup, GPU telemetry, shutdown and cache behavior. Gate: real L4 inference and evidence.
6. **Multi-tenant integration:** preserve ONNX; integrate vLLM with authenticated gateway, tenant model grants, shared Redis request/token/concurrency/queue limits, reservation/reconciliation, timeout/cancellation/failure cleanup, privacy-safe metering, and synthetic customer-support/engineering/research tenants. Gate: real GPU requests and cross-tenant/security/failure behaviors proven across replicas.
7. **GPU and AI observability:** collect available DCGM, node, vLLM, gateway, Redis, Prometheus, Grafana, Alertmanager, OpenTelemetry, and Tempo signals; correlate requests safely and exercise alerts. Gate: live workload data, controlled alert behavior, metric definitions/limits documented.
8. **Benchmarking and FinOps:** prebuild controlled benchmark scripts; measure latency, throughput, memory, concurrency, startup, contention, overload, model and precision trade-offs; record runtime metadata and raw result references; explain cost formulas and distinguish estimates from settled billing. Gate: reproducible real-GPU report with charts and evidence.
9. **Evaluation and governed model releases:** version a synthetic evaluation set; use deterministic checks where possible; bind model revision/digest and evaluation to immutable release plans, independent approval, sequential release/reject/rollback for one GPU. Gate: real evaluation, a rejected candidate, and verified rollback; no concurrent canary claim without proof.
10. **Incident and recovery exercises:** safely inject reversible GPU/driver/container/model/queue/Redis/gateway/metrics failures; preserve real logs and evidence; report diagnosis, root cause, fix, recovery duration and limits. Gate: representative real incidents and independently checked recovery.
11. **Automation and CI:** Terraform/Ansible/Compose/Make orchestration, local/static CI, security and dependency checks, cloud actions gated and never run on ordinary PRs, repeatable configuration. Gate: clean automation tests and preserved existing validation.
12. **Clean-room and teardown:** reproduce from clean project state, capture evidence, destroy only authorized project resources, independently verify absence and report estimated/settled costs. Gate: all required lifecycle evidence and no unintended remaining billable project resources.

## Required documentation and evidence

Write documentation with every implementation package. Maintain the goal, PR-numbered tickets (`docs/tickets/pr-<number>.md`), execution journal (`docs/gpu-lab/EXECUTION_JOURNAL.md`), implementation status, validation, architecture diagrams, risk register, sanitized evidence manifest, benchmark/incident/cost records, and phase-specific runbooks as work proceeds.

Final deliverables, when the evidence exists: `FINAL_PROJECT_REPORT.md`, `MANUAL_REPRODUCTION_GUIDE.md`, `AI_INFRASTRUCTURE_HANDBOOK.md`, `BENCHMARK_REPORT.md`, `INCIDENT_RESPONSE_HANDBOOK.md`, `INTERVIEW_PREPARATION.md` (at least 100 substantive Q&As with follow-ups and evidence-based STAR examples), `COST_REPORT.md`, and a searchable, professionally rendered PDF report; editable Word output where practical. These must explain the real implementation and label every proposed, static, simulated, local, AWS-planned, AWS-executed, measured, estimated, or billed claim accurately.

Evidence manifest entries identify filename, capture date, phase, PR, commit, what is and is not demonstrated, and whether evidence is local/simulated/static/real AWS. Use genuine screenshots or genuine sanitized command output. Never synthesize console screenshots or measurement results.

## Research requirements

Before each relevant implementation, consult current official sources for AWS G6, EC2 drivers, SSM, service quotas, budgets/pricing, Terraform/AWS provider, Ubuntu, NVIDIA driver/CUDA/container toolkit/DCGM/Nsight, Docker, PyTorch/Profiler, Triton, vLLM, Qwen licensing/model card, Prometheus, Grafana, Alertmanager, OpenTelemetry/GenAI conventions, Redis, MLflow, evaluation, and GitHub Actions. Record the exact version/date and how the source affected a decision. Do not add a tool merely because it was researched.

## Cost, approval, and resource boundaries

The user set a **maximum initial project AWS budget of USD $25**. This is a ceiling, not a target, and does not grant unlimited spend. Research, source work, static checks, local tests, and preparation happen before paid compute. Before the first billable apply, record a current price/availability/quota check, exact resource list, hourly and full experiment estimate, runtime limit, spend cap, expiry/cleanup mechanism, exact plan review, and teardown procedure. If the exact bounded GPU experiment cannot fit within $25, do not apply; finish safe non-billable work and request additional authorization.

Plan for at most 8–12 cumulative GPU instance hours where feasible. Bundle GPU-dependent tasks, export evidence, and terminate the instance and unneeded support resources immediately after each batch. Never leave it running for writing, review, CI, research, or a waiting period. Budget alerts are notifications, not hard caps. Track instance-hours and estimated spend; retrieve actual billing data when available. No AWS mutation before account/region/permissions/boundary checks and explicit review of the exact saved plan. Keep the local SSO/key profiles private and do not print credentials.

## Current project state

- **Active phase:** Phase 2 — isolated EC2 infrastructure, static preparation only; AWS mutation is blocked.
- **Current task:** complete the static review and evidence for the separate EC2 root, guarded saved-plan workflow, dual expiry, and teardown verification; then open a focused PR. Do not request quota changes or run an AWS mutation yet.
- **Completed:** source audit and initial proposed architecture with AWS, Linux/GPU stack, request/security/admission/inference/observability/model-release/provision/teardown diagrams; risk/research/status/journal and prioritized implementation backlog; README/docs index links; read-only AWS identity and exact project-tag inventory checks; G6 offerings and zero quota checks; initial Price List lookup; both existing Terraform roots passed backend-disabled validation; baseline local lint, 50 tests, Compose configuration, and cloud-delivery validation passed. In dependency PR #31, shared minimum constraints were applied to local and container installs; `make install`, a local image build, Ruff, 50 tests, the audit, Compose config, smoke, and the cumulative CPU/local demo passed. Two successful local clean-room cycles and project-scoped cleanup are documented there. No AWS resource was changed.
- **Outstanding:** finish review of the static EC2 root and scripts and publish PR #32; prepare an exact remote-state plan and refreshed full cost review; recheck dated dependency/model pins before runtime packages; obtain human review/approval for PRs #30–#32; continue non-billable work. GPU apply remains ineligible while the quota increase is pending and until the exact plan, runtime, total cost, tax, expiry, and teardown gates are reviewed.
- **Blocked:** G6 launch in `us-east-1` remains blocked by the account's On-Demand G and VT quota of 0 vCPUs (`L-DB2E81BA`). `g6.xlarge` was offered in several zones, not capacity-guaranteed. No quota increase was requested. The planned request is 4 vCPUs, enough for exactly one `g6.xlarge`; submit it only after the exact plan, full cost, expiry, and teardown gates are ready for review. Independently, no billable apply can happen until all controls fit within the $25 ceiling.
- **Open PRs:** #30 (goal registration; latest docs head `04cb564`, all required checks passed; human review remains open); #31 (dependency audit repair; ready for review; Python, manifests, supply-chain, and two local-e2e workflow checks passed at `9710932`).
- **Relevant commits:** baseline `c8f02ed` on `main`; goal registration `754564d`, `914ecaf`, `612e4d3`, `80ca94e`, `04cb564` on `codex/single-l4-gpu-goal`; dependency repair `e1d9aa0`, `9710932` on `codex/fix-baseline-dependency-audit`.
- **AWS project resources:** no resources created by this goal. Read-only exact-tag and exact-tag EC2 queries in `us-east-1` returned no matches; untagged or differently tagged resources are not ruled out. Historical repo evidence records an authenticated no-apply EKS-oriented Terraform plan on 2026-10-08.
- **Validation:** baseline on `main`: Ruff and 50 tests passed with one Starlette deprecation warning; `pip-audit` failed with 84 advisory records across seven transitive distributions; separate `docker compose config --quiet`, `make terraform-validate`, and `make cloud-delivery-validate` passed. On PR #31: shared constraints resolved the audit; `make verify` passed Ruff, 50 tests, pip-audit, and Compose config; gateway image build and two successful local clean-room cycles passed. Details and the stateful 429 repeat-demonstration failure are recorded in `docs/governance/VALIDATION.md` and `docs/tickets/ticket31.md`. PR #30's four required check names passed in both workflows at `336c1b4`. No GPU validation exists.
- **Final completion:** all essential phase gates above genuinely executed; local CPU/EKS contracts preserved; actual single-L4 AWS, CUDA, vLLM, tenant, telemetry, benchmark, evaluation, release, incident, reproducibility, teardown, cost, and educational-document evidence cross-checked; all PRs resolved; no secrets in history; final resource absence and limitations recorded.

## Change log

- 2026-11-26: Registered the persistent goal and began the source audit. No AWS resource was changed.
- 2026-11-26: Recorded direct audit, read-only AWS findings, dependency-audit repair, clean-room evidence, and current GPU runtime/state/cost research. PRs #30 and #31 are ready for review; checks passed at their recorded commits, and the latest PR #30 research update still requires CI. No AWS resource was changed.
- 2026-11-27: PR #30 checks completed successfully at `336c1b4`. Completed detailed request/stream/Redis failure-path review, researched an independently scheduled expiry design, and recorded a provisional full-resource cost envelope. The $25 ceiling remains a hard cap; no AWS mutation or quota request occurred.
- 2026-11-27: Phase 1 audit/research package reached its documentation gate; Phase 2 begins with static-only Terraform and expiry preparation. The preliminary estimate is not an apply authorization. No AWS mutation or quota request occurred.
- 2026-11-27: Added the repository-required DynamoDB table to the proposed independent state-lock design and cost estimate. The current rounded planning envelope is `$18.35`; PR #30 head `80ca94e` is under its existing CI watcher. No AWS mutation or quota request occurred.
- 2026-11-27: Corrected the state design after re-reading `AGENTS.md`: the existing repository bootstrap already supplies one repository-scoped bucket/table, so the GPU root reuses it with a unique state key. PR #30 commit `04cb564` passed its displayed required checks. No AWS mutation or quota request occurred.
