# Single-L4 GPU Lab Implementation Backlog

This is the ordered work plan for the single-L4 goal. It is a working backlog, not a
claim that any cloud or GPU phase has run. Every package uses its own focused branch
and pull request. Review and required CI checks must pass before merge; implementation
pull requests must include the repository's clean-room evidence.

**Current readiness update (2026-11-28):** the existing request is `CASE_CLOSED` and
4.0 On-Demand G/VT vCPUs are applied in `us-east-1`. This clears the quota threshold
for one `g6.xlarge`; it does not authorize provisioning. The project state bucket,
lock table, and Budget are absent, and the alert recipient is not verified. Exact
remote-state plan, updated price/AZ-capacity review, independent expiry check, and
separate apply authorization remain required. The user-set $25 total ceiling remains.
Old quota-denial statements below are dated historical snapshots, not current state.

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
- Historical quota snapshots below this note preceded the appeal decision. On
  2026-11-28, read-only `us-east-1` checks show `CASE_CLOSED` and 4.0 applied On-Demand
  G/VT vCPUs. That is sufficient by quota for one `g6.xlarge`; no AZ reservation is
  implied and no duplicate request should be sent.
- Terraform bootstrap code defines a repository-scoped budget and state/lock resources,
  but the exact project Budget, state bucket, and lock table are currently absent. GPU
  state should use a unique key namespace once the backend is authorized. The budget
  alert recipient must be provided outside version control and verified; the alert is
  not a spending limit.
- The initial USD $25 limit is a hard ceiling. A provisional planning scenario now
  includes compute, public IPv4, gp3, temporary state and lock storage, one expiry
  invocation, data-transfer allowance, tax contingency, and a reserve. It still
  requires exact AMI, price, egress, tax-profile, and state-retention confirmation;
  it is not permission to apply.
- PRs #30–#61 remain open and unmerged; merge authorization is outstanding. PR #59
  and #60 were rebased onto current PR #58 head `59925fd`; #60 head `9a8bd28` has
  fresh CI running after eight focused tests and Ruff passed locally. PR #61's
  interview guide was rebased onto #60 head `9a8bd28`; fresh CI is required. Earlier
  passing CI on the old stack is not evidence for these updated heads. PR #53
  code head `e623b75` passed all five checks in `46023306230`, including a Linux AMD64
  gateway image build and CPU end-to-end. PR #56 head `852c873` passed all five checks
  in `46040861818`; PR #57 Ansible head `4795f12` passed all six checks, including a
  clean-room local end-to-end cycle, in `46045068200`. Neither host configuration nor
  AWS deployment has run.
- PR #58 adds named tenant identities and the manual guide. Run `46052092657` passed
  the checksum-verified Trivy scan and identified that owner-only token permissions
  prevented the local edge agents from registering. Commit `d759b8e` fixed the local
  container UID/GID and passed all six checks in run `46054114999`, including a fresh
  local end-to-end cycle. Commit `a1616ec` resolves three automated guide findings
  about exact Terraform variables, the manual vLLM handoff, and workstation teardown.
  Its final-head run `46055428111` passed all six jobs. No AWS resource, model, or GPU
  execution occurred.

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
host-only deployment controller and has 16 focused local tests passing; updated head
`852c873` passed all five checks in `46040861818`.
PR #55 remains open and unmerged. [PR #56](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/56)
is open as a draft, stacked on PR #55. Initial head `ad10699` passed all five required
checks in run `46039778508`, including one clean-room local end-to-end cycle. The
current type-safety follow-up passed full local validation; its checks are pending.

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
- [x] Complete full repository validation for the controller package: `make verify`
  passes Ruff, 144 tests (2 skipped), audit, Compose/monitoring validation, and
  benchmark/evaluation/CUDA dry runs.
- [x] Complete one CI clean-room cycle on the first validated controller head.
- [ ] Rerun required CI after a material tensor-parallel type-safety fix.
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
  cost and budget recipient. The quota is now approved at 4.0 vCPUs, but do not apply
  until the remote state, recipient/Budget, $25 total cost, exact plan, expiry, and
  separate authorization gates are cleared.

**Exit gate:** exact plan creates one authorized L4 and only enumerated project
resources, estimated total remains below $25 with safety margin, expiry is tested,
and teardown/absence commands are ready.

### Package 3 — Manual Linux, NVIDIA, CUDA, Docker, and Ansible

**Status:** PR #50 contains a non-billable ordered install manifest and hashed PyTorch lock. PR #57 adds a universal hash-locked Ansible 2.21.6 controller and local-host role for the dated Ubuntu/NVIDIA/CUDA/Docker candidate set. Its six checks, including one clean-room local run, passed on head `4795f12` in `46045068200`; PR #57 is ready for review. No GPU host has been configured; candidates are not runtime-verified.

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
- [x] Prepare the Ansible role, signed-repository configuration, version pins, and
  CI syntax check before the GPU session. Do not run it until the manual learning pass.
- [ ] Run the playbook twice on the approved host and verify the second run has no
  configuration changes.
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

**Status:** statically prepared in PR #45 and research/runbook updates through PRs
#47/#50/#57. The current candidate is vLLM 0.34.0 at its reviewed image digest,
Qwen2.5-1.5B-Instruct at a pinned revision, Ubuntu 24.04 amd64, an R580 host-driver
candidate, and CUDA 13.0/13.0.3 candidates. The manual guide now uses one named model
cache volume for the first vLLM launch and later Compose service. This matrix still
requires live package/license/artifact/runtime verification before use.

- [x] Research the dated vLLM image, model revision/license, candidate CUDA/driver
  versions, model/cache workflow, and host/runtime health checks.
- [x] Prepare manual and Compose commands for download, cache, launch,
  health/readiness, inference, streaming, and teardown in the manual guide and GPU
  batch runbook. Commands are prospective, not executed.
- [ ] Before the GPU batch, refresh the image digest and model license/revision,
  confirm architecture and API compatibility, verify actual downloaded snapshot
  digest, and check memory/context requirements against the L4.
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
- [x] Run `make demo-gateway-cancellation` through the local flagship flow. CI run
  `46066808334` cancelled ten streams across both CPU gateway processes and verified
  each active gauge and the shared Redis lease hash returned to zero.
- [ ] Rerun `make demo-redis-outage` after the shared rollout-store fix. In CI run
  `46066808334`, the first replica returned HTTP 500 instead of the expected 503;
  `INCIDENT-LOCAL-REDIS-001.md` records the failure. The exit trap restarted Redis,
  but gateway readiness after recovery was not tested because the assertion failed.
  The local fix and focused tests are ready for the next PR workflow.
- [ ] Verify the stream/admission contract against the pinned live vLLM runtime and
  route real GPU-backed requests.
- [x] Preserve ONNX defaults and add vLLM as a separately configured single-target
  runtime in the isolated Compose profile; GPU catalog and CPU-default regression
  tests exist in PR #45.
- [x] Prepare customer-support, internal-engineering, and research catalog profiles
  with different model grants, request/token limits, and concurrency, plus signed
  identity fixtures. Ticket #58 tests application authentication; no physical GPU
  isolation is claimed.
- [ ] Demonstrate the named tenants against real vLLM through both gateway replicas,
  verify shared Redis accounting, model denials, overload, and failure cleanup on the
  approved L4 host.

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

**Status:** PRs #47–#52 prepare static benchmarking, evaluation, private MLflow evidence, and sequential-release design. PR #52 head `55f4d59` passed all five checks in run `46020258170`. PR #60 adds an authenticated gateway benchmark with privacy-safe metadata and a strict L4 guard. Current rebased head `9a8bd28` passed focused tests locally and its fresh six-job CI is running. Actual GPU performance, live model evaluation, and release/rollback behavior remain outstanding.

The existing ONNX release API still does not support the one-target vLLM profile. PR
#52 adds a private MLflow tracking service and evaluator report publication, while PR
#51 documents the separate sequential LLM release path. No candidate has been
registered or deployed. Immutable release plans and approval enforcement remain open.

- [x] Prepare the official `vllm bench serve` runner, context-bounded synthetic
  workloads, gated high concurrency, repeated aggregates, and hardware/software
  metadata capture. Static dry-run only; no inference request was sent.
- [x] Prepare an authenticated gateway benchmark that reports direct-versus-gateway
  latency, multi-tenant admission status, client-side queue wait, and bounded requests
  without logging tokens or prompt/response content. Cancellation remains covered by
  the separate gateway cancellation drill. Static and mock-transport checks only;
  actual GPU measurement is outstanding.
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
- Historical snapshot: the applied quota was zero in the checked regions before the
  appeal was resolved. The current `us-east-1` result is 4.0 applied vCPUs and
  `CASE_CLOSED`; no duplicate request is needed. The quota does not bypass the
  remaining budget, backend, exact-plan, expiry, capacity, and apply gates.
- Provisional 12-hour estimate: about `$10.68` before tax for one g6.xlarge, one public
  IPv4, 100 GiB gp3, short-lived S3 state and lock objects, one scheduler invocation,
  and 1 GiB of internet egress. A 25% tax allowance plus `$5` general reserve gives
  about `$18.35`. This is neither a provider quote nor authorization. Confirm current
  rates, the account tax profile, aggregate data-transfer usage, state retention, and
  exact plan immediately before any paid run.
