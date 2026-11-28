# Single-L4 GPU Lab Implementation Backlog

This is the ordered work plan for the single-L4 goal. It is a working backlog, not a
claim that any cloud or GPU phase has run. Every package uses its own focused branch
and pull request. Review and required CI checks must pass before merge; implementation
pull requests must include the repository's clean-room evidence.

## Latest PR and engineering status — 2026-11-28 18:09 UTC

PRs #77–#83 passed all six required checks on their refreshed heads, including the
local CPU end-to-end job. PR #84 head `f2963db` passed all six jobs, including
local-e2e, in run `46173687147` after current-quota and clean-room-record corrections.
Its local validation passed 67 focused tests, 12 mocked Terraform cases, Ruff, the
35-file docs checker, and `git diff --check`. The single designated local clean-room run remains the one recorded
in `docs/governance/VALIDATION.md`; no repeat is planned. PR #43 and #53 are now
reported mergeable in the current open-PR inventory, but still require owner review.
The project Budget/verified recipient, remote state and lock, final plan/cost,
capacity, expiry verification, and separate apply authorization remain open.

## Read-only AWS gate snapshot — 2026-11-28 15:06 UTC

**Read-only refresh:** the expected AWS account matched. Applied On-Demand G/VT quota
is `4.0` vCPUs, enough numerically for one `g6.xlarge`; request history now
reports `CASE_CLOSED` with desired value 4.0. Five us-east-1 AZ offerings were listed;
none reserves live capacity. The exact project state bucket, lock table, project Budget,
project-tagged resources, and project EC2 instances are absent. A different account
Budget was listed, but its project coverage is unverified and it is not relied upon.
The current `$0.8048/hour` price matches the `$18.5193` 12-hour planning envelope. A
guarded preflight stopped at the absent state bucket. No Billing alternate contact or
verified private alert recipient is configured. No paid apply is ready or authorized.

At capture time, this section was the handoff. Detailed package notes below are dated historical
records; use the goal, implementation status, tickets, and live GitHub records for newer
state. The owner wants every feasible code, automation, local/static validation,
documentation, and CI task finished before the paid GPU batch. Only real-L4 execution
and its immediate live safety gates should remain at that point. The one designated local
CPU clean-room run passed and is recorded in `docs/governance/VALIDATION.md`; no further
manual local clean-room run is planned. The cloud/GPU clean-room remains Phase 12 work.

- The latest GitHub inventory found **54 open PRs** from #30–#84 except #54; none is
  a draft or has an approving review. PRs #43 and #53 conflict after parent updates;
  the other 52 are mergeable. PR #42, #52, and #84 current heads pass CI. No PR was
  merged by this work. PRs #46 and #55 are ready for review after
  their clean-room evidence threads were answered and resolved using the integrated
  record in `docs/governance/VALIDATION.md`. PR #65 is ready for owner review after
  its P1 evidence thread was resolved and all six checks passed on head `24ea5e8` in
  run `46117285643`. PR #72 head `ef1f5e3` passed all six checks in run
  `46124118809`; PR #73 head `b50c5a9` passed all six checks in run `46126117628`.
  PR #74 head `944b457` passed all six checks in run `46128237140`; PR #75 head
  `a7c6ccd` passed all six checks in run `46129784597`; PR #76 head `dba21f1` passed
  all six checks in run `46132280041`; PR #77 final head `387b91c` passed all six
  checks in run `46134599825`; PR #78 implementation head `5c3bd12` passed all six
  checks in run `46135887060`. All remain open and unmerged for owner review.
- PR #76 (`codex/gpu-documentation-link-checks`) adds a standard-library Markdown
  link and heading checker to local verification and manifests CI. It is stacked on
  PR #75.
- PR #77 (`codex/gpu-expiry-safeguard-tests`) adds mocked-provider Terraform tests
  for bounded expiry and least-privilege termination. Its three tests, full local
  verification, and Terraform validation pass; implementation head `75f91e3` passed
  all six required CI jobs in run `46133957636`. It is stacked on PR #76.
- PR #78 (`codex/gpu-network-guardrail-tests`) adds mocked-provider checks for no
  inbound security-group rules, TCP 80/443-only egress, and the instance's single
  project security group. All four Terraform tests and full local verification pass;
  implementation head `5c3bd12` passed all six required jobs in `46135887060`. Its
  later documentation head `6aeb638` had one HTTP 500 in local E2E; rerunning that job
  passed all six checks in `46136477854`. The first failure's cause is unknown. It is
  stacked on PR #77.
- PR #79 (`codex/gpu-project-tag-guardrails`) makes ownership, expiry, cost-scope,
  and data-class tags explicit on every GPU-root resource type where the pinned
  provider exposes tags. Its mock test checks 11 taggable resources; individual
  Scheduler schedules have no `tags` argument in this provider schema, so the schedule
  group is tagged and the schedule retains its exact project-specific name. Local
  formatting, validation, and all five mocked Terraform assertions pass. Implementation
  head `2e92165` passed all six required jobs in run `46137645356`; final documentation
  head `efe7eed` passed all six in `46138350722`. No AWS/GPU behavior is implied.
- PR #80 (`codex/gpu-input-constraint-tests`) adds negative plan tests for
  the initial single-`g6.xlarge` restriction, the disallowed `g5` family, storage bounds,
  region/project pins, and malformed AMI IDs. All 12 GPU-root mocked Terraform tests
  pass locally. The first region test also violated the availability-zone validation;
  it now isolates the region input. Ticket, docs index, and CI link-checker updates are
  prepared. Final documentation head `6145e25` passed all six required jobs in run
  `46139713692`. No AWS/GPU behavior is implied.
- PR #81 is open on top of #80 at final head `3cb8139`; all six required jobs passed
  in run `46142107889`. Its validator reviews the exact saved plan,
  checks all 14 expected managed resources and critical instance/network/tag/expiry
  settings, prints only a sanitized summary, and repeats validation before apply.
  Fake-CLI coverage ensures an unsafe saved plan never reaches Terraform apply. The
  33 focused tests and 12 GPU-root Terraform mocks pass locally. It does not replace
  human review of the full plan or the separate cloud authorization gates.
- PR #82 is open on top of #81 at final head `d5afac7`; all six required checks passed
  in run `46143890538`. It checks the project expiry schedule group and EC2 terminate
  action. Its focused plan and wrapper suite passes 35 tests. This is fixture evidence,
  not proof of an actual schedule execution.
- PR #83 is open on top of #82 at final head `4c75115`; all six required CI jobs
  passed in run `46146275508`. It uses Terraform's saved-plan configuration
  expressions to require the expiry schedule role and input, and the IAM policy's
  role and resource, to reference this exact project instance. Twenty-four focused
  validator tests and 39 combined plan/wrapper tests pass locally. Its initial CI run
  `46145456879` caught a stale fake plan in the wrapper suite; the corrected head
  passed all six jobs. A real AWS-provider plan is still required to confirm the
  expression shape. No AWS resource or GPU execution occurred.
- PR #84 is open on top of refreshed #83 head `142d0f3`; restacked head `798b2e8`
  passed all six required CI jobs in run `46171879043`. It extends saved-plan review
  to the VPC, subnet, route, gateway, route-table association, security group, and
  instance topology. The refreshed branch passes 67 focused tests and 12 mocked
  Terraform cases. Live AWS plan evidence remains open.
- Current restacked heads #66–#71 all passed their six required jobs: #66 `2c5766e`
  (`46117369933`), #67 `7b9fb9f` (`46117439007`), #68 `6afa0ef` (`46117499822`),
  #69 `f21d61a` (`46117561667`), #70 `5f70852` (`46117637674`), and #71 `63df036`
  (`46119306265`). All six required jobs passed on those heads. These are CI/local
  checks only; they do not establish AWS or GPU behavior. All PRs remain open and
  unmerged pending owner review; no merge was performed.
- The repository has prepared source for a separate EC2 L4 environment, host
  configuration, Docker deployment, vLLM gateway path, tenant controls, monitoring,
  benchmark/evaluation/release tooling, incident procedures, and cleanup. This is
  implementation/static/local evidence only. No L4 driver install, GPU computation,
  real vLLM inference, GPU benchmark, or cloud teardown has been demonstrated.
- AWS denied the initial quota request by email. The owner reports manually appealing
  through the existing case. The latest read-only request history is `CASE_CLOSED` with
  desired value `4.0`, and applied On-Demand G/VT quota is `4.0`. Do not create a
  duplicate request. The expected account was verified; project-tag inventory and the
  project EC2 instance query returned zero.
- The corrected 12-hour estimate is `$18.5193` with `$6.4807` arithmetic headroom
  under the `$25` ceiling. This is only a planning estimate. Shared Terraform backend
  and budget resources were absent in the last exact-name inventory, and the recorded
  bootstrap preview used a placeholder alert recipient. Bootstrap, live backend plan,
  recipient validation, current pricing, and explicit apply authorization remain
  separate gates; quota approval alone is not permission to spend.
- This project has created no AWS resources, downloaded no model weights, used zero
  verified GPU instance hours, and recorded `$0` project-specific AWS spend.


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
is open and ready for review, stacked on PR #55. Initial head `ad10699` passed all five required
checks in run `46039778508`, including one clean-room local end-to-end cycle. The
material tensor-parallel integer type-safety follow-up is head `852c873`; all five
required checks passed in run `46040861818`, including the one workflow clean-room cycle.

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
- [x] Rerun required CI after the material tensor-parallel type-safety fix; all five
  jobs passed on head `852c873` in run `46040861818`.
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
- [x] Add host-side verification of current live champion and model file digests in
  the dependent host controller (PR #56). Its 16 fake-based tests and CI pass prove
  local control flow only; checking actual host state and model files remains open.
- [x] Implement sequential deployment, readiness checks, transaction recovery, and
  rollback in the dependent host controller (PR #56). Real vLLM rollout, gateway
  inference, rollback, and interrupted-host recovery remain pending L4 execution.

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
- [x] Add mocked-provider Terraform tests for the guest timer, one-time cloud
  schedule, role scope/trust, shutdown and volume behavior, and expiry input limits.
  These verify configuration only; they do not replace the real expiry test below.
- [x] Add mocked-provider assertions that the host has no inbound rules and exactly
  two public IPv4 outbound rules, TCP 80 and 443; confirm the single L4 instance uses
  only the project security group and selected subnet. The effective deployed rules
  remain unverified until AWS provisioning.
- [x] Pin the exact Canonical Ubuntu 24.04 amd64 AMI and reject an untrusted or
  unavailable image before plan/apply; keep destroy planning independent of AMI lookup.
- [x] Refresh and inspect a pinned-AMI local-state preview. Its plan contains 14
  creates for one `g6.xlarge`; it is ignored locally and is not suitable for apply.
- [ ] Create and inspect the final remote-state saved plan and confirm the full current
  cost and budget recipient. The owner reports quota approval and the latest applied
  quota reads `4.0` vCPUs and request history says `CASE_CLOSED` with desired value 4.0;
  the state bucket and verified Budget recipient are absent. Do not apply until the exact plan, owner authorization, and $25 project
  gates are cleared.

**Exit gate:** exact plan creates one authorized L4 and only enumerated project
resources, estimated total remains below $25 with safety margin, both real expiry
paths are independently tested, and teardown/absence commands are ready.

### Package 3 — Manual Linux, NVIDIA, CUDA, Docker, and Ansible

**Status:** PR #50 contains a non-billable ordered install manifest and hashed PyTorch lock. PR #57 adds a universal hash-locked Ansible 2.21.6 controller and local-host role for the dated Ubuntu/NVIDIA/CUDA/Docker candidate set. Its six checks, including one clean-room local run, passed on head `4795f12` in `46045068200`; PR #57 is ready for review. No GPU host has been configured; candidates are not runtime-verified.

- [x] Select and pin a candidate standard Ubuntu 24.04 x86_64 AMI, R580.196.11 host
  driver, CUDA Toolkit 13.0.3, Docker Engine 29.9.3/Compose 5.8.1, NVIDIA Container Toolkit 1.20.2,
  Python 3.12, standalone PyTorch 2.14.0+cu130, vLLM 0.34.0, and the pinned Qwen
  revision using official release and artifact metadata. Version-family compatibility
  is researched on paper; live kernel, signed-index, package-install, model-license,
  artifact, and runtime verification remain mandatory before or during the L4 batch.
- [x] Record ordered host/container components, candidate versions, verification
  points, stop conditions, and items deliberately kept off the host in
  `GPU_HOST_INSTALL_MANIFEST.md`.
- [x] Resolve and hash-lock the standalone PyTorch 2.14.0 CUDA 13.0 dependencies for
  CPython 3.12 / Linux x86_64; keep the install separate from the vLLM image.
- [ ] Recheck signed package indexes and exact package versions against the pinned AMI
  and live Ubuntu kernel before launch; retain the reviewed package metadata.
- [x] Prepare install automation, CUDA/PyTorch/Triton experiments, bounded host
  commands, output capture, and recovery steps before paid compute; the commands are
  recorded in the host manifest, manual guide, and batch runbook.
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

**Status:** PR #49 (`codex/gpu-cuda-lab-preparation`) is open. PR #65's bounded Triton
vector-add and Nsight instructions are restacked locally on PR #64 head `06f1a11`.
Twelve focused tests and full `make verify` (193 passed, 2 skipped) pass locally.
Parent PR #64 passed all six checks in run `46114151883`. PR #65 source head `49076a5` passed all six required jobs in run `46114955314`; the local-e2e job is recorded as the single integrated local CPU clean-room acceptance run in `docs/governance/VALIDATION.md`. Governance follow-up head `24ea5e8` passed all six checks in `46117285643`; its P1 evidence thread is resolved and PR #65 is ready for owner review. No kernel has been compiled on a GPU and no real measurements exist.

- [x] Prepare bounded CPU/GPU vector and matrix operations, separate host/device
  copies, supported precision checks, and warmup/repeat controls.
- [x] Use CUDA events plus explicit synchronization for GPU timings; test the dry-run
  without importing PyTorch or touching a GPU.
- [x] Prepare an optional Triton vector-add experiment using the existing hash-locked
  Triton dependency, with a no-GPU plan, L4/host guard, result verification, runtime
  cap, and private output. Document short Nsight Systems/Compute samples, counter
  permission limits, package-availability checks, and separation from normal timings.
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
- [x] Rerun `make demo-redis-outage` after the shared rollout-store fix. CI run
  `46068015904` verified HTTP 503 from both gateways while Redis was unavailable,
  Redis recovery, and readiness on both gateways. The initial HTTP 500 and root cause
  remain in `INCIDENT-LOCAL-REDIS-001.md` as a real local incident history.
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

**Status:** local failure/recovery evidence and reversible GPU drill preparation exist;
real GPU incident exercises remain unstarted.

- [x] Prepare safe, reversible GPU/container/model/admission/monitoring drill steps
  and host recovery methods without destructive host changes.
- [ ] Execute representative failures on the authorized L4; capture genuine logs,
  telemetry, detection, root-cause alternatives, recovery time, verification, and
  prevention for every executed drill.

**Exit gate:** reports prove real failure and independent recovery; no simulated error
is presented as an executed incident.

### Package 10 — Automation, clean-room reproduction, and teardown

**Status:** automation source, static checks, and the designated local CPU clean-room
cycle are prepared and CI-validated; cloud reproduction and teardown remain pending.

- [x] Prepare Makefile/Ansible/Compose/CI automation and ensure normal PR CI never
  launches paid AWS jobs.
- [ ] Validate host automation on the real L4 and independently test its expiry and
  teardown behavior without touching unrelated resources.
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
- The latest `us-east-1` applied G/VT quota is `4.0` vCPUs and request history is
  `CASE_CLOSED` with desired value 4.0. Previously checked `us-east-2` and `us-west-2`
  values were zero. Do not send a duplicate appeal. Recheck
  current quota and live capacity before any plan/apply; quota value alone is not
  launch authorization.
- Provisional 12-hour estimate: about `$10.68` before tax for one g6.xlarge, one public
  IPv4, 100 GiB gp3, short-lived S3 state and lock objects, one scheduler invocation,
  and 1 GiB of internet egress. A 25% tax allowance plus `$5` general reserve gives
  about `$18.5193` per the corrected 2026-11-28 Price List API inputs in `COST_REPORT.md`. This is neither a provider quote nor authorization. Confirm current
  rates, the account tax profile, aggregate data-transfer usage, state retention, and
  exact plan immediately before any paid run.
