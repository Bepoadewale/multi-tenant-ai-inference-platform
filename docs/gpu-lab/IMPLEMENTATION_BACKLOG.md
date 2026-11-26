# Single-L4 GPU Lab Implementation Backlog

This is the ordered work plan for the single-L4 goal. It is a working backlog, not a
claim that any cloud or GPU phase has run. Every package uses its own focused branch
and pull request. Review and required CI checks must pass before merge; implementation
pull requests must include the repository's clean-room evidence.

## Current state

- Phase 1 design gate is complete. The repository audit and candidate architecture are recorded in
  `REPOSITORY_AUDIT.md`, `ARCHITECTURE.md`, and `RESEARCH_NOTES.md`.
- PR #30 registers this goal and is ready for review. All required checks passed for
  head `336c1b468cf1ac9e0505ffc95a7e8bb10d8a86b6` on 2026-11-26.
- PR #31 repairs the baseline dependency audit, passed two fresh local clean-room
  cycles and all required GitHub checks, and is ready for review.
- No AWS resources or GPU instance hours have been used by this goal.
- The account's On-Demand G and VT quota is zero. No quota increase request has been
  submitted.
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

**Status:** static design/implementation in progress; billable resources prohibited
until every cost and quota gate is satisfied.

- [ ] Create a separate Terraform root with strict account, region, instance-type,
  instance-count, project-tag, and IMDSv2 guards.
- [ ] Keep the resource set to a VPC, subnet, route/IGW, minimal security group,
  scoped IAM instance role/profile, one `g6.xlarge`, and encrypted gp3 storage.
- [ ] Use a private, versioned, encrypted S3 state bucket and native Terraform S3 lock
  file; define bootstrap and final state-bucket teardown without committing state or
  saved plans.
- [ ] Prefer SSM with no inbound ports. Add only outbound access required for package
  and model downloads; do not add NAT Gateway or endpoints without a demonstrated
  need and priced approval.
- [ ] Add an independent EventBridge Scheduler one-time `ec2:TerminateInstances`
  call with an exact UTC deadline and instance/tag-scoped execution role; use a
  guest-side systemd shutdown timer as a second control. Configure automatic schedule
  deletion after invocation and test retry, missed invocation, reboot, and already-
  terminated-instance behavior. EC2 guest shutdown must terminate; encrypted gp3
  storage must delete on termination.
- [ ] Validate and plan statically first. Prepare a single saved plan and human-readable
  resource/cost review. Do not apply until the quota and exact cost gate are cleared.

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
- The G/VT On-Demand quota is currently zero. Do not request an increase or launch
  until the exact bounded cost and resource plan is ready and the account change is
  authorized.
- Provisional 12-hour estimate: about `$10.67` before tax for one g6.xlarge, one public
  IPv4, 100 GiB gp3, short-lived S3 state and lock objects, one scheduler invocation,
  and 1 GiB of internet egress. A 25% tax allowance plus `$5` general reserve gives
  about `$18.34`. This is neither a provider quote nor authorization. Confirm current
  rates, the account tax profile, aggregate data-transfer usage, state retention, and
  exact plan immediately before any paid run.
