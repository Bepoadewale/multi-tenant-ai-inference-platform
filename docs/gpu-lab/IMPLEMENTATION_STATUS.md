# GPU Lab Implementation Status

## Latest PR and validation status — 2026-11-28 17:58 UTC

PRs #77–#83 passed all six required jobs on refreshed heads in runs `46169578415`,
`46170127067`, `46170178018`, `46170356996`, `46170595453`, `46170895199`, and
`46171131696`. PR #84 head `4a4f542` passed all six jobs in run `46172702249` after
the current-quota documentation update. Its local validation passed 67 focused tests,
12 mocked Terraform cases, Ruff, and the 35-file docs checker. No AWS resources, GPU
execution, or spend.

## Historical read-only AWS gate snapshot — 2026-11-28 15:06 UTC

- AWS Service Quotas history reports the existing request `CASE_CLOSED` with desired
  value 4.0; `get-service-quota` confirms 4.0 applied On-Demand G/VT vCPUs in
  `us-east-1`. That is numerically enough for one `g6.xlarge`, but it does not reserve
  availability-zone capacity. Do not submit another request.
- The exact project state bucket, DynamoDB lock table, and project Budget are absent.
  Project-tag inventory and EC2 instance queries returned no matches. No Billing
  alternate contact exists. A different account Budget was listed, but its project
  coverage is unverified and it is not relied upon.
- No AWS resource, GPU hour, or project spend has been created. No Terraform state
  backend or locked GPU plan exists. Do not launch until the private alert recipient,
  reviewed bootstrap plan, remote-state lock, exact GPU-root plan, complete cost and
  live capacity checks, expiry/teardown review, and separate apply authorization are
  complete.
- PR #42 (`6be7c96`), PR #52 (`7c12824`), and PR #84 (`c43cb0a`) have passing
  required CI. PR #43 and #53 are conflicting after parent updates and need restacking
  and fresh CI. GitHub showed 54 open PRs and no approving reviews in the snapshot.


**Overall:** ACTIVE — Phase 2 infrastructure is prepared; the owner reports quota approval and the latest AWS CLI read confirms an applied On-Demand G/VT quota of `4.0` vCPUs, sufficient on paper for one `g6.xlarge`. The latest request-history API read says `CASE_CLOSED` (desired value 4.0); `get-service-quota` confirms 4.0 applied vCPUs. A live launch remains gated by the exact remote-state plan, verified budget-alert recipient, full cost, current capacity, expiry, teardown, and separate apply authorization. The deployment stack is statically prepared through PR #53 and includes PRs #33–#36. PR #53's code head `e623b75` passed all five checks in `46023306230`; its documentation follow-up `2153942` passed all five checks in `46025160292`. PR #54 passed all five required jobs in `46028053505`; PR #55 passed all five in `46034523863`; PR #56 updated head passed all five in `46040861818`. PR #57 head `4795f12` passed all six jobs, including one fresh-runner clean-room cycle, in `46045068200`; PR #57 is ready for review and remains open. PR #58 adds the manual reproduction guide and GPU tenant identities. Run `46052092657` passed the checksum-verified Trivy scan but smoke found the edge-device inventory empty because edge agents could not read the owner-only token file. Commit `d759b8e` matches the two local agents to the bootstrap UID/GID; all six jobs, including the fresh-runner clean-room cycle, passed in `46054114999`. Commit `a1616ec` addresses three automated operator-guide findings; all review threads are resolved and final-head CI runs `46055428111`, `46056755505`, `46057657498`, and runbook follow-up `46058891531` each passed all six jobs, including local E2E. The batch and manual vLLM procedures now share the model-cache volume and served alias; a direct non-streaming adapter contract test is added. No GPU cloud execution has occurred in this goal.

**Latest Phase 6 evidence:** PR #58 head `351f164` passed all six checks in run
`46068015904`, including the corrected local outage/recovery drill. Both gateways
returned 503 while Redis was unavailable, Redis recovered, and both gateways became
ready. The signed-tenant API denial test and ten-stream cancellation drill also
passed in earlier runs. This is local CPU Compose evidence, not live GPU evidence.
PR #58 remains open and unmerged.

**Earlier Phase 2 plan-review history:** PR #84's earlier code and documentation
heads passed all six checks in runs `46147292091` and `46148089116`. Review then
found that the guard checked public-IP assignment on the subnet but not the EC2
instance plan value. The validator and both plan fixtures now require the instance
public-IP flag; 44 focused tests, Ruff, `make gpu-docs-validate` (35 files), and
`git diff --check` pass locally. Follow-up head `8349510` passed all six required
checks in run `46148953601`; documentation head `355deba` passed all six in run
`46149649470`.

**Quota update (2026-11-28):** the owner reports the AWS quota request was approved.
A read-only CLI check confirms 4.0 applied On-Demand G/VT vCPUs, sufficient on paper
for one `g6.xlarge`; Service Quotas request history now reports `CASE_CLOSED` with desired value 4.0, matching the 4.0 applied quota. This does not reserve AZ capacity. The private Budget recipient,
remote-state backend and locked plan, current full-cost/expiry review, and separate
apply authorization remain open gates. Finish these non-GPU gates before launching.

**Live pull-request review snapshot (2026-11-28 15:06 UTC):** 54 PRs remain open and none has
an `APPROVED` review decision. PR #43 and #53 have merge conflicts after parent
updates; the other 52 are currently mergeable. PR #42 head `6be7c96` passed all five
checks in run `46157149583`, PR #52 head `7c12824` passed all five in
`46157257204`, and PR #84 head `c43cb0a` passed all six in `46155121499`. PR #84 is
open and mergeable with no review decision. The open PR stack still needs owner
review/merge decisions; PR #43 and #53 need restacking and fresh CI.

**Recent non-billable work:** updated heads #59–#63 passed all six required jobs in
runs `46112594557`, `46112810861`, `46113035567`, `46113162785`, and
`46113289587`; PR #64 passed all six in `46114151883`. PR #65 source head `49076a5`
passed six jobs in `46114955314`. Its single designated integrated local CPU
clean-room run is recorded in `docs/governance/VALIDATION.md`; the governance
follow-up head `24ea5e8` passed all six jobs in `46117285643`. The P1 thread was
answered with that record and resolved, and PR #65 is ready for owner review.
Sequentially restacked heads #66 `2c5766e`, #67 `7b9fb9f`, #68 `6afa0ef`, #69
`f21d61a`, #70 `5f70852`, and #71 `63df036` each passed all six required jobs in
runs `46117369933`, `46117439007`, `46117499822`, `46117561667`, `46117637674`,
and `46119306265`, respectively. All remain open and unmerged. The clean-room used
a fresh GitHub runner; no workstation repeat, AWS resource, GPU operation, or spend
occurred.

**Current AWS refresh (2026-11-28 15:06 UTC):** the expected account identity matched. The
applied G/VT quota is `4.0` vCPUs and request history is `CASE_CLOSED` with desired value
`4.0`. `g6.xlarge` was listed in five AZs in the earlier same-day check. Exact
project-tag inventory, EC2 instance query, state bucket, lock table, and project Budget
lookups found no project resources. A different account Budget exists, but coverage of
this project is unverified; there is no Billing alternate contact. The earlier Price
List result was `$0.8048/hour`; the 12-hour planning envelope is `$18.5193`. This clears
only the numeric quota condition; no apply-ready remote-state plan, verified recipient,
AWS resource, or project spend exists.

**Bootstrap readiness package (PR #74 open for owner review; current head `944b457` passed all six CI checks in run `46128237140`):** the new local-only wrappers
provide private saved-plan review, exact digest confirmation for apply, exact-resource
checks, and a separate confirmed state migration. The plan validator rejects any
unexpected resource or action and hides the configured recipient from its summary.
Six focused fake-tool tests and all three Terraform root validations pass. The bootstrap now requires Terraform 1.10+ for S3-native locking. Full `make verify` passed (Ruff, 199 tests with 2 skipped, dependency audit, Docker Compose, observability, and GPU benchmark/evaluation/CUDA dry runs); no actual Terraform plan/apply, state migration, or AWS mutation is part of this work. The
private Budget address and owner authorization are still required before any apply.

**Learning-document preparation:** the previously missing AI infrastructure handbook
is drafted in this branch. It explains GPU/CUDA layers, transformer inference and KV
cache, vLLM, multi-tenant admission, evaluation, observability, reliability, cost,
and distributed GPU concepts deliberately outside this one-L4 scope. It labels the
proposed architecture and distinguishes design explanations from real L4 evidence.
PR #75 head `a7c6ccd` passed all six required CI checks in run `46129784597`; no runtime evidence is added.
The reproduction guide's quota note is also updated to the latest recorded `4.0`
applied-vCPU reading while preserving the unresolved appeal and remaining launch
gates.

**Documentation check automation:** a standard-library link and heading checker is
now included in `make verify` and the GitHub Actions manifests job. It checks local
links in the core GPU goal, guide, status, backlog, tickets, and README without
network access. Three focused tests pass; full `make verify` passed (202 tests, 2
skipped), and all three Terraform roots validate. This does not add runtime or GPU
evidence. PR #76 head `dba21f1` passed all six required CI jobs in run `46132280041`;
it is open and stacked on #75.

**Expiry configuration tests:** PR #77 adds three mocked-provider Terraform tests
for both expiry paths, IAM scope, root-volume and metadata settings, and invalid
deadlines. All three tests pass locally. Full `make verify` passed (202 tests, 2
skipped), and `make terraform-validate` passed all three roots, including the mocked
GPU Terraform tests. The mocks make no AWS calls. Live Scheduler delivery and Ubuntu
timer execution remain unverified and required before the paid GPU batch. PR #77
implementation head `75f91e3` passed all six required CI jobs in run `46133957636`;
the PR remains open for review.

**Network configuration tests:** PR #78 adds a mocked-provider test for zero inbound
rules, exactly TCP 80 and 443 outbound, absence of IPv6/prefix-list/security-group
egress paths, and the one instance's use of the intended group and subnet. Four
Terraform tests now pass locally (three expiry and one network). This is static
configuration evidence; the live AWS security group and Session Manager remain
unverified. Full `make verify` and all Terraform root validations pass locally. PR #78
implementation head `5c3bd12` passed all six required CI jobs in run `46135887060`.
The later documentation head `6aeb638` initially failed its sandboxed-agent API demo
with HTTP 500 and no captured server detail; rerunning the failed job in run
`46136477854` passed all six jobs. The cause of the first failure is unconfirmed. PR
#78 remains open for review.

**Explicit resource tags (PR #79 in progress):** the GPU Terraform root now sets the
project, environment, owner, cost-scope, expiry, synthetic-data, and Name tags directly
on each taggable resource. A Terraform mock test checks 11 resource tag maps. The
pinned AWS provider schema does not allow tags on an individual Scheduler schedule;
its schedule group is tagged and the schedule remains in the dedicated root under its
project-specific name. Local GPU-root formatting and validation pass, as do all five
mocked Terraform assertions. This remains static configuration evidence. PR #79 is
open on branch `codex/gpu-project-tag-guardrails`; implementation head `2e92165`
passed all six required jobs in run `46137645356`, and final documentation head
`efe7eed` passed all six jobs in run `46138350722`.

**Terraform input limits (PR #80):** seven mocked plan cases now check
that unsupported GPU types, out-of-bound root-disk sizes, another AWS region/project,
and malformed AMI identifiers are rejected. The complete GPU Terraform mock suite
passes all 12 cases locally. The first region case also tripped the independent zone
guard; it was corrected to isolate only the region input. Ticket80 and the docs-link
checklist are prepared. PR #80 is open on branch `codex/gpu-input-constraint-tests`
at final documentation head `6145e25`; all six required checks passed in run
`46139713692`.

**Saved-plan validation (PR #81):** a standard-library validator reviews
the saved plan's exact managed-resource set, create-only actions, single-L4 settings,
storage, metadata, resource tags, network rules, SSM attachment, and exact expiry. The
plan command prints only a bounded summary; apply repeats the check against the
checksum-bound saved plan. Fake-CLI tests verify an unsafe plan cannot reach apply and
private user-data text is not printed. All 33 focused tests, Ruff, shell syntax,
documentation links, and diff checks pass locally; GPU-root format, validation, and 12
mocked Terraform tests also pass. PR #81 final head `3cb8139` passed all six CI jobs in
run `46142107889`, including local CPU end-to-end. This does not verify Terraform's
live AWS JSON or authorize infrastructure changes.

PR #82 adds a saved-plan check for the expected one-time expiry group and EC2
termination action. Its focused plan and wrapper tests passed 35 cases locally and
Ruff. Final head `d5afac7` passed all six CI jobs in run `46143890538`, including
local CPU end-to-end. This still does not verify actual AWS plan JSON or authorize
infrastructure changes.

**Expiry target binding review (PR #83 open on #82):** Terraform's JSON output
includes configuration references when the created instance ID and generated IAM
role ARN are not known at plan time. The saved-plan validator now requires the
Schedule target to reference the exact project expiry role and GPU instance, and
requires the expiry policy to bind to those same resources. Twenty-four focused
fixtures pass, along with Ruff and the docs-link checker. The first CI run
`46145456879` found the shell-wrapper fake plan had not been updated with the new
configuration expressions. That fixture is fixed locally; the plan and wrapper
suites now pass 39 tests, while the CI rerun remains pending. This validates the
documented fixture shape only; a real
provider plan remains required before any apply. No AWS, GPU, or spend occurred.

**Network topology guard (PR #84):** the saved-plan validator checks the configured
VPC and subnet ranges, DNS, public-IP assignment, single default route, and references
connecting the gateway, route table, subnet, association, security group, and EC2
instance. After restacking on PR #83 head `142d0f3`, 67 focused tests, all 12 mocked
Terraform cases, Ruff, and 35-file documentation validation pass. Current head
`798b2e8` passed all six checks in run `46171879043`. A real provider plan must still
confirm the fixture's JSON shape; no AWS resource or GPU execution occurred.

**Readiness target:** finish every feasible non-GPU source, configuration, deployment
automation, documentation, local/static check, CI, benchmark/evaluation/incident plan,
and evidence/cleanup safeguard before the paid GPU batch. The designated local CPU
clean-room cycle passed once; Phase 12's cloud/GPU reproduction remains outstanding.
The readiness target is to make quota approval leave only immediate live safety checks
(account, applied quota, capacity, current price, exact saved plan, total cost, expiry,
and apply authorization) plus work that needs a real L4. Do not start another manual
clean-room run. The applied quota value by itself does not authorize a paid apply.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only; numeric quota is sufficient, apply gates pending | Dedicated Terraform root, one-instance/account/region/AMI guards, encrypted gp3, IMDSv2, SSM, one-time expiry, plan digest checks, destroy safeguards, and read-only cleanup verification are prepared. PR #74 adds private bootstrap saved-plan, exact digest apply, and state migration wrappers; six required CI jobs passed on head `944b457` in `46128237140`. The pinned-AMI local-state preview proposes 14 creates for one `g6.xlarge`; it is not a remote-state or apply-ready plan. Real state locking, SSM registration, expiry, provisioning, and teardown remain untested. Read-only AWS refresh on 2026-11-28 found applied quota 4.0 and request history `CASE_CLOSED` with desired value 4.0. Five AZ offerings appeared, but exact project-tag resource/instance queries were empty and the bootstrap backend/project Budget are absent. A different account Budget is not relied upon; no Billing alternate contact exists. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Prepared — static host automation | PR #50 provides an ordered host-install manifest and 29-package hashed PyTorch lock, but PR #50 currently has a merge conflict. PR #57 adds the hash-locked Ansible 2.21.6 controller and host role for pinned Ubuntu/NVIDIA/CUDA/Docker packages, signed repositories, runtime configuration, PyTorch, and post-reboot verification. All six CI jobs passed on head `4795f12` in `46045068200`. No package has been installed on an EC2 host. The manual learning pass and second-run idempotency check remain open. |
| 4. CUDA performance lab | Prepared — static; L4 execution pending | PR #49 prepares bounded CUDA vector-add, synchronized PyTorch experiments, and no-GPU plans. PR #65 adds bounded Triton vector-add and Nsight procedures; its rebased source passes 12 focused tests and full `make verify` (193 passed, 2 skipped). No Triton kernel or profiler has run on an L4; PR #65 head `49076a5` passed all six required checks in run `46114955314`, including the designated local CPU clean-room cycle. |
| 5. vLLM and Qwen serving | Prepared — static only | The isolated Compose profile and immutable image/model candidates are prepared. The profile is now stacked after the gateway stream, admission, tokenizer, and cleanup work in PRs #33–#36. No image layer or model weights were downloaded; no L4 load, inference, or streaming result exists. |
| 6. Multi-tenant GPU gateway | Local integration fixes CI-verified; L4 unverified | PR #58 head `351f164` passed all six jobs in `46068015904`. The corrected outage drill verified 503 from both gateways, Redis recovery, and readiness from both. The ten-stream cross-gateway cancellation drill passed. No real GPU request, token reconciliation against vLLM, or live GPU cancellation has been verified. |
| 7. GPU/AI observability | Prepared — static only | PR #46 configures pinned exporters, Prometheus, Grafana, Alertmanager, OpenTelemetry, Tempo, rules, and dashboards. All five required jobs pass on the current restacked head. No live device metrics, alert, dashboard, or trace has been observed. |
| 8. Benchmarks and FinOps | Prepared — static only | PR #47 includes a bounded direct vLLM serving matrix. PR #60's current head `9a8bd28` passed six jobs in `46112810861`, after 8 focused tests, Ruff, and a no-network plan passed locally. No L4 benchmark or measured inference cost exists. |
| 9. Evaluation and releases | In progress — static implementation | PR #48 has seven synthetic evaluation cases and a privacy-safe dry-run. PR #51 designs sequential LLM release. PR #52 adds private MLflow tracking and report publication. PR #54 adds local manifest/plan controls. PR #55 adds authenticated plan/read/approval routes, checks candidate metadata against a finished MLflow run and sanitized report, and stores manifests in shared single-host SQLite. Latest five-check run `46034523863` passed. PR #56 head `852c873` passed all five checks in `46040861818`, including the required clean-room cycle. Live host/inference/recovery checks remain open. No real LLM evaluation or release has occurred. |
| 10. Incidents and recovery | First local incident recorded; GPU drills pending | `INCIDENT-LOCAL-REDIS-001.md` records the real CI 500, root cause, and fix. Run `46068015904` verified both gateways returned 503 during the Redis outage, Redis recovered, and both gateways became ready. No controlled L4 failure/recovery report exists yet. |
| 11. Automation and CI | In progress — guarded host commands CI-verified; live host use pending | PR #64 adds pre-driver identity checks, deployment provenance checks, bounded deployment/evaluation/benchmark wrappers, authenticated tenant smoke, a reversible Redis drill, and private evidence output. Twenty focused tests and full `make verify` pass locally; all six CI jobs passed in `46114151883`. No Terraform apply, Ansible host configuration, EC2 wrapper, or GPU operation has run. |
| 12. Clean-room and teardown | Local CPU cycle recorded; cloud/GPU gate not started | One designated local CPU clean-room cycle passed at source `49076a5` in `46114955314`; independent AWS recreation, export and provider-side absence checks remain L4/Phase 12 work. |

## Baseline verified directly

- FastAPI gateway with Ed25519 signed identities, tenant/model authorization, Redis-backed request/token/concurrency admission and metering, routing, streaming, telemetry, CPU ONNX and vLLM adapter modules.
- Local Compose and historical clean-room evidence use CPU ONNX. The current repository does not demonstrate GPU execution.
- Existing Terraform root is an EKS and managed-services contract; existing Kubernetes vLLM manifests are not the EC2 deployment.
- Gateway vLLM response accounting and token estimation need direct tests and design review before GPU integration.
- Baseline on `main` reported 84 advisory records across seven transitive packages and failed `make verify`. PR #31 adds shared minimum-version constraints; local full verification, image build, clean-room evidence, and all four required GitHub check names across two workflow runs passed. Human review/merge remains outstanding. See ticket #31 and `docs/governance/VALIDATION.md`.
- Historical validation is documented in `docs/governance/VALIDATION.md`; this session's local results are not GPU evidence.
- The prior CPU baseline has two recorded clean-room cycles. This GPU goal requires one successful end-to-end clean-room reproduction; rerun only to recover from a failure or verify a material fix.

## Authorization and resource tracking

- Initial project ceiling: **USD $25 maximum**. No billable apply is authorized until the full bounded execution estimate and exact resource plan fit under that ceiling and the expiry/teardown controls are ready.
- GPU instance-hours used: **0 verified in this goal**.
- AWS resources created by this goal: **none**.
- Exact-name read-only checks on 2026-11-26 found the planned repository state bucket,
  DynamoDB lock table, and `$10` budget were all absent. They appear as creates in the
  7-resource bootstrap preview; no bootstrap apply has occurred.
- Read-only `us-east-1` resource-group tag and EC2 instance lookups for the exact project tag: **no matches**. Untagged or differently tagged leftovers are not excluded.
- EC2 instance type offerings list G6 in multiple `us-east-1` AZs; this is not a capacity reservation.
- On-Demand G/VT applied quota: **4.0 vCPUs** (`L-DB2E81BA`) in the latest
  2026-11-28 read-only check; request history is `CASE_CLOSED` with desired value 4.0.
  Five AZ offerings were listed, but they do not reserve capacity. The expected state
  bucket, DynamoDB lock table, and project Budget are absent; no tagged project resource
  or project EC2 instance was found. A different account Budget is not relied upon; no
  Billing alternate contact exists. The guarded preflight stopped at the missing bucket.
  No apply or spend has occurred.
- Price List API on 2026-11-28: Linux shared On-Demand `g6.xlarge` **$0.8048/hour**.
  The current 12-hour full-resource planning envelope is **$18.5193**, including
  provisional tax and contingency; see `COST_REPORT.md`. This is an estimate, not a
  settled bill or apply authorization.
- Credentials are never recorded here.

**GPU preparation:** [GPU batch runbook](GPU_BATCH_RUNBOOK.md) groups preflight,
manual driver/CUDA/container/PyTorch setup, vLLM, tenant validation, telemetry,
benchmark/evaluation, evidence export, and teardown. It is a static procedure only;
all package candidates must be rechecked and no L4 command has run. The latest
read-only AWS check on 2026-11-28 verified the expected account, applied G/VT quota
of `4.0` vCPUs, and request history `CASE_CLOSED` with desired value `4.0`. Exact
project-tag EC2/resource-group queries returned no resources in `us-east-1`. A separate EC2
Compose profile now statically configures one vLLM GPU service, two loopback-only
gateway replicas, and shared Redis. Catalog routing and health checks are opt-in and
unit-tested; the profile has not run on an L4.

## Current Next Actions

1. Resolve PR #84 review feedback; do not merge without owner authorization.
2. Continue non-billable work that closes missing Phase 2 and other pre-GPU acceptance gaps; avoid repeating the designated local clean-room cycle.
3. Keep AWS read-only until a valid private Budget recipient, bootstrap plan, locked GPU-root plan, cost/expiry review, and separate apply authorization are ready; do not send another quota request.
4. Recheck signed package indexes, exact model/image digests, capacity, prices, and total cost immediately before any authorized GPU batch.
5. After every gate is met, perform one bounded L4 batch, export evidence, and terminate/verify teardown under the $25 ceiling. Keep the PR-only workflow; no direct changes to `main`.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
