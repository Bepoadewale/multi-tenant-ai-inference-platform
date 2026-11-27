# Single-L4 GPU Lab Implementation Backlog

This is the ordered work plan for the single-L4 goal. It is a working backlog, not a
claim that any cloud or GPU phase has run. Every package uses its own focused branch
and pull request. Review and required CI checks must pass before merge; implementation
pull requests must include the repository's clean-room evidence.

## Current state

- Phase 1 design gate is complete. The repository audit and candidate architecture are recorded in
  `REPOSITORY_AUDIT.md`, `ARCHITECTURE.md`, and `RESEARCH_NOTES.md`.
- PR #30 registers this goal and is ready for review. Its current head is
  `04cb5645be7c3182958248a62c22b0a9b9d055f6`; all required checks passed.
- PR #31 repairs the baseline dependency audit, passed two fresh local clean-room
  cycles and all required GitHub checks, and is ready for review.
- PR #32 adds the static single-L4 Terraform root and helpers. Head `d3cee0f` passed
  all four required jobs once on the PR event. Ten create/destroy fail-closed tests are
  committed locally through `ca3706b`; local verification passes, and CI awaits
  publication.
  Two helper review findings have regression tests and are fixed. Human review remains
  open.
- No AWS resources or GPU instance hours have been used by this goal.
- The account's applied On-Demand G and VT quota is zero. A 4-vCPU quota increase
  request was submitted on 2026-11-27 and AWS reports `CASE_OPENED` (pending); see the
  execution journal. Do not submit a duplicate.
- The existing repository budget and Terraform state guardrails use a repository-
  scoped bucket and lock table. GPU state must use a unique key namespace, not create
  duplicate guardrails. The budget uses email notifications. A recipient must be
  provided outside version control and verified before that alert is active; it is
  not an enforcement control.
- The initial USD $25 limit is a hard ceiling. A provisional planning scenario now
  includes compute, public IPv4, gp3, temporary state and lock storage, one expiry
  invocation, data-transfer allowance, tax contingency, and a reserve. It still
  requires exact AMI, price, egress, tax-profile, and state-retention confirmation;
  it is not permission to apply.

## Ordered implementation packages

### Package 0 — Goal charter and baseline gates

**Status:** PR #30 and PR #31 ready for review.

- [x] Register the persistent objective, scope, financial boundary, acceptance gates,
  initial source audit, and open AWS blocker.
- [x] Repair local/container package resolution for the known dependency audit.
- [x] Run local install, clean bootstrap, smoke, full CPU/local demo, tests, audit,
  container build, and project-scoped cleanup.
- [ ] Obtain review and merge through the PR workflow; do not push to `main` directly.

### Package 1 — Complete Phase 1 source and cost audit

**Status:** complete as a research/documentation gate; PR review remains open; no AWS mutation.

- [x] Inspect the gateway, identity, model catalog, Redis admission, CPU ONNX, vLLM
  adapter, Terraform roots, Compose, observability, model lifecycle, tests, CI, and
  historical validation records.
- [x] Record the vLLM token/stream accounting gaps and zero-quota/cost boundaries.
- [x] Review API request schemas, cancellation/error paths, Redis reservation expiry,
  tenant label cardinality, image/model pins, and existing EKS controls in source.
- [x] Research current official Docker, NVIDIA Container Toolkit, Ubuntu, DCGM,
  Prometheus, Grafana, OpenTelemetry, MLflow, Redis, model-license, and evaluation
  sources before implementation packages use them.
- [x] Prepare a provisional full resource/runtime cost model including state, expiry,
  egress, logging policy, and contingency; recheck rates and actual tax treatment
  immediately before any apply.
- [x] Finish the Phase 1 risk register, evidence manifest scheme, and independent
  shutdown/termination test design.

**Exit gate:** met for the Phase 1 design gate: audit and architecture explain what
exists, what is proposed, known failure gaps, and what the first bounded run must
validate. Exact runtime pins and refreshed cost inputs remain later apply gates. This
phase exit does not authorize payment.

### Package 2 — Isolated EC2 Terraform and expiry controls

**Status:** PR #32 is ready for review against PR #30; all four required jobs passed on
head `da2567e` in run `45933749318`. Billable resources remain prohibited until every
cost and quota gate passes.

- [x] Create a separate Terraform root with account, region, type, project-tag, and
  IMDSv2 guards. One `aws_instance` resource and a quota/resource preflight limit the
  first package to one GPU host.
- [x] Keep the resource set to a VPC, subnet, route/IGW, minimal security group,
  scoped IAM instance role/profile, one `g6.xlarge`, and encrypted gp3 storage.
- [x] Reuse the repository's private, versioned, encrypted S3 state bucket and
  pay-per-request DynamoDB lock table, with a unique `gpu-ec2/` state-key namespace.
  Add S3-native lock files if supported by the selected Terraform release, and test
  both locks together. Do not delete shared repository guardrails during GPU teardown
  or commit state or saved plans.
- [x] Prefer SSM with no inbound ports. Limit outbound access to TCP 80/443 for
  package/model retrieval; do not add NAT Gateway or endpoints without a demonstrated
  need and priced approval.
- [x] Add an independent EventBridge Scheduler one-time `ec2:TerminateInstances`
  call with an exact UTC deadline and instance/tag-scoped execution role; use a
  guest-side systemd shutdown timer as a second control. The schedule has no repeat
  rule and Terraform destroy removes it; the current pinned provider lacks an
  after-completion delete setting. EC2 guest shutdown must terminate; encrypted gp3
  storage must delete on termination.
- [x] Validate statically and prepare AWS-backed local-state previews: 7 bootstrap
  creates and 14 GPU-root creates. The previews are not remote-state or apply-ready
  plans. Keep plans outside Git.
- [x] Enforce the expected AWS account through the provider and fail an instance
  launch when the selected AZ does not offer the approved type.
- [x] Render and parse the cloud-init YAML; actual host behavior remains unverified.
- [ ] Create and inspect the final remote-state saved plan and confirm the full current
  cost and budget recipient. A 4-vCPU quota request is already open; track its outcome.
  Do not apply until the $25 project gate is cleared.

**Exit gate:** exact plan creates one authorized L4 and only enumerated project
resources, estimated total remains below $25 with safety margin, expiry is tested,
and teardown/absence commands are ready.

### Package 3 — Manual Linux, NVIDIA, CUDA, Docker, and Ansible

**Status:** not started.

- [ ] Select and pin a standard Ubuntu 24.04 x86_64 AMI, kernel, NVIDIA driver,
  CUDA Toolkit, Docker Engine, NVIDIA Container Toolkit, Python, and PyTorch after
  verifying the exact version matrix against the pinned vLLM build.
- [ ] Prepare scripts, packages, commands, output capture, and recovery steps before
  launching paid compute.
- [ ] Manually install the driver and run `nvidia-smi`, a CUDA container, and a
  synchronized PyTorch computation on the L4.
- [ ] Then implement Ansible roles/playbooks and run them twice to test idempotency.

**Exit gate:** real GPU and container computation passes, exact versions and raw
sanitized output are retained, and a repeated Ansible run makes no unintended changes.

### Package 4 — CUDA performance laboratory

**Status:** not started. Prepare source and validation locally before GPU runtime.

- [ ] Implement bounded CPU/GPU vector and matrix operations, copy/memory/precision/
  batch experiments, timing synchronization, and optional Triton/Nsight exercises.
- [ ] Record design, warm-up, repetitions, hardware/software context, raw values, and
  profiler availability before interpreting results.

**Exit gate:** measured GPU results and truthful limitations are documented; no
numbers are fabricated or inferred from CPU fixtures.

### Package 5 — Manual and containerized vLLM/Qwen serving

**Status:** not started. Exact model license/revision/digest and version tuple remain
open.

- [ ] Pin a dated vLLM release/image digest, compatible CUDA variant, Python ABI, and
  Qwen 1.5B model revision. Confirm artifact hash, license, memory, context, and
  tokenizer/template before downloading.
- [ ] Prepare the exact download, cache, launch, health/readiness, inference, streaming,
  telemetry, export, and teardown commands before the GPU batch.
- [ ] Start manually, verify real L4 inference and streaming, then reproduce with
  Docker Compose without publishing the endpoint or internal services.

**Exit gate:** actual model output is attributable to the L4 and versioned artifacts;
startup, readiness, streaming, and clean shutdown are proven.

### Package 6 — Multi-tenant GPU gateway integration

**Status:** not started; requires token accounting and lease design first.

- [ ] Test and fix OpenAI-compatible schemas, measured TTFT, final streaming usage,
  tokenizer-based reservation, actual-usage reconciliation, cancellation/error
  outcomes, Redis failure, and crash-safe concurrency lease recovery.
- [ ] Preserve ONNX defaults and add vLLM as a separately configured runtime target.
- [ ] Demonstrate support, engineering, and research tenants with shared quotas,
  model grants, bounded queueing, and noisy-neighbor controls.

**Exit gate:** real gateway-routed GPU calls, policy denials, shared state, failure
cleanup, and CPU ONNX regression all have evidence.

### Package 7 — Metrics, traces, dashboards, and alerting

**Status:** not started. First identify actual metric names and exporter versions.

- [ ] Integrate DCGM Exporter, Node Exporter, vLLM/Gateway/Redis metrics, Prometheus,
  Grafana, Alertmanager, OpenTelemetry, and Tempo only where they fit the host and
  budget.
- [ ] Set alert thresholds from measured behavior; do not publish prompts, completions,
  credentials, or raw tenant identifiers in telemetry.

**Exit gate:** live workload data and one controlled alert/trace correlation are
captured and described with units and limits.

### Package 8 — Benchmarking, FinOps, evaluation, release, and rollback

**Status:** not started; prepare data and scripts before paid execution.

- [ ] Implement controlled vLLM and local benchmark drivers with valid context/output
  combinations, concurrency ramp, warmups, repetitions, and raw result retention.
- [ ] Run representative workload/precision/concurrency experiments inside the
  authorized GPU runtime window; compute full request and million-token cost.
- [ ] Prepare versioned synthetic evaluations and deterministic quality/format gates.
- [ ] Demonstrate sequential candidate approval, rejection, known-good reload, and
  verified rollback on the single L4.

**Exit gate:** actual run metadata, raw data, charts, evaluation decisions, cost formula,
and rollback evidence exist and fit the budget.

### Package 9 — Controlled incident drills and recovery

**Status:** not started. Prepare reversible drills, commands, and recovery steps first.

- [ ] Cover representative GPU/container/model/admission/monitoring failures without
  destructive host changes.
- [ ] Capture real logs, telemetry, detection, root-cause alternatives, recovery time,
  verification, and prevention for every drill.

**Exit gate:** reports prove real failure and independent recovery; no simulated error
is presented as an executed incident.

### Package 10 — Automation, clean-room reproduction, and teardown

**Status:** not started.

- [ ] Complete Makefile/Ansible/Compose/CI automation; normal PR CI must never launch
  paid AWS jobs.
- [ ] Recreate from clean project state using only documented commands; capture exact
  stack outputs and evidence.
- [ ] Export sanitized evidence and charts before teardown. Destroy only the authorized
  GPU root, verify provider-side absence, and retain only documented state/evidence
  with known cost.
- [ ] Complete the report, manual reproduction guide, handbook, interview guide,
  incident handbook, cost report, and searchable downloadable documents after real
  execution results are available.

**Exit gate:** clean-room recreation, immediate teardown, independent absence checks,
cost status, educational artifacts, and goal closure are complete.

## Spending and authorization gates

- The hard initial budget is $25 total; the total run plan must remain below it with a
  margin. Instance-only cost is not the project estimate.
- No GPU runs while writing, reviewing, researching, waiting for CI, or generating
  reports. Bundle all GPU-required experiments into short authorized batches.
- Keep cumulative instance runtime within the planned 8–12 hour target where feasible;
  record start/stop times and estimates per batch.
- Terminate the instance and remove unnecessary supporting resources after every
  batch. Never rely on AWS Budget alerts as an enforcement mechanism.
- If the complete mandatory work cannot be done under $25, stop paid work, document
  remaining requirements, finish non-billable work, and ask before increasing the
  ceiling or changing the design.
- The applied G/VT On-Demand quota is currently zero. A user-requested 4-vCPU quota
  increase is open with AWS; do not submit another request and do not launch until AWS
  approves it and the exact bounded cost/resource plan and apply gates pass.
- Provisional 12-hour estimate: about `$10.68` before tax for one g6.xlarge, one public
  IPv4, 100 GiB gp3, short-lived S3 state and lock objects, one scheduler invocation,
  and 1 GiB of internet egress. A 25% tax allowance plus `$5` general reserve gives
  about `$18.35`. This is neither a provider quote nor authorization. Confirm current
  rates, the account tax profile, aggregate data-transfer usage, state retention, and
  exact plan immediately before any paid run.
