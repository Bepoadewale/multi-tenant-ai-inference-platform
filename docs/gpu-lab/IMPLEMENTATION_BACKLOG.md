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
- PR #37 is open against PR #36 to record the dated Ubuntu/NVIDIA/CUDA, vLLM image,
  and pinned Qwen model compatibility candidates. PRs #38–#51 are stacked one at a
  time through PR #50. PR #54 passed all five checks in run `46028053505`. This is
  research and static CI evidence, not proof of GPU execution; exact target-AMI
  packages and real L4 validation remain open.
- PR #38 is open as a focused model-artifact verification helper based on PR #37.
  Head `5256060` records the verifier, fixture tests, and Terraform validation; its
  head passed all four required checks in run `45946331836`. Fixture tests do not
  replace checking the actual downloaded artifact.
- PR #39 is open against PR #38 to record the quota denial, regional quota checks,
  and an unsent appeal draft. Its head `7605b0b` passed all four required checks in
  run `45947503606`. It does not submit an AWS message or quota request.
- PR #40 is open against PR #39 to pin the reviewed Canonical Ubuntu AMI
  and fail closed when publisher, image family, architecture, or availability does
  not match. All four required checks passed in the implementation run
  `45949421928` and documentation follow-up runs `45950217355` and `45951027403`.
  No AWS resource or GPU run is part of this package.
- PR #41 records the owner's authorized CLI appeal attempt. The Support API rejected
  the communication before sending due to the current account plan; no case update
  occurred. All four required checks passed in run `45976696129`.
- A refreshed AWS-backed local-state preview uses the exact pinned AMI. It proposes 14
  creates, including one `g6.xlarge`, IMDSv2, and an encrypted 100-GiB root volume.
  It is not remote-state locked and must not be applied. Ticket42 records its digest
  and security review; the remote-state plan remains outstanding.
- No AWS resources or GPU instance hours have been used by this goal.
- The applied On-Demand G and VT quota is zero in `us-east-1`, `us-east-2`, and
  `us-west-2`. AWS email reports that the 4-vCPU `us-east-1` request was denied, while
  Service Quotas history still returns `CASE_OPENED`. The owner reports appealing
  through the existing case; see `QUOTA_APPEAL_DRAFT.md`. Do not duplicate the request
  or launch while quota is zero.
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
- PRs #32–#53 are open and unmerged. PR #52 follow-up head `1f02955` passed run
  `46021471851`. PR #53 tested code head `e623b75` passed all five required checks in
  run `46023306230`, including a Linux amd64 Docker image build and CPU end-to-end.
  A documentation-only PR #53 follow-up awaits checks. No AWS resources or GPU
  execution.

## Ordered implementation packages

### Cross-cutting package — repeatable gateway image inputs

**Status:** PR #53 adds a pinned Python base-image digest and 124-package
hash-locked runtime requirements. Local lock coverage passes; Linux amd64 image build
and CPU end-to-end validation passed in CI run `46023306230`. The Python 3.12 CUDA
learning lock and pinned vLLM image remain separate.

- [x] Pin the multi-platform official Python slim Bookworm base image by OCI index
  digest.
- [x] Generate universal runtime dependency hashes and require them during image
  installation.
- [x] Add a CI/local lock coverage check.
- [x] Confirm the Docker image builds on Linux amd64 and local CPU flows remain healthy.

**Exit gate:** CI builds the shared gateway image from the pinned base and hash-locked
Python dependencies.

**Evidence:** PR #53 run `46023306230` passed all five required jobs. The Linux amd64
image build, dependency audit, and existing CPU local end-to-end flow passed.

### Package — immutable single-L4 LLM release records

**Status:** PR #54 adds local manifest/plan digest validation, stale-input protection,
and independent-approver state in SQLite. PR #55 adds the authenticated plan and
approval API, MLflow evaluation checks, and shared single-host manifest storage; all
five checks passed on latest head `de4c6e7` in run `46034523863`. PR #56 prepares a
host-only deployment controller and currently has 15 focused local tests passing.
The PR #55 and #56 changes remain open and unmerged; PR #56 full validation and CI
are pending.

- [x] Bind full model revision, artifact digest, license, serving image/configuration,
  evaluation suite/report digests, and source commit.
- [x] Reject deterministic failures, unpinned image tags, multi-GPU configuration,
  tampered manifests/plans, stale manifests, and self-approval.
- [x] Connect plan approval and request identity to existing signed role dependencies.
- [x] Link the candidate to a finished MLflow run, sanitized report, and declared
  model/runtime/source provenance.
- [x] Implement local checks for active champion state, running container image,
  command, model-cache mount, readiness, and full model snapshot digest.
- [x] Implement the host-only sequential restart, private transaction journal, and
  simulated success/failure rollback tests.
- [ ] Complete full repository validation and CI for the controller package.
- [ ] Verify active champion, model bytes, sequential restart, inference, rollback,
  and interrupted-transaction recovery on the authorized L4 host.

**Exit gate:** an authenticated independent approval binds to the exact candidate and
runtime; the host controller verifies live state and model bytes, then deploys, checks
real gateway inference, or restores the known-good model on one L4. Local fake tests
do not satisfy the live exit gate.

### Package — authenticated LLM release planning and approval API

**Status:** [PR #55](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/55)
is open; focused tests and full `make verify` pass. All five required CI jobs passed
on head `b94fc27` in run `46033196309`. No AWS or GPU operation is involved.

- [x] Require `platform.admin` to create/read plans and `release.approve` to approve.
- [x] Reject a candidate unless its finished MLflow run and sanitized report match the
  model ID/revision, source commit, declared artifact digest, immutable serving image,
  runtime configuration, evaluation suite, and deterministic gate.
- [x] Persist the plan and both manifests in a shared SQLite volume for the two gateway
  containers on one host; enable WAL and a bounded busy wait.
- [x] Keep the API unable to access Docker or restart vLLM.
- [ ] Add host-side verification of current live champion and model file digests.
- [ ] Implement sequential deployment, readiness checks, and rollback.

**Limit:** the champion and model artifact digest are still caller-supplied. This API
records and checks them against evaluation metadata; it does not prove running state or
model bytes. The SQLite volume is single-host storage, not a distributed or highly
available database.

**Evidence:** see `docs/tickets/ticket55.md` and the updated evidence manifest.

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
- [x] Pin the exact Canonical Ubuntu 24.04 amd64 AMI and reject an untrusted or
  unavailable image before plan/apply; keep destroy planning independent of AMI lookup.
- [x] Refresh and inspect a pinned-AMI local-state preview. Its plan contains 14
  creates for one `g6.xlarge`; it is ignored locally and is not suitable for apply.
- [ ] Create and inspect the final remote-state saved plan and confirm the full current
  cost and budget recipient. The existing quota request was denied by email, remains
  `CASE_OPENED` in the API, and applied quota is zero. Do not apply until the quota and
  $25 project gates are cleared.

**Exit gate:** exact plan creates one authorized L4 and only enumerated project
resources, estimated total remains below $25 with safety margin, expiry is tested,
and teardown/absence commands are ready.

### Package 3 — Manual Linux, NVIDIA, CUDA, Docker, and Ansible

**Status:** PR #50 contains a non-billable ordered install manifest and hashed PyTorch lock. Its current restacked head passes all five required jobs. No GPU host has been configured; candidate versions are not runtime-verified.

- [ ] Select and pin a standard Ubuntu 24.04 x86_64 AMI, kernel, NVIDIA driver,
  CUDA Toolkit, Docker Engine, NVIDIA Container Toolkit, Python, and PyTorch after
  verifying the exact version matrix against the pinned vLLM build.
- [x] Record ordered host/container components, candidate versions, verification
  points, stop conditions, and items deliberately kept off the host in
  `GPU_HOST_INSTALL_MANIFEST.md`.
- [x] Resolve and hash-lock the standalone PyTorch 2.14.0 CUDA 13.0 dependencies for
  CPython 3.12 / Linux x86_64; keep the install separate from the vLLM image.
- [ ] Recheck signed package indexes and exact package versions against the pinned AMI
  and live Ubuntu kernel before launch; retain the reviewed package metadata.
- [ ] Prepare scripts, packages, commands, output capture, and recovery steps before
  launching paid compute.
- [ ] Manually install the driver and run `nvidia-smi`, a CUDA container, and a
  synchronized PyTorch computation on the L4.
- [ ] Then implement Ansible roles/playbooks and run them twice to test idempotency.
- [x] Add a private MLflow tracking service to the dedicated GPU Compose profile and
  publish only sanitized evaluation metadata/reports to it. PR #52 implements the
  static/local path; the optional operator UI/API port binds only to loopback. Live
  artifact upload on the L4 remains unverified.

**Exit gate:** real GPU and container computation passes, exact versions and raw
sanitized output are retained, and a repeated Ansible run makes no unintended changes.

### Package 4 — CUDA performance laboratory

**Status:** PR #49 (`codex/gpu-cuda-lab-preparation`) is open. Its current restacked
head passes all five required jobs. The bounded CUDA C++ vector-add and synchronized
PyTorch matrix/transfer lab is static preparation. No kernel has been compiled and no
real measurements exist.

- [x] Prepare bounded CPU/GPU vector and matrix operations, separate host/device
  copies, supported precision checks, and warmup/repeat controls.
- [x] Use CUDA events plus explicit synchronization for GPU timings; test the dry-run
  without importing PyTorch or touching a GPU.
- [ ] Prepare optional Triton/Nsight exercises after runtime compatibility and tool
  availability are confirmed.
- [ ] Compile and execute the experiments on the real single L4.
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
- [ ] Before that batch, use the local verifier from ticket #38 to check the pinned
  Qwen `model.safetensors` after download; fixture tests are not artifact evidence.
- [ ] Start manually, verify real L4 inference and streaming, then reproduce with
  Docker Compose without publishing the endpoint or internal services.

**Exit gate:** actual model output is attributable to the L4 and versioned artifacts;
startup, readiness, streaming, and clean shutdown are proven.

### Package 6 — Multi-tenant GPU gateway integration

**Status:** non-billable gateway correctness work is in progress across PRs #33–#35.
PR #33 covers stream usage/error accounting; PR #34 covers shared reservations and
Redis lease recovery; PR #35 adds model-aware token bounds and admission renewal during
tokenizer preflight. None has live GPU inference evidence.

- [x] Cover final streaming usage, in-band errors, gateway estimates, and local
  cancellation/error accounting (mock/local backends only).
- [x] Add shared request reservations, measured usage reconciliation, idempotent
  release, crash-expiring leases, renewal deadlines, and stale metadata cleanup; test
  Redis scripts against a local Redis 7.4 service.
- [x] Add tokenizer-based reservation and model context bounds; renew the admission
  lease during slow tokenizer preflight and release it on rejection.
- [x] Add local failure-path coverage for preflight cancellation, unavailable Redis
  admission, and bounded tokenizer HTTP timeout.
- [ ] Test Redis failure and cancellation across separate gateway processes.
- [ ] Verify the stream/admission contract against the pinned live vLLM runtime and
  route real GPU-backed requests.
- [ ] Preserve ONNX defaults and add vLLM as a separately configured runtime target.
- [ ] Demonstrate support, engineering, and research tenants with shared quotas,
  model grants, bounded queueing, and noisy-neighbor controls.

**Exit gate:** real gateway-routed GPU calls, policy denials, shared state, failure
cleanup, and CPU ONNX regression all have evidence.

### Package 7 — Metrics, traces, dashboards, and alerting

**Status:** PR #46's rebased static configuration passed all five required checks in
run `45992409372`; live L4 validation remains outstanding.

- [x] Prepare pinned single-host exporters, vLLM/Gateway/Redis scrapes, Prometheus,
  Grafana, Alertmanager, profile-specific OpenTelemetry with sensitive-attribute
  deletion, and Tempo configuration. Pinned config-validator images were pulled
  locally; no profile service or GPU image was started.
- [ ] Validate exporter/device access, every metric name and unit, rule expressions,
  dashboard panels, and trace propagation against the real L4 batch.
- [ ] Set alert thresholds from measured behavior; do not publish prompts, completions,
  credentials, or raw tenant identifiers in telemetry.

**Exit gate:** live workload data and one controlled alert/trace correlation are
captured and described with units and limits.

### Package 8 — Benchmarking, FinOps, evaluation, release, and rollback

**Status:** PRs #47–#52 prepare static benchmarking, evaluation, private MLflow evidence, and sequential-release design. PR #52 head `55f4d59` passed all five checks in run `46020258170`. Gateway benchmarking, actual GPU performance, live model evaluation, and release/rollback behavior remain outstanding.

The current ONNX release API does not support the one-target vLLM profile. The
The existing ONNX release API still does not support the one-target vLLM profile. PR
#52 adds a private MLflow tracking service and evaluator report publication, while PR
#51 documents the separate sequential LLM release path. No candidate has been
registered or deployed. Immutable release plans and approval enforcement remain open.

- [x] Prepare the official `vllm bench serve` runner, context-bounded synthetic
  workloads, gated high concurrency, repeated aggregates, and hardware/software
  metadata capture. Static dry-run only; no inference request was sent.
- [ ] Prepare an authenticated gateway benchmark that reports gateway overhead,
  multi-tenant admission behavior, cancellation, and queueing without logging tokens
  or prompt/response content.
- [ ] Run representative workload/precision/concurrency experiments inside the
  authorized GPU runtime window; compute full request and million-token cost.
- [x] Prepare versioned synthetic tasks with deterministic quality/format gates and
  a human-review marker for subjective summarization. The runner's dry-run makes no
  network requests; no LLM has been evaluated yet.
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
- The applied G/VT On-Demand quota is zero in three checked regions. The first
  4-vCPU request was denied by email, though the API history remains `CASE_OPENED`.
  The owner reports an appeal through the existing Support Center case. Wait for
  AWS's response; do not send a duplicate appeal or launch with zero applied quota.
- Provisional 12-hour estimate: about `$10.68` before tax for one g6.xlarge, one public
  IPv4, 100 GiB gp3, short-lived S3 state and lock objects, one scheduler invocation,
  and 1 GiB of internet egress. A 25% tax allowance plus `$5` general reserve gives
  about `$18.35`. This is neither a provider quote nor authorization. Confirm current
  rates, the account tax profile, aggregate data-transfer usage, state retention, and
  exact plan immediately before any paid run.
