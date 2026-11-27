# GPU Lab Execution Journal

<<<<<<< HEAD
## 2026-11-27 — Quota status rechecked without mutation
=======
## 2026-11-27 — Attempt the authorized quota-case update with AWS CLI

- **Phase:** Phase 2 — static-only EC2 preparation; GPU execution remains blocked.
- **Branch / PR:** `codex/quota-case-cli-followup`, preparing a focused PR #41 on top
  of PR #40.
- **Objective:** follow the owner's instruction to reopen the existing denied quota
  case through the CLI, while avoiding a duplicate quota request or support case.
- **AWS identity and case:** verified `ai-platform-pilot-key` caller account against
  the expected project account. The support case reference was obtained from the
  existing quota record and the AWS email; the identifier is intentionally omitted
  from the public repository.
- **Attempt:** inspected `aws support help`; it has `add-communication-to-case` but no
  `reopen-case` command. Used the available add-communication operation with the
  prepared appeal text and existing case reference. AWS returned
  `SubscriptionRequiredException` before accepting any communication.
- **Failed approach:** the SSO profile had no cached token, so an SSO device-auth
  login was briefly started. After the owner clarified to use CLI only, it was
  canceled before sign-in; no browser interaction or AWS change occurred.
- **Alternative checked:** `aws service-quotas create-support-case` only applies to
  quota requests with status `PENDING`. This request still reports `CASE_OPENED`, so
  that command would not reopen it and was not called.
- **Post-check:** a fresh read returned `CASE_OPENED` and desired quota `4.0`; applied
  quota remains `0.0`. No new request, support case, communication, resource, GPU hour,
  or spend was created.
- **Support path:** AWS's official guide documents reopening a resolved case through
  the Support Center. The owner's explicit CLI request has been attempted, but the
  API route is blocked by the account's Support plan. Keep the project moving on
  non-billable tasks; do not launch with zero applied quota.
- **Next:** submit this truthful blocker record in PR #41 and continue remote-state,
  cost, expiry, and automation work that does not require GPU runtime.

## 2026-11-27 — PR #40 status follow-up checks passed
>>>>>>> e837919 (docs: record quota case CLI blocker)

- **Phase:** Phase 2 static-only preflight; no cloud resource creation or spend.
- **Command:** read-only AWS Service Quotas queries in `us-east-1` checked the existing
  request and applied G/VT quota using `ai-platform-pilot-key`.
- **Result:** request `34647c8598cb4ac5a8e43b3e956ccd65ikyKx4Qy` remains
  `CASE_OPENED`, requested value `4.0`; the applied `Running On-Demand G and VT
  instances` quota is `0.0` vCPUs.
- **Decision:** do not retry the request or launch infrastructure. This is status
  evidence only; quota approval would still not authorize Terraform apply.
- **Cost:** no AWS resources or spend; GPU instance-hours remain `0`.

## 2026-11-27 — PR #35 lease held during tokenizer preflight

- **Phase:** Phase 6 non-billable gateway correctness work. Phase 2 remains the active
  cloud phase; no AWS resource or GPU was used.
- **Branch / PR:** `codex/tokenizer-admission-preflight`, PR #35 stacked on PR #34.
  Code fix commit: `59cca44`; docs and rebase follow-up are local pending publication.
- **Starting state:** PR #35 was based on old PR #34 head `ae99959`; PR #34 had been
  rebased and updated to `b51aedd`. The PR #35 branch had diverged after both histories
  changed.
- **Objective:** resolve review finding that tokenization can take longer than the
  concurrency lease, allowing admission to expire before the exact token reservation.
- **Rebase/troubleshooting:** rebased PR #35 with
  `git rebase --onto origin/codex/redis-admission-leases ae99959940b217495ae5a2e231656965b2a4ce2f
  codex/tokenizer-admission-preflight`. Conflicts affected shared goal/status/journal
  docs and `test_vllm_streaming.py`. Kept the updated PR #34 documentation and combined
  unique PR #35 test functions with current stream regression tests. A targeted test run
  then found five `NameError` failures because the merged test file lacked its
  `HTTPException` import; restored the import and reran successfully. No conflict markers
  or partial rebase remain.
- **Change:** start a bounded lease watcher immediately after vLLM admission, retain it
  through `/tokenize` and exact reservation adjustment, then stop it on all success,
  rejection, error, and cancellation paths. Normal generation and streaming start their
  own watcher after preflight.
- **Validation:** targeted stream/lease suite passed **21 tests**. `make verify` passed
  Ruff, **87 tests**, pip-audit and Compose config (2 optional Redis tests skipped; one
  existing Starlette deprecation warning). Redis 7.4 integration passed **2 tests**.
  `git diff --check` passed. The integration container was stopped and is absent.
- **Review response:** resolved the stale second-clean-cycle finding based on the
  owner's explicit rule: one successful cycle is sufficient, and the two historical CPU
  cycles remain evidence.
- **Cloud/cost:** no AWS calls, GPU, or live vLLM; goal-specific spend remains `$0` and
  GPU hours remain `0`.
- **Follow-up:** pushed PR #35 head `5cd8dfb` with `--force-with-lease`, updated its
  description, resolved both review threads, and watched one CI run to success. Run
  `45937540562` passed all four required jobs.

## 2026-11-27 — PR #36 carried onto the tokenizer lease fix

- **Phase:** Phase 6 non-billable gateway tests. The active cloud phase remains Phase 2.
- **Branch / PR:** `codex/vllm-preflight-failure-cleanup`, PR #36 stacked on PR #35.
  Local source commit `ec5dcd1`; local documentation commit `a8d3278`.
- **Starting state:** PR #36 targeted the earlier #35 branch at `a8e63b8`; #35 had
  moved to `5cd8dfb` after the tokenizer lease fix.
- **Action:** ran `git rebase --onto origin/codex/tokenizer-admission-preflight
  a8e63b8 codex/vllm-preflight-failure-cleanup`. Two commits replayed. Shared goal,
  status, backlog, journal, evidence, and validation docs conflicted; retained the newer
  #35 state and preserved the #36 ticket, test additions, and validation entry.
- **Validation:** `make verify` passed Ruff, **90 tests**, pip-audit, and Compose
  configuration; 2 optional Redis tests were skipped, with one existing Starlette
  warning. `git diff --check` passed. No full clean-room run was started because the
  existing PR CI cycle is the relevant reproduction gate.
- **Limits:** cancellation and Redis outage use deterministic local doubles; tokenizer
  timeout uses `MockTransport`. No real Redis failure, live vLLM, AWS, or GPU was used.
- **Cloud / cost:** no AWS resource or spend; GPU hours remain `0`.
- **Next action:** publish this rebased PR #36 branch with `--force-with-lease`, update
  the PR evidence, then watch its CI once.

## 2026-11-27 — Redis lease review fixes and branch recovery

- **Phase:** Phase 6 non-billable gateway correctness prework. The active cloud
  implementation phase remains Phase 2; no cloud resource was created or changed.
- **Branch / PR:** `codex/redis-admission-leases`, PR #34 stacked on PR #33. Code fix
  commit: `4cffc60`, documentation head `b51aedd`. The rebased branch was pushed with
  lease protection; both review threads were resolved and all four required checks
  passed in run `45936485832`.
- **Starting state:** local branch was rebased onto PR #33 head `c5de757`, while the
  GitHub PR branch still pointed to `ae99959940b217495ae5a2e231656965b2a4ce2f`.
  Five validation and goal documents contained local updates that had not been committed.
- **Objective:** close two lease-lifecycle review findings, record actual test evidence,
  and make the reviewed branch reflect the rebased source.
- **Commands / troubleshooting:** inspected `git status`, branch history and PR state;
  the local and remote histories diverged after the first rebase. An initial rebase
  replayed PR #33 ancestors and produced conflicts; it was aborted. The corrected
  `git rebase --onto origin/codex/gateway-stream-accounting e87753c
  codex/redis-admission-leases` replayed only PR #34 commits. Documentation conflicts
  were resolved by retaining the newer PR #33 documentation and PR #34 ticket/code.
- **Changes:** bounded asynchronous lease renewal and request cancellation before
  expiry; reject renewal after expiry; prune stale reservation metadata on later
  admissions while retaining conservative token-ledger entries through their windows.
  Added regression tests for an unresponsive renewal and repeated crash cleanup.
- **Validation:** `make verify` passed Ruff, 75 tests, pip-audit and Compose config; two
  optional Redis integration tests were skipped in the no-Redis run. A disposable
  local Redis 7.4 container ran the relevant lease suite with 7 passing tests. The
  container was stopped after the test. The evidence and test limitations are in
  `VALIDATION.md` and `EVIDENCE_MANIFEST.md`.
- **Failed approaches:** the first rebase attempt replayed the wrong ancestor range and
  caused conflicts in files already changed by PR #33. It was aborted before any push;
  the `--onto` rebase used the old PR #34 base commit to replay only its own work.
- **Cloud / cost:** no AWS API, GPU, or live vLLM was used in this package. Goal-specific
  spend remains `$0`; GPU instance-hours remain `0`.
- **Completion:** the rebased PR #34 branch was published, both review threads resolved,
  and all four required checks passed as recorded above. Work then moved to PR #35.

## 2026-11-27 — Clean-room run count clarified

- **Scope:** verified the repository's clean-room requirements after the owner clarified
  that one successful run is sufficient.
- **Finding:** `AGENTS.md` and the pull request template required a second bootstrap/demo;
  the GPU goal's final acceptance text already described one reproduction. Historical
  CPU evidence records two successful runs, but no GPU clean-room run has started.
- **Decision:** one successful clean-room cycle satisfies this GPU goal and the shared
  implementation-PR gate. Repeat only after a failed cycle or a material correction that
  requires revalidation. Historical records remain unchanged.
- **Changes:** aligned `AGENTS.md`, the PR template, goal document, and implementation
  status with that decision.
- **Validation:** source review only; no runtime clean-room cycle was run. No AWS resource
  was created or changed.
- **Next step:** continue Phase 2 non-billable work; retain the single clean-room run for
  Phase 12 after the GPU automation and evidence process are ready.

Preserve earlier entries. Record actual actions and outcomes; never replace failed attempts with a clean narrative. Keep credentials, tokens, private data, raw Terraform state, and sensitive logs out of this file.

## 2026-11-26 — Goal registration and initial audit

- **Phase:** 1 — repository audit, research, and architecture.
- **Branch / PR:** `codex/single-l4-gpu-goal` / [#30](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/30), draft and open.
- **Starting repository:** clean `main`, `c8f02ed`; tracking `origin/main`.
- **Starting AWS state:** not yet queried in this project. No cloud mutation was performed.
- **Objective:** register the persistent project charter and inspect baseline implementation before GPU architecture work.
- **Commands and checks:** inspected `AGENTS.md`, README, repository file inventory, system map, vLLM adapter and gateway selection, tenant/catalog/auth/Redis admission code, Terraform EKS root and GPU module, Kubernetes vLLM manifest, Compose, Makefile, CI, status/backlog, and validation history; ran `gh auth status` and `gh pr list` (authenticated as Bepoadewale; no open PR listed); `make verify`; `docker compose config --quiet`; `make cloud-delivery-validate`; read-only AWS identity, tag inventory, instance inventory, instance-type offerings, quota, and Price List API lookup; official docs/model-card research.
- **Findings:** local production claim is CPU ONNX only; gateway has a vLLM HTTP adapter selected by `backend_url`; Redis quotas and server-side Ed25519 tenant identity exist; current GPU deployment manifests are Kubernetes/EKS contracts and explicitly outside execution; Terraform EKS root includes NAT/RDS/ElastiCache and must not be used for this project.
- **Issues to audit:** streaming token accounting counts chunks, streaming supplies a fixed TTFT, quota reservation estimates whitespace-delimited words; Redis release accepts `actual_tokens` but its Lua release only decrements active requests, while daily and minute token ledgers retain estimated reservations; mutable `latest` vLLM image and a different model in the old Kubernetes contract; no isolated EC2 deployment root identified in the source inventory.
- **Changes:** added goal, proposed architecture, status, risk, research, and execution records; linked the goal from README and docs index.
- **Tests / validation:** `make verify`: Ruff passed; 50 tests passed, one Starlette deprecation warning; `make audit` failed with 84 known vulnerability records across seven packages and exit 2 after retries, so full command failed before Compose validation. `docker compose config --quiet` passed when run separately. `make cloud-delivery-validate` and `make terraform-validate` passed. Historical results remain distinct from current results; see `VALIDATION.md`.
- **Cloud resources/cost:** none created or changed. Read-only project-tagged resource and EC2 instance queries returned no matches in `us-east-1`. G/VT On-Demand quota is 0 vCPUs. AWS Price List API lookup returned g6.xlarge Linux On-Demand `$0.8048/hour` in US East (N. Virginia), giving `$6.4384` for 8 hours and `$9.6576` for 12 hours before storage, IPv4, transfer, state, logging, and taxes. No spend estimate is yet complete or authorized for apply.
- **Decisions:** favor On-Demand as requested; no Spot plan. Do not request quota increase or apply Terraform during Phase 1. Treat quota increase as a pending AWS account change requiring explicit preparation and authorization review.
- **Pull request:** created draft PR #30 at commit `754564d`; documentation-only registration. CI status will be recorded after the existing PR checks complete. Per repository policy, no merge or clean-room readiness claim is made here.
- **Next action:** deepen Phase 1 audit and official source research; identify safe baseline audit remediation as a separate focused package; then open the docs-only goal-registration PR.
- **Next action:** finish source audit, run `make verify` as explicitly requested, record exact outcomes, then complete read-only AWS inventory and official documentation research.

## 2026-11-26 — Dependency audit repair and clean-room verification

- **Phase:** Phase 1 — repository audit, research, and architecture. This was a
  non-billable local implementation package to restore the baseline validation gate.
- **Branch / PR:** `codex/fix-baseline-dependency-audit`; [PR #31](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/31), draft and open. Commits `e1d9aa0` and `9710932`. The goal registration PR is #30; its required checks passed on the observed revision.
- **Starting repository:** started from a new branch based on `main` at
  `c8f02ed`, then committed the source fix and evidence. `gh auth status` confirmed
  the existing Bepoadewale GitHub session; no credential was printed or stored.
- **Starting local state:** an existing `.local/self-service/profiles.db` predated
  this work. It was moved to `/tmp/multi-tenant-ai-inference-platform-self-service-profiles.db`
  before project cleanup and restored to its original path after final cleanup.
- **Objective:** resolve the pre-existing pip-audit failure in local and container
  installs and establish fresh clean-room evidence before review.
- **Commands and checks:** `make install`; `make bootstrap-local`; `make smoke`;
  `make demo-flagship`; `make verify`; `make clean-local` (two successful clean-room
  cycles); `docker build -t inference-gateway:dependency-audit -f gateway/Dockerfile .`;
  `git diff --check`; GitHub PR checks are under one watcher using
  `gh pr checks 31 --watch --interval 120`.
- **Changes:** added root `constraints.txt` with safe minimum versions for seven
  affected transitive dependencies; applied it to Makefile install and the gateway
  Dockerfile. Updated README, `PROJECT_STATUS.md`, `docs/governance/VALIDATION.md`,
  and ticket #31. The constraints prevent resolutions below current audit fixes but
  are not a complete lock file.
- **Validation:** PR branch `make verify` passed Ruff, 50 tests (one existing
  Starlette/httpx deprecation warning), pip-audit (`No known vulnerabilities found`,
  editable project skipped), and Docker Compose configuration. Local image build
  passed on arm64. Fresh bootstrap, smoke, and cumulative CPU/local demo passed.
  Final cleanup left no project Compose containers, generated `.venv`, or generated
  `models/`; the standalone test image was removed.
- **Failed approaches and diagnosis:** after an initial demo sequence had populated
  Redis, rerunning the cumulative demo against that same state returned 429 in
  `demo-agent-tools`, because the synthetic tenant's minute allowance had already
  been consumed. The failed rerun was retained as troubleshooting history, not counted
  as a clean-room pass. A new project cleanup and bootstrap reset Redis, and the full
  demo then exited 0. Expected connection resets during controlled restarts were
  visible in logs; the relevant recovery assertions passed.
- **Evidence:** full results in `docs/governance/VALIDATION.md`; detailed acceptance
  checklist in `docs/tickets/ticket31.md`; reviewable source and validation changes in
  PR #31. No screenshot was generated. No AWS command was needed for this package.
- **Cloud resources/cost:** no cloud resource was created or changed; GPU instance
  hours remain 0; AWS spend from this package is $0. The pre-existing local profile DB
  was restored. No other local generated artifacts remain.
- **Decisions:** keep this fix isolated from the GPU goal PR. Do not mark PR #31
  review-ready until CI is terminal. The PR remains draft pending checks/review.
- **Blockers:** PR #31 CI result is pending. Separately, first G6 launch remains
  blocked by quota `L-DB2E81BA` at 0 vCPUs and by the unresolved full $25-bound cost,
  expiry, resource, and teardown plan.
- **Next action:** review gateway vLLM schema and token/accounting/cancellation paths,
  continue official compatibility and price research, and record the exact dependency
  PR CI outcome before updating the project goal state.

## 2026-11-26 — GPU stack compatibility research

- **Phase:** Phase 1 — official research; no infrastructure or local application
  runtime was started.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30, draft.
- **Starting state:** persistent goal updated to include PR #31, its local evidence,
  current quota blocker, and prior checks. PR #31's CI watcher was still active; no
  result was assumed.
- **Objective:** refine the candidate host/GPU runtime compatibility model from current
  primary sources, and correct the EC2 L4 memory description to match AWS's units.
- **Commands / research:** browsed the AWS EC2 accelerated-instance table and public
  NVIDIA driver guide, NVIDIA CUDA compatibility matrix, PyTorch local-install guide,
  and current vLLM stable and latest GPU guides.
- **Findings:** AWS lists `g6.xlarge` as 4 vCPUs/16 GiB system memory and 1 L4 with
  22 GiB GPU memory; `g6.2xlarge` is 8 vCPUs/32 GiB and the same 22 GiB GPU memory.
  AWS's Ubuntu 24.04 x86_64 CUDA example installs matching kernel headers and shows
  CUDA 13.0/driver 580.65.06. NVIDIA's broad minor-compatibility table lists driver
  family 580+ for CUDA 13 and 525+ for CUDA 12, subject to toolkit-specific requirements
  and feature limits. Current vLLM stable docs list L4 support, Linux/Python 3.11–3.14,
  default CUDA 12.9 wheel plus 12.8/13.0 choices, and warn of compiled-kernel binary
  compatibility. vLLM wheels bundle PyTorch, so serving should use the matching bundled
  build; a separate PyTorch learning workload should use an isolated environment.
  Fractional `g6f` L4 slices do not meet the one-full-L4 project constraint.
- **Changes:** expanded `RESEARCH_NOTES.md` with the sources, version implications,
  candidate-but-unpinned stack, and open verification gates; corrected memory values;
  updated the risk register for PR #31 and the exact-tag inventory boundary.
- **Validation:** research only. These documents do not establish actual runtime
  compatibility, driver availability for the eventual AMI/kernel, live capacity,
  inference, or GPU performance.
- **Cloud resources/cost:** none created or changed; no billable operation.
- **Next action:** complete source audit and price the full bounded stack; wait for
  PR #31 CI through its existing watcher. No quota request or apply is authorized.

## 2026-11-26 — PR #31 checks completed

- **Phase:** Phase 1; dependency repair is a local non-billable support package.
- **Branch / PR:** PR #31, `codex/fix-baseline-dependency-audit`, commits `e1d9aa0`
  and `9710932`.
- **Checks:** the single `gh pr checks 31 --watch --interval 120` process completed
  successfully. Both workflow runs passed Python, manifests, supply-chain, and
  `local-e2e`; observed run IDs were `45906309837` and `45906313982`.
- **Decision:** mark the change ready for human review now that the repository-required
  implementation clean-room evidence and GitHub checks have both passed. Do not merge
  without the normal approval/review requirements.
- **Cloud resources/cost:** none created or changed; no GPU time and no AWS spend.
- **Next action:** continue Phase 1; PR #30's latest docs-only checks remain on their
  existing watcher.

## 2026-11-26 — Goal registration PR checks completed

- **Phase:** Phase 1 registration documentation; runtime clean-room execution is not
  applicable to this documentation-only PR.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30; goal/research documentation
  current commit will be recorded with this journal update.
- **Checks:** the single `gh pr checks 30 --watch --interval 120` process completed
  successfully. Both workflow runs passed Python, manifests, supply-chain, and
  `local-e2e`; observed run IDs were `45906505681` and `45906511022`.
- **Decision:** PR #30 and PR #31 are both marked ready for review. No merge has been
  performed; the normal approval and PR-only workflow remain in force.
- **Cloud resources/cost:** none created or changed; no GPU time and no AWS spend.
- **Next action:** continue non-billable Phase 1 source audit, official references,
  capacity/price review, and exact bounded-cost design while the PRs await review.

## 2026-11-26 — State and expiry cost-control research

- **Phase:** Phase 1; planning only.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30; no AWS account mutation.
- **Sources consulted:** official HashiCorp S3 backend and state locking guides, AWS
  Session Manager security guidance, S3 pricing page, and EC2 service authorization
  reference.
- **Findings and decision candidates:** use Terraform's versioned, private, encrypted
  S3 backend with native `use_lockfile=true` and a dedicated pay-per-request DynamoDB
  lock table because the repository's `AGENTS.md` requires one per cloud root. HashiCorp
  marks DynamoDB locking deprecated, so test dual-lock behavior and retain the table
  only while that repository policy requires it. Session Manager itself has no
  EC2 connection fee; interface VPC endpoints add hourly/data charges, so the current
  minimum-cost candidate is one public IPv4 with no inbound service rules and outbound
  HTTPS, after recording its egress risk. Treat inbound model/image transfers as free
  only where the applicable AWS price rules say so; the final estimate must include
  S3 state requests/versions, IPv4, EBS, transfer, logs, taxes, and all other actual
  line items, without relying on free-tier eligibility.
- **Expiry candidate:** a boot-scheduled systemd shutdown timer plus EC2
  `instance_initiated_shutdown_behavior = "terminate"` avoids a permanent Lambda or
  broad terminate role. This design is only proposed. Its scheduling, host clock,
  cloud-init failure behavior, volume deletion, and actual instance termination must
  be tested before any GPU batch.
- **Changes:** refined proposed architecture and research notes; updated the risk
  register. No Terraform resource or IAM permission was created.
- **Cost boundary:** current `$9.7309` 12-hour subtotal remains partial (GPU, one
  public IPv4, 100 GiB gp3 only). It is not a complete estimate, cost authorization,
  or apply approval. Current G/VT quota remains zero.
- **Next action:** complete exact price and expiry checklist and static validation of
  the proposed EC2-only root before requesting any paid run or account change.

## 2026-11-26 — Phase backlog and proposed architecture expanded

- **Phase:** Phase 1 — architecture and non-billable preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal`, PR #30; commit `336c1b4` has been pushed
  and its required GitHub checks are running.
- **Starting state:** both PRs #30 and #31 are ready for human review; #31 has passing
  local and CI evidence. No AWS mutation has occurred.
- **Objective:** finish the architecture deliverables required for Phase 1 and make
  the implementation sequence reviewable before any infrastructure work.
- **Changes:** expanded the proposed architecture with the Linux/GPU software stack,
  identity and admission sequence, LLM request execution/KV cache, GPU telemetry, and
  rationale for a single EC2 host instead of EKS. Added the 10-package ordered
  `IMPLEMENTATION_BACKLOG.md` and linked it from the docs index. The backlog records
  dependencies, exit gates, cost boundaries, and the zero-quota blocker.
- **Research used:** official HashiCorp S3-native locking docs, AWS Session Manager and
  S3 pricing guidance, EC2 tag-scoped terminate authorization, EC2 L4 specs, NVIDIA
  CUDA compatibility, current vLLM stable GPU guide, and PyTorch installation docs.
  All architecture is labeled proposed; no diagram is a deployment record.
- **Validation:** `git diff --check` passed before commit. PR #30 CI is the validation
  gate for this documentation-only update. No local model or cloud runtime was started.
- **Cloud resources/cost:** none created or changed; instance-hours remain zero.
  Current partial estimate remains `$9.7309` for 12 hours of instance + IPv4 + sample
  100-GiB gp3 only; it is not a total estimate or authorization.
- **Open items:** remaining API/security source audit, official Docker/Toolkit/DCGM/
  monitoring/MLflow/Redis/evaluation research, complete cost model, exact expiry tests,
  quota gate, and eventual PR reviews.
- **Next action:** finish the remaining code audit and cost analysis before drafting
  any billable plan. Do not raise the GPU quota or apply infrastructure at this stage.

## 2026-11-26 — Container GPU and telemetry research

- **Phase:** Phase 1 research; no package installation or AWS changes.
- **Branch / PR:** `codex/single-l4-gpu-goal`; PR #30's documentation commit `336c1b4`
  is under its existing CI watcher.
- **Sources consulted:** official NVIDIA Container Toolkit install guide; Docker
  Compose GPU device reservation guide; NVIDIA DCGM Exporter release notes and release
  strategy; OpenTelemetry semantic convention writing and GenAI conventions pages.
- **Findings:** install the NVIDIA driver before Container Toolkit; current toolkit
  guide documents `1.20.2-1` and a systemd cgroup reload GPU-visibility issue.
  Compose requires `capabilities: [gpu]` and supports a one-device count but this
  grants device visibility, not GPU partitioning. DCGM Exporter 4.8.4 currently
  reports DCGM 4.6.1 components and distinguishes immutable full image tags from
  mutable `latest`; pin digest and validate actual fields. OpenTelemetry asks for
  explicit opt-in treatment for sensitive/verbose attributes; do not export prompt
  or completion content or credentials by default.
- **Changes:** recorded source/date and implementation implications in
  `RESEARCH_NOTES.md`. The GPU observability architecture remains proposed.
- **Validation:** documentation research only; no exporter, GPU container, telemetry,
  metrics, or alerts were run.
- **Cloud resources/cost:** none; instance-hours remain zero.
- **Next action:** continue remaining official references and source audit; then finish
  an exact total cost and expiry plan before considering any AWS change.

## 2026-11-27 — Phase 1 evidence and cost package completed

- **Phase:** Phase 1 complete as a repository audit/research/architecture gate; Phase 2
  starts with static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal`, PR #30. Its pushed head `336c1b4` has
  passed both required workflow runs; this additional documentation update is not yet
  committed or checked by CI. PR #31 is open and its required checks have passed.
- **Starting state:** documentation edits remained uncommitted after the #30 CI
  watcher ended. Zero AWS resources and zero GPU instance hours for this goal.
- **Objective:** close the source audit and Phase 1 research record, document current
  pricing inputs and evidence boundaries, and define the next static-only package.
- **Changes:** documented concrete API request/stream lifecycle risks, updated the
  official sources for monitoring, evaluation, model license, Terraform, Ansible,
  CUDA profiling, and current OpenTelemetry GenAI conventions; added a cost report and
  evidence manifest; recorded EventBridge Scheduler as the proposed independent
  expiry mechanism paired with guest shutdown. Marked Phase 1 complete and Phase 2
  static-only preparation active.
- **Cost model:** provisional 12-hour estimate is `$18.35`, including 12 hours at the
  2026-11-26 g6.xlarge catalog rate, one IPv4, 100 GiB gp3, temporary S3 state and
  S3/DynamoDB state lock, expiry invocation, a 10x data-egress placeholder, a 25% tax allowance, and a
  `$5` reserve. This is not a quote or authorization. Current G/VT quota is zero.
- **Validation:** official-source review and documentation inspection only; no cloud
  validation or local runtime started. `git diff --check` will be run before commit.
- **Cloud resources/cost:** none created/changed; spend `$0`; instance-hours `0`.
- **Known limitations:** the provisional estimate needs exact AMI, Price List, tax,
  account-level transfer, state-retention, and saved-plan confirmation. The expiry
  mechanism is proposed and not yet implemented or tested. The quota is unchanged.
- **Next action:** finish the static Terraform/expiry design in a focused PR; no AWS
  apply or quota request.

## 2026-11-27 — Repository state-lock policy and cost correction

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30.
- **Starting state:** PR #30 head `80ca94e`; its two workflow runs were still active
  when the repository's state-lock requirement was reviewed.
- **Objective:** align the architecture and cost record with the repository rule that
  the cloud repository has its own DynamoDB lock table and roots use unique state-key
  namespaces, while keeping Terraform's current S3-native lock option documented.
- **Research and decision:** HashiCorp documents that S3 and DynamoDB backend locking
  can be configured together, but marks DynamoDB locking deprecated. The repository
  rule requires a repository-scoped DynamoDB table. A follow-up inspection of the
  actual `AGENTS.md` and existing bootstrap showed that the repository already defines
  this bucket and table. The GPU root will reuse them with a unique state key and
  test the pinned Terraform dual-lock path; it will not create a duplicate table.
  AWS Budgets direct-email alerts require recipient verification and can lag charges;
  they are not a runtime stop control.
- **Changes:** corrected the current rounded 12-hour envelope from `$18.34` to
  `$18.35`, added a small DynamoDB request allowance, documented email-alert
  verification, and updated the proposed state architecture, status, backlog, and
  evidence index. No Terraform resource was created.
- **Validation:** `git diff --check` passed. The existing PR #30 watcher reported
  Python, manifests, supply-chain, and local-e2e passing in both runs; `gh pr checks
  30` confirmed all displayed checks passed at `80ca94e`.
- **Cloud resources/cost:** none created or changed; AWS spend `$0`; GPU instance-hours
  `0`; quota remains `0` vCPUs.
- **Limitations:** estimate remains provisional. Exact price, tax, egress aggregation,
  state lifetime, resource plan, budget recipient verification, and expiry testing
  remain open before any apply.
- **Next action:** finish the static cost/design correction and prepare the isolated
  Phase 2 Terraform root in a separate pull request; keep it static-only.

## 2026-11-26 — Phase 2 single-L4 static root and AWS preview plans

- **Phase:** Phase 2 — isolated EC2 infrastructure, static-only.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended PR #32, based on PR #30 head
  `04cb564`.
- **Starting state:** PRs #30 and #31 remained open; PR #30's latest checks passed.
  This branch contained no Phase 2 Terraform root. Project AWS resources and GPU
  instance-hours were both zero.
- **Objective:** add a reviewable one-L4 root, independent expiry, scoped read-only
  preflight, exact-plan gates, and cleanup verification; produce AWS-backed previews
  without applying resources.
- **Research:** reviewed official Terraform S3 backend guidance, current AWS provider
  `5.100.0` schema, AWS quota/offerings, Canonical Ubuntu AMIs, AWS Systems Manager
  Agent setup, AWS budget notification pricing, and EventBridge Scheduler behavior.
- **Changes:** added a dedicated `gpu-ec2` Terraform root with one `g6.xlarge`, no
  inbound rules, outbound TCP 80/443, IMDSv2, encrypted 100 GiB gp3, scoped SSM and
  expiry roles, a guest `systemd` timer, and a one-time scheduled termination. Added
  account/quota/AZ/resource/bootstrap preflight, plan/apply/destroy scripts with
  checksum checks, a read-only resource-absence verifier, local-only preview plans,
  Make targets, and Phase 2 documentation. Reused the repository-level state bucket
  and DDB lock table under a distinct `gpu-ec2/` key after checking the actual
  `AGENTS.md` rule; created no duplicate table.
- **AWS read-only checks:** the expected account matched. Current On-Demand G/VT quota
  is `0.0` vCPUs. The `g6.xlarge` offering list currently includes `us-east-1a`, `1b`,
  `1c`, `1d`, and `1f`. Offerings do not reserve capacity.
- **Preview results:** the bootstrap local-state preview proposed `7 to add, 0 to
  change, 0 to destroy`; it used `operator@example.invalid` as a placeholder alert
  address. The GPU local-state preview proposed `14 to add, 0 to change, 0 to
  destroy`, exactly one `g6.xlarge`, AZ `us-east-1c`, and Canonical image
  `ami-0a951420c495183dc`. Together these show a preliminary 21-create scope. Plans
  are ignored under `.local/`, are not remote-backend plans, and must not be applied.
- **Validation:** final `make terraform-validate` passed the bootstrap, existing EKS,
  and new GPU roots with backend disabled. `make gpu-ec2-validate`, `bash -n
  scripts/gpu-ec2-*.sh`, and `git diff --check` passed. PR #30 checks passed at
  `04cb564`.
- **Failed attempts and fixes:** Terraform 5.100.0 rejected the optional
  `action_after_completion` argument; kept the pinned provider and rely on Terraform
  destroy to remove the non-recurring schedule. An HCL multi-line expiry expression
  needed parentheses. `terraform console` requested backend initialization and did
  not render the cloud-init file. The first `terraform show` command ran from the
  source root and could not load the plan copy's provider schema; rerunning `show`
  from `.local/gpu-ec2-preview` succeeded and listed all 14 create addresses. These
  failed commands changed no AWS resources.
- **Financial boundary:** preliminary estimate remains `$18.35`, below the `$25`
  ceiling but not an authorization. AWS Budgets notifications are free without
  actions, but email verification is required for alerts. No apply or quota request
  was made; AWS spend is `$0` and GPU hours are `0`.
- **Limitations:** previews omit remote locking and state bootstrap relationships,
  do not prove Scheduler or guest-timer behavior, and do not reserve capacity. The
  placeholder budget recipient is not usable. A final remote-state plan, exact price
  and tax confirmation, and expiry tests remain outstanding.
- **Next action:** finish static review, create and monitor the focused PR, then
  prepare the full cost/plan review. Request 4 vCPUs only after that is ready; do not
  apply while quota is zero.

## 2026-11-26T23:57Z — Final static checks and cloud-init template evidence

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended stacked PR #32 based on PR #30.
- **Starting state:** Terraform, scripts, and documentation were present but
  uncommitted. PRs #30 and #31 remained open. No Terraform mutation or quota request
  had been made.
- **Objective:** verify the latest cloud-init change, preserve the correct preview
  evidence, and run the complete static validation before opening the PR.
- **Commands and results:** `make gpu-ec2-validate` passed; `make terraform-validate`
  passed for bootstrap, the existing EKS root, and the GPU root; `bash -n
  scripts/gpu-ec2-*.sh` passed; `git diff --check` passed. A backend-free local copy
  rendered `cloud-init.yaml.tftpl`; Ruby YAML safe parsing succeeded using
  `YAML.safe_load(File.read(...))`. The prior `safe_load_file` method was unavailable
  in the installed Ruby and was replaced with the supported API.
- **Preview evidence:** the revised AWS-backed local-state GPU plan has SHA-256
  `a91226c5be150e1972e9351c843837c0004d54f19072684389a1c035facdef5d` and proposes
  14 creates. The bootstrap preview proposes 7 creates and has SHA-256
  `e1cd8a88e803b8cd15c1dd20fc9896aba03ffe40013d879cd6aff5928f69aaed`. The plans are
  local previews with the S3 backend removed; neither is suitable for apply.
- **Changes:** updated the validation record, ticket, and evidence manifest to
  distinguish successful static rendering/YAML parsing from unverified real-host
  cloud-init, SSM registration, and expiry behavior.
- **Cloud resources and cost:** no resources created or changed; AWS spend `$0`; GPU
  instance-hours `0`; G/VT quota remains `0` vCPUs; no quota request submitted.
- **Limitations:** no quota approval, remote-state plan, capacity guarantee, instance,
  GPU, or guest behavior has been verified. The first project bootstrap still needs
  private operator email input before its budget alert can be applied.
- **Next action:** complete the diff review and open PR #32 against the PR #30 branch;
  continue non-billable work while PR checks run. Keep quota and apply gates closed
  until exact plan, cost, and expiry controls are ready.

## 2026-11-27T00:00Z — Enforced account guard and refreshed preview

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended stacked PR #32 based on PR #30.
- **Objective:** ensure Terraform's account and AZ guards stop operations rather than
  merely warn, then produce a preview from the final source.
- **Issue found:** Terraform `check` blocks are diagnostic checks, not a sufficiently
  strong control for an account boundary or instance-launch condition.
- **Change made:** configured AWS provider `allowed_account_ids` in both the new GPU
  root and its prerequisite bootstrap root. Moved the G6 AZ-offering test into an
  `aws_instance` lifecycle precondition. The account identity remains a data source
  for the expiry-role trust policy.
- **Validation:** `make gpu-ec2-validate`, `make terraform-validate` (bootstrap,
  existing EKS root, GPU root), shell syntax checks, and `git diff --check` passed.
- **Read-only preview:** the source-updated AWS-backed local-state GPU plan proposed
  `14 to add, 0 to change, 0 to destroy`. It selected one `g6.xlarge` in `us-east-1c`
  and Canonical Ubuntu AMI `ami-0a951420c495183dc`. SHA-256 is recorded in
  `EVIDENCE_MANIFEST.md`; the plan is not remote-state-backed or apply-ready. No cloud
  resource was created or changed.
- **Cost and quota:** spend remains `$0`, GPU instance-hours `0`, G/VT quota `0` vCPUs;
  no quota request was submitted. The plan is not an authorization to spend.
- **Next action:** finish reviewing staged source and documentation, then create PR
  #32 against the PR #30 branch. Keep quota and apply gated on the exact remote plan,
  refreshed cost review, expiry proof, and the existing `$25` maximum.

## 2026-11-27T00:03Z — User-directed G/VT quota request

- **Phase:** Phase 2 — static infrastructure preparation; no paid resources.
- **Branch / PR:** `codex/gpu-ec2-foundation`, commit `8f3bb44`; PR #32 was being
  prepared against PR #30's branch.
- **Instruction:** the user asked to request quota immediately while non-billable
  engineering continued.
- **Pre-request verification:** ran the required
  `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity`; the account matched
  the expected project account. Read the `L-DB2E81BA` applied quota (0 vCPUs) and
  request history (no existing requests) before submitting. No credentials were
  recorded.
- **Action and result:** submitted an account-level request for 4 On-Demand G/VT vCPUs
  in `us-east-1`, enough for the planned single `g6.xlarge`. Request ID:
  `34647c8598cb4ac5a8e43b3e956ccd65ikyKx4Qy`. AWS accepted the request and reports
  `PENDING`; an independent `get-requested-service-quota-change` query confirmed the
  status immediately after submission.
- **Financial/security boundary:** this is a quota control-plane request, not an EC2
  launch. Applied quota remains 0, no infrastructure was created or changed, no GPU
  hours accrued, and recorded project spend remains `$0`. The `$25` ceiling and the
  exact-plan/apply approval gate remain in force.
- **Next action:** record this request in PR #32, create the focused stacked PR, and
  continue the remote plan, price, expiry, teardown, and non-billable work while AWS
  reviews the request.

## 2026-11-27T00:06Z — Phase 2 pull request opened

- **Phase:** Phase 2 — static-only infrastructure foundation.
- **Branch and commits:** `codex/gpu-ec2-foundation`; `8f3bb44` adds the root and
  safeguards; `80d0d47` records the quota request and evidence.
- **Pull request:** [#32 — guarded single-L4 EC2 foundation](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/32), opened as a draft against PR #30's `codex/single-l4-gpu-goal` branch.
- **CI state:** both repository CI workflow runs started. At the last read-only PR
  query, Python, supply-chain, and local-e2e checks were running; one manifests check
  had passed. The other manifests check was still running.
- **Quota:** the 4-vCPU request remains `PENDING`; applied quota remains zero. The
  request ID and pre-request verification are indexed above.
- **Cloud cost:** no Terraform apply or other infrastructure mutation; AWS spend
  remains `$0`, and GPU instance-hours remain `0`.
- **Next action:** allow the single PR-check watcher to reach terminal state, resolve
  any failures, and continue the remote-state/cost/expiry preparation while AWS
  processes the quota request.

## 2026-11-27 — Resolve PR #32 script review findings

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32, stacked on PR #30.
- **Starting state:** PR #32's review identified that the plan/apply parent processes
  did not inherit the profile default set by their child preflight, and that the
  teardown verifier enumerated Scheduler schedules even when their group was absent.
  AWS confirms the requested 4-vCPU quota change remains open (`CASE_OPENED`); applied
  quota is still zero. No GPU instance or infrastructure exists from this goal.
- **Changes:** plan/apply now export `AWS_PROFILE` before preflight, defaulting to
  `ai-platform-pilot-key` and preserving an explicit profile. The cleanup verifier
  now skips schedule enumeration when its group is already absent. Added subprocess
  tests with fake AWS/Terraform binaries to check profile propagation and the missing
  group path.
- **Validation:** first lint attempt found import ordering, an unused import, and a
  datetime style issue in the new test; Ruff auto-fixed these. `make verify` then
  passed Ruff, 52 tests, the dependency audit, and Compose configuration. All 52 tests
  passed with one existing Starlette deprecation warning. `bash -n` for the three
  changed scripts and `git diff --check` passed.
- **Cloud / cost:** only read the AWS caller identity and quota request history; did
  not request a duplicate, run Terraform, or create/change AWS resources. Spend and
  L4 instance-hours remain `$0` and `0` in this goal.
- **Evidence limits:** fake CLI subprocess tests prove local wrapper branching and
  environment propagation only. They do not prove actual AWS authentication,
  Scheduler behavior, infrastructure deployment, or clean teardown.
- **CI duplication observed:** publishing the same PR head created two workflow runs
  (`45928736210` and `45928742151`) because this branch's workflow still ran on both
  branch pushes and pull requests. Both have passed Python, manifest, and supply-chain
  checks; their local-e2e jobs were pending at the last check. The workflow trigger is
  now restricted to pushes to `main` plus all pull requests so future branch updates
  produce one PR workflow. These are automated fresh-runner jobs, not the project's
  final end-to-end AWS/GPU clean-room reproduction.
- **Research update:** AWS's one-time schedule documentation confirms an `at(...)`
  schedule continues to count against schedule quota after it fires, until deleted.
  The pinned AWS provider schema does not support automatic deletion after completion,
  so the runbook must require Terraform destroy to remove the schedule and must not
  claim that expiry removes it.
- **Next:** validate the workflow YAML and research note, then publish them to PR #32
  after the currently running checks reach terminal state. Observe the one subsequent
  PR-triggered workflow and update the evidence manifest.

### Follow-up outcome

- PR #32 head `528b52c` passed all four required jobs in the single PR-triggered
  workflow `45929546262`. Evidence is indexed in `EVIDENCE_MANIFEST.md`; the PR
  description has been updated. Human review remains open.
- During a read-only tag audit, direct inspection confirmed `versions.tf` configures
  provider-level `default_tags = local.required_tags`, so supported resources receive
  project/environment/owner/expiry tags even when a resource block only adds `Name`.
  AWS provider documentation confirms tags for VPCs, subnets, IAM roles, and Scheduler
  groups. No source change was needed.
- A `terraform providers schema -json` attempt from the configured S3-backend root
  stopped with “Backend initialization required.” Running `init -backend=false` and
  `-reconfigure` succeeded, but the schema command still rejected the configured
  remote-backend root. No AWS backend call, plan, or state access occurred. The
  provider-level default-tag configuration was verified from source instead.
- The AWS quota request currently reports `CASE_OPENED`; the applied quota remains
  zero. No AWS resource was created or changed, and goal-specific spend remains `$0`.
- **Next:** continue Phase 2 non-billable cost and remote-state preparation while
  preserving the exact-plan and apply authorization gates. Track the open review and
  quota request without submitting a duplicate or launching infrastructure.
- The status and backlog refresh was published as head `d3cee0f`; its one PR-triggered
  workflow `45930498661` passed Python, manifests, supply-chain, and local-e2e. The
  evidence manifest and PR description record that result. The AWS request is still
  `CASE_OPENED`; no infrastructure was launched.

## 2026-11-27 — Expand EC2 fail-closed tests and recheck account inventory

- **Phase:** Phase 2 — static-only EC2 infrastructure and non-billable validation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; code commit `7988b8f` is local
  and awaits publication with its documentation update.
- **Changes:** added fake-CLI tests that verify preflight stops on a wrong account or
  insufficient G/VT quota; apply refuses before AWS/Terraform if the operator has not
  set `GPU_EC2_CONFIRM=apply`; and a modified plan fails checksum review before cloud
  preflight. Together with earlier tests, six fail-closed cases cover the wrapper and
  cleanup paths.
- **Validation:** `make verify` passed Ruff, 56 tests, pip-audit, and Compose config.
  One existing Starlette deprecation warning remains. Bash syntax and `git diff
  --check` passed. The first lint issue was resolved earlier in this package; no new
  lint failures occurred.
- **AWS state reconciliation:** verified the caller matches the expected project
  account in `us-east-1`; the account number is omitted from this public journal.
  Exact project-tag Resource Groups and EC2 queries returned no resources
  or non-terminated GPU instance. S3 `HeadBucket` returned 404 for the expected state
  bucket; DynamoDB returned `ResourceNotFoundException` for the expected lock table;
  the exact project budget query returned no budget. This confirms the bootstrap
  guardrails are not present yet. No API mutation was made.
- **Quota and cost:** the 4-vCPU request is already open (`CASE_OPENED`); applied quota
  remains zero. No duplicate request, Terraform plan/apply, resource, GPU hour, or
  goal-specific spend was created.
- **Next:** publish code plus records to PR #32; let its single PR workflow validate
  the current head. Continue preparing the remote-state and full-cost gates without
  applying the bootstrap or GPU roots.

## 2026-11-27 — Verify destroy-plan authorization gates locally

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; teardown tests are committed at
  `ca3706b` and docs are being prepared before publication.
- **Changes:** added fake-CLI tests proving the destroy wrapper refuses missing
  explicit confirmation, altered destroy-plan bytes, and an unexpected AWS account
  before Terraform. A positive fake command test verifies the plan helper calls
  `terraform plan -destroy` and stores its output only in the test's temporary path.
- **Validation:** `make verify` passed Ruff, all 60 tests, dependency audit, and Compose
  configuration. Shell syntax checks passed for all six `gpu-ec2` helper scripts, as
  did `git diff --check`. One existing Starlette deprecation warning remains.
- **Cloud / cost:** tests replace `aws` and `terraform` in `PATH` with local stubs.
  They make no AWS API calls and cannot create or destroy resources. No GPU hours or
  goal-specific spend were added.
- **Next:** publish this test package and its evidence; observe the single PR-triggered
  CI workflow. Keep actual bootstrap and GPU changes gated by approval, quota, exact
  cost, saved plan, and expiry controls.

## 2026-11-27 — Verify baseline resource scope and cleanup output

- **Phase:** Phase 2 — static infrastructure preparation; no GPU infrastructure has
  been created by this goal.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; verifier scope correction is at
  `11d2e6e`.
- **Discovery:** the verifier's generic success message said shared repository state
  and budget controls were “intentionally retained,” but live read-only checks showed
  the expected state bucket, lock table, and budget do not exist yet. The GPU verifier
  never queried them. Changed its message and test to state clearly that shared state,
  locks, and budget guardrails are outside its scope and are neither checked nor
  modified by this script.
- **AWS baseline check:** ran the read-only verifier against the expected account in
  `us-east-1`. It exited 0 and reported no non-terminated project instance, tagged
  volume/network resource, snapshot, expiry IAM role/profile, or Scheduler resource.
  This is an initial pre-provision baseline, not proof of post-destroy cleanup.
- **Partial command observation:** the first invocation returned only the first seven
  lines at the command tool's 10-second boundary and did not return its exit code. A
  process check found no verifier still running; the standalone NAT-gateway query
  returned empty successfully. Re-ran the full verifier with a longer bound and
  captured all checks and exit code `0`.
- **Validation:** after the wording change, `make lint` and `make test` passed (60
  tests, one existing Starlette deprecation warning); Bash syntax and `git diff
  --check` passed. The AWS verifier itself remains read-only.
- **State/cost:** exact project-tag inventory remains empty. Separate calls show the
  shared state bucket, DynamoDB lock table, and budget are absent, so the preflight
  correctly blocks until bootstrap resources are established. No cloud resource or
  cost was created.
- **Next:** publish the verifier correction, test, and truthful baseline record with
  the current PR package. Keep this baseline clearly distinct from future teardown
  evidence.

## 2026-11-27T00:20Z — Local vLLM streaming and cancellation package

- **Phase:** local prerequisite work for Phase 6; Phase 2 remains the active cloud
  phase. No AWS resource or GPU was used.
- **Branch / parent:** `codex/gateway-stream-accounting`, initially based on PR #32
  commit `24336cf`; it was later rebased onto PR #32 head `da2567e`.
- **Objective and changes:** close the audited vLLM streaming usage/TTFT gaps before
  live inference. The adapter requests/parses the final usage event; the gateway
  supports client `stream_options`, records measured versus estimated usage, measures
  first-content delay, and records terminal cancellation/error outcomes once.
- **Setup failures retained:** `.venv` and the ignored ONNX fixture were absent. The
  first Ruff command failed because its binary did not exist; the first test collection
  failed because the fixture was absent. Installed editable dependencies and generated
  the ignored fixture. A test initially expected bytes although this direct response
  iterator yielded strings; corrected the assertion. The first fake Redis pipeline also
  omitted a positional `hset` form and failed before its target assertion; updated the
  fake to model both forms.
- **Earlier validation snapshots:** the initial package reached 5 targeted/55 full
  tests; subsequent usage-option checks reached 7/57; the stream-failure case reached
  8/58. Each snapshot had one existing Starlette deprecation warning. These are retained
  as history; later validation is recorded below.
- **Evidence boundary:** vLLM used `httpx.MockTransport`; cancellation used the local
  in-memory limiter. No real vLLM server, Redis recovery, or GPU behavior was tested.
- **Quota/cost:** the 4-vCPU request remained pending; applied quota remained zero. No
  infrastructure mutation, GPU hours, or AWS spend occurred.

## 2026-11-27T00:25Z — PR #33 implementation committed

- **Original implementation commit:** `1186e30` (`fix: preserve vLLM stream usage and
  cancellation`), later replayed during rebase as `130bddd`.
- **PR:** #33 was opened against PR #32's `codex/gpu-ec2-foundation` branch. The PR
  branch was later rebased onto PR #32 head `da2567e` to preserve the stack.
- **Validation at that point:** Ruff passed; targeted tests reported 8 passed and the
  full suite reported 58 passed with one existing warning. Later review-fix validation
  is recorded below.

## 2026-11-27 — PR #32 latest checks and PR #33 review fixes

- **PR #32:** the single watcher reached terminal success for head `da2567e`; run
  `45933749318` passed Python, manifests, supply-chain, and local-e2e.
- **PR #33 findings:** in-band vLLM error events after HTTP 200 were silently ignored;
  string-yielding backends omitted final usage when clients requested it. Both issues
  were fixed. Error frames now fail the backend stream; estimated usage is emitted once
  when the backend has no measured usage.
- **Current validation:** targeted streaming suite **10 passed**; `make verify` passed
  Ruff, **60 tests**, pip-audit with no known vulnerabilities, and Docker Compose
  validation, with one existing Starlette/httpx warning.
- **Rebase and publication:** PR #33 was rebased on PR #32 head `da2567e`; source and
  tests are in `635f61d`. The force-with-lease push succeeded. Checks on the new PR head
  are still pending; one watcher will be used.
- **Cloud boundary:** no vLLM server, Redis, AWS mutation, or GPU was used. Goal spend
  remains `$0`; GPU hours remain `0`; quota and apply gates are unchanged.

## 2026-11-27 — NVIDIA, vLLM, and model compatibility candidate

- **Phase:** Phase 1 official research supporting Phase 3; no cloud or GPU execution.
- **Branch / PR:** `codex/gpu-software-compatibility`, prepared on the PR #32 foundation
  branch at `da2567e`; PR #37 is not yet open.
- **Starting state:** worktree clean; quota request `34647c8598cb4ac5a8e43b3e956ccd65ikyKx4Qy`
  still `CASE_OPENED`, with applied G/VT quota 0 vCPUs. PR #36's existing CI watcher
  session `5600` was live; run `45938690893` had manifests and supply-chain passed,
  Python passed, while local-e2e remained pending.
- **Objective:** replace moving dependency references with current official release
  evidence and identify a verifiable model artifact before preparing the one bounded
  GPU batch.
- **Research and commands:** checked NVIDIA's R580.196.11 release notes, driver/CUDA
  matrix, and Ubuntu installation guide; checked vLLM v0.34.0 release, L4 GPU
  requirements, and supported model table. Queried `docker buildx imagetools inspect
  vllm/vllm-openai:v0.34.0` and recorded the registry index and AMD64 digests.
  Queried Hugging Face's public model page/API using `python3` for revision, license,
  model config, tokenizer metadata, size, and LFS SHA-256. No image layers or model
  files were downloaded.
- **Minor failed command:** invoking the Python query with `python` failed because
  this host exposes `python3` only; the same read-only query then completed with
  `python3`. This changed the command only and did not affect environment state.
- **Finding:** R580.196.11 / CUDA 13.0 / vLLM 0.34.0 / Qwen2.5-1.5B is an official-doc
  candidate for Ubuntu 24.04 x86_64 and L4, but not proven on EC2. The model's
  `config.json` reports 32,768 positional embeddings while tokenizer metadata reports
  131,072 max length; use a conservative context until RoPE and runtime behavior are
  checked. The exact package repository versions and host kernel remain open.
- **Changes:** added the dated compatibility matrix and source links to
  `RESEARCH_NOTES.md`; added ticket37 with digests, model provenance, unresolved
  checks, and clear no-execution status; added the research package to the backlog.
- **Validation:** public metadata queries succeeded; no model weights, GPU image,
  container, or cloud resource was started. Diff review and documentation checks are
  pending.
- **AWS/cost:** no mutations; 0 GPU hours; no AWS resource or spend. No quota request
  was repeated.
- **Next:** validate documentation formatting, commit the focused research package,
  push its branch, open PR #37 against PR #32, and let its required checks reach a
  terminal state. Continue using the existing PR #36 watcher only.

## 2026-11-27 — Quota denial and support-path investigation

- **Phase:** Phase 2 remains static-only; GPU execution is blocked.
- **Starting state:** PR #38 head `5256060` is under its one active CI watcher. No GPU
  resources exist or were created. The existing quota request ID is recorded in the
  project ledger; do not create another request.
- **New evidence:** the owner provided an AWS email stating that the 4-vCPU On-Demand
  G/VT quota increase was denied and that the case may be reopened with a detailed use
  case. A read-only Service Quotas history query still reports `CASE_OPENED` for the
  same request; the applied quota remains `0.0`. Treat the email as the denial notice
  and the API status as inconsistent until reconciled.
- **Commands / checks:** queried Service Quotas request history and applied quota in
  `us-east-1`; checked the applied G/VT quota and `g6.xlarge` regional offering in
  `us-east-2` and `us-west-2`. All three regions report zero applied quota; G6 is
  offered in each, which does not prove AZ capacity. A read-only AWS Support
  `describe-cases` call failed with `SubscriptionRequiredException`; no support case
  or quota request was created or changed.
- **Research:** AWS states that a denied quota request should be taken to Support and
  that resolved cases can be reopened through the Support Center console. The account
  profile cannot use the Support API. Official references are in
  [`QUOTA_APPEAL_DRAFT.md`](QUOTA_APPEAL_DRAFT.md).
- **Alternatives considered:** checked two other US regions; their applied quotas are
  also zero, so switching regions alone does not solve the issue. No alternative GPU
  family is allowed by project constraints. A duplicate quota request is unsafe while
  the existing request still appears open.
- **Changes:** created a sanitized appeal draft with the single-instance use case,
  four-vCPU request, hard $25 ceiling, 8–12 hour target, private access, automatic
  expiry, and teardown safeguards. The draft has not been submitted.
- **Next action:** keep non-billable repo work moving. The owner must reopen the
  existing case from AWS Support Center if they choose to appeal; no GPU launch is
  possible until the quota is approved and the cost/apply gates pass.
- **Cost:** no AWS resources, GPU hours, or charges were created.

## 2026-11-27 — Refresh the pinned-AMI local-state preview

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation; quota blocks apply.
- **Branch / PR:** `codex/refresh-gpu-ec2-preview`, preparing PR #42 on top of PR #41.
- **Starting cloud state:** verified the AWS account with the key profile. Latest
  read-only quota checks show applied On-Demand G/VT quota `0.0`; the existing
  request still says `CASE_OPENED`, despite the denial email. The attempted Support
  CLI communication was rejected before sending. No project resources exist.
- **Objective:** refresh the EC2 local-state plan after pinning the exact Ubuntu AMI
  and review its resource count and security properties without applying it.
- **Execution:** `scripts/gpu-ec2-preview-plan.sh` ran with `g6.xlarge`,
  `us-east-1c`, the reviewed Canonical Ubuntu 24.04 amd64 AMI, and an exact six-hour
  expiry. It verified caller account and AZ offering, copied the Terraform root,
  removed only the S3 backend block in that preview copy, and produced a local-state
  saved plan. Plan digest:
  `d33721981fdeaec4b513d3a738553c155423d50aa8bb7851c31ef0c5da70bd44`.
- **Plan review:** 14 creates, zero changes, zero destroys. Exactly one `g6.xlarge`;
  IMDSv2 required; root volume is 100 GiB, encrypted gp3, delete on termination;
  security group has no inbound rules and outbound TCP 80/443. A public IPv4 is
  associated so the host can use public internet egress without a NAT Gateway.
- **Plan limitations:** this local-state preview has no remote lock, does not run the
  quota preflight, cannot establish account capacity, and must not be applied. The
  raw plan remains under ignored `.local/` and was not added to Git. Terraform's
  `applyable=true` is metadata, not authorization or proof of safe applicability.
- **Troubleshooting:** an initial `terraform show -json` from the repository root
  could not load the provider schema. Running it from the initialized preview copy
  succeeded. A first filtered parser assumed object-shaped metadata and failed on
  Terraform's list-shaped JSON; correcting the parser produced the security summary.
- **Cost:** plan-only; no AWS resource, GPU hour, or spend was created. It does not
  recalculate the full project estimate.
- **Next:** submit the sanitized plan review in PR #42; continue work on shared remote
  state, current cost assumptions, expiry safeguards, and runtime preparation without
  paid GPU infrastructure.

## 2026-11-27 — Record manual appeal report and remote-lock test coverage

- **Phase:** Phase 2 — static EC2 preparation; GPU execution remains blocked.
- **Branch / PR:** `codex/test-dual-terraform-locks`, preparing PR #43 on top of PR #42.
- **Starting state:** PR #42's four required checks passed in run `45977824955`. The
  owner reports manually submitting the appeal through the existing AWS Support
  Center case. Read-only quota history remains `CASE_OPENED`, applied quota is `0.0`,
  and the connected email search has no newer reply.
- **Objective:** record the appeal status without resubmitting it and add regression
  coverage for Terraform state-lock configuration.
- **Changes:** documented the owner-reported appeal in the goal, status, research,
  appeal record, and ticket #41. Added fake-Terraform assertions that the plan and
  destroy-plan wrappers pass both S3 lockfile and DynamoDB lock arguments to `init`.
- **Validation:** focused script tests passed (14 tests), Ruff passed, and
  `git diff --check` passed. These tests prove argument wiring only; actual remote
  lock acquisition, contention, and release remain untested. The first `make verify`
  attempt could not start because this worktree had no `.venv`; using the existing
  project virtual environment then exposed absent generated CPU ONNX fixtures. After
  creating both expected local fixtures with `scripts/create_model.py`,
  `make VENV=<existing-project-virtualenv-path> verify` passed Ruff, 72 tests,
  pip-audit, and Docker Compose configuration. The model files are generated local
  fixtures and are not part of this change.
- **Cloud and cost:** read-only status only; no support message, AWS mutation, resource,
  GPU hour, or project spend was created during this work.
- **Next:** publish PR #43, then prepare a consolidated GPU execution runbook covering
  manual host setup, inference, metrics, experiments, evidence export, and teardown.
  Runtime commands remain unverified until an authorized GPU run occurs.

## 2026-11-27 — Prepare GPU batch runbook and reconcile read-only AWS state

- **Phase:** Phase 2 static preparation; planning Phase 3–10 GPU work in one batch.
- **Branch:** `codex/gpu-batch-readiness`, based on PR #43 head `4e62876`.
- **Objective:** pre-stage future GPU work and confirm the cloud is safe to wait for
  quota approval.
- **Research:** checked official NVIDIA Ubuntu driver/CUDA installation guides,
  NVIDIA Container Toolkit installation, PyTorch CUDA installation and verification,
  and vLLM GPU/Docker deployment. Recorded the headless driver path, the normal CUDA
  13/R580-or-newer vLLM driver requirement, and the need to recheck exact packages on
  the execution date.
- **AWS reads:** verified the key profile's expected account without copying its
  identifiers into evidence; applied G/VT quota remains `0.0`. Exact project-tag EC2
  and Resource Groups Tagging API queries returned no project resources. All calls
  were read-only.
- **Changes:** drafted `GPU_BATCH_RUNBOOK.md` with prerequisites, a ten-hour planning
  ceiling, manual host setup, manual vLLM first run, tenant/telemetry checks,
  benchmark/evaluation, stop conditions, evidence export, and teardown. Commands are
  labeled as planned and unexecuted.
- **Cost:** no infrastructure, GPU hour, or spend.
- **Next:** validate and publish PR #44; continue preparing scripts and datasets
  locally while quota and the Support Center response remain pending.

## 2026-11-27 — PR #44 published

- **Branch / PR / commit:** `codex/gpu-batch-readiness`, PR #44 against PR #43,
  initial head `868e11d`.
- **Checks:** CI is pending; no AWS changes or GPU hours.
- **Next:** finish recording this publication and wait for the existing PR #43 and
  #44 CI runs, then continue non-billable code readiness work.

## 2026-11-27 — PR #43 and #44 checks passed

- PR #43 head `4e62876`: run `45979618437` passed Python, manifests, supply-chain, and
  local end-to-end checks.
- PR #44 head `02247c8`: run `45980633787` passed the same four required checks.
- Both PRs remain open for human review. No AWS or GPU execution occurred.
- Continue static deployment integration in PR #45.

## 2026-11-27 — Build the opt-in single-L4 Compose runtime path

- **Phase:** static preparation for Phases 5, 6, and 11; no GPU execution.
- **Branch:** `codex/single-l4-compose-deployment`, based on PR #44 head `02247c8`.
- **Objective:** connect the existing gateway vLLM adapter to a standalone EC2 Compose
  profile while keeping the CPU ONNX path as the default.
- **Changes:** added an opt-in catalog target/model ID, single-GPU Compose profile,
  candidate image/model env file, and readiness checks for the selected backend and
  shared capacity state. The Compose file exposes only loopback gateway ports; vLLM
  and Redis are private to the Compose network. Added `make gpu-compose-config` to
  the standard verification target.
- **Validation:** `make VENV=<existing-project-virtualenv-path> verify` passed Ruff,
  76 tests (one existing Starlette deprecation warning), pip-audit with no known
  vulnerabilities, and both base/GPU Compose config checks. Nine focused tests also
  passed for catalog defaults/profile, unhealthy vLLM readiness, and the API health
  endpoint. `git diff --check` passed.
- **Cloud/cost:** no image pull, GPU allocation, AWS write, instance hour, or spend.
- **Limitations:** simulated Redis capacity remains a logical accounting mechanism.
  This profile has no DCGM exporter yet and has not run against actual GPU hardware.
- **Next:** finish full verification, publish PR #45, and continue GPU observability
  and benchmark preparation in separate packages.

## 2026-11-27 — Add safe capacity-demo CI diagnostics

- **Phase:** Phase 2 static deployment prep; no cloud or GPU execution.
- **Branch / PR / commit:** PR #45 branch `codex/single-l4-compose-deployment`,
  commit `2688d48`, pushed to PR #45.
- **Starting state:** PR #45's fixed smoke check passes. The cumulative local CPU
  `demo-capacity` demo failed in runs `45983777135` and `140460013629`; the PR #46
  workflow also failed in the same script. The scripts used bare `test` / `jq` checks,
  so CI did not identify which request or expected status failed.
- **Change:** the capacity demo now tracks its current stage and, on error, prints each
  captured HTTP status plus a restricted JSON summary of error, capacity decision, and
  usage fields. It does not print bearer tokens, prompts, generated text, or full
  response bodies.
- **Validation:** `bash -n scripts/demo-capacity.sh` passed. The script itself was
  not run locally because it calls `FLUSHDB` on the project Redis service. CI must
  establish the actual failure cause and verify that diagnostics are sufficient.
- **Cloud and cost:** none. This only changes local CPU demo diagnostics.
- **Next:** push to PR #45, run its existing CI once, inspect the new failure detail,
  and fix the underlying issue if confirmed. CI has not yet been checked for this
  head at the time of this entry; the observability branch must rebase onto this head.


## 2026-11-27 — Fix stale capacity snapshot assertion

- **Phase:** Phase 2 static deployment preparation; local E2E is CPU-only.
- **Branch / PR:** `codex/single-l4-compose-deployment`, PR #45.
- **Starting state:** CI run `45988603667` on head `65e5cba` passed smoke, then failed
  at the capacity demo's administrative snapshot check. The diagnostic reported that
  the preceding search quota request returned 429 as expected, search and payments
  requests returned 200, and the analytics CPU fallback returned 200.
- **Root cause:** the capacity API returns `mode: SIMULATED_HARDWARE_QUOTA_ACCOUNTING`
  and the pools list; the demo checked an obsolete `hardware: SIMULATED` property.
  This was a stale assertion, not a GPU failure.
- **Change:** updated the demo to compare the returned `mode` and pool slot count. The
  snapshot body/status are now stored in the temporary diagnostic directory, so a
  future failure can report the relevant fields.
- **Validation:** `bash -n scripts/demo-capacity.sh` and `git diff --check` passed. The
  demo was not run locally because it executes Redis `FLUSHDB`; a fresh GitHub Actions
  run is needed to verify the assertion and reveal any later queue-path failure.
- **Cloud and cost:** no AWS operation, GPU, model, or spend.
- **Next:** push this correction and watch its one PR #45 run. After it passes, rebase
  PR #46 and the benchmark preparation branch onto the updated PR #45 head.

## 2026-11-27 — Confirm PR #45 capacity fix in CI

- **Phase:** Phase 2 static deployment preparation; CI exercised the existing local
  CPU-only stack, not a GPU.
- **Branch / PR / commit:** `codex/single-l4-compose-deployment`, PR #45, `31348c3`.
- **Starting state:** the stale capacity mode assertion was fixed and pushed. CI run
  `45990929878` was watched once using `gh pr checks 45 --watch --interval 120`.
- **Result:** all four required checks passed: local E2E (5m11s), manifests, Python,
  and supply-chain. The capacity demo including its queue path passed in local E2E.
- **Evidence:** run `45990929878`; sanitized cause and result are recorded in
  `docs/tickets/ticket45.md`.
- **Cloud and cost:** no AWS resources, GPU runtime, model download, or spend.
- **Next:** rebase the observability branch onto `31348c3`, validate it and its CI,
  then rebase the benchmark branch onto the updated observability head.

## 2026-11-27 — Prepare static GPU observability profile

- **Phase:** Phase 7 preparation; static configuration only. Live GPU observability
  remains unvalidated until an authorized L4 execution.
- **Branch / parent:** `codex/gpu-observability-profile`, based on PR #45 head
  `bb9ad9c`; PR #46 has not yet been created.
- **Starting state:** PR #45 smoke fix was pushed. Workflow `45983777135` passed the
  smoke step but failed inside the pre-existing cumulative CPU `demo-capacity` script.
  Rerunning only the failed job (`140460013629`) failed at the same script. The log
  does not reveal which internal request/assertion failed. We did not run the script
  locally because it begins with Redis `FLUSHDB`, which would destroy local project
  state.
- **Objective:** prepare the single-GPU profile's metrics, logs/traces, alerting, and
  dashboards using current official component docs and release-pinned images, without
  starting services or incurring cloud cost.
- **Changes:** added DCGM, Node, and Redis exporters; Prometheus; Grafana; Alertmanager;
  OpenTelemetry Collector; Tempo 3; five lab warning rules; and a focused GPU/inference
  dashboard. Monitoring ports are loopback-only where published; exporters and model
  services remain internal. DCGM profiling fields and `SYS_ADMIN` are not enabled.
  The DCGM exporter and vLLM both see the same physical GPU; the reservation does not
  isolate devices. Monitoring data is ephemeral and must be exported before stopping.
- **Validation:** `make gpu-compose-config` passed without starting services.
  `make gpu-observability-validate` passed: Prometheus 3.16.0 validated the actual
  mounted scrape config and found five alert rules; Alertmanager 0.35.0 validated its
  actual mounted config; Tempo 3.1.1 verified its actual mounted config; OpenTelemetry
  Collector Contrib 0.166.0 validated the profile-specific privacy-filtering config;
  both dashboard JSON files parsed; Compose config parsed; Bash syntax and `git diff
  --check` passed. The dedicated GitHub Actions job and `make verify` target are now
  wired to rerun the same validators. System Python lacked PyYAML; the system Ruby YAML parser rejected
  valid flow endpoint lists in Compose/Prometheus, which were instead checked by their
  native parsers. Four config-validator images were downloaded into local Docker
  cache; no profile containers were started.
- **Research:** reviewed NVIDIA DCGM exporter installation, metrics fields and v4.9
  unit/name changes; vLLM current V1 metric names; Prometheus scrape configuration;
  Node Exporter setup; Tempo 3 migration; and official release manifests. The release
  digests are recorded in the PR ticket; they must be rechecked at run time.
- **Failures and troubleshooting:** first Tempo config verification exposed invalid
  compaction nesting; corrected to the schema accepted by Tempo 3.1.1. A generic YAML
  check also failed because the available Ruby parser is old and not Compose-aware.
  Initial PR #45 smoke check was corrected separately; later `demo-capacity` failure
  remains unresolved and is not attributed to GPU work.
- **Cloud and cost:** no AWS calls or resources, GPU hours, model downloads, vLLM/DCGM
  image pulls, or goal-specific AWS spend. The four local validator images occupy
  Docker cache; the profile has not run.
- **Evidence:** static files and validator outcomes are indexed in the evidence
  manifest; no screenshots or real metrics exist yet.
- **Next:** finish review of Compose security/limits, update this record, publish PR
  #46 stacked on PR #45, and diagnose the parent PR's opaque capacity-demo failure
  through non-destructive CI diagnostics.

## 2026-11-27 — Rebase observability preparation on passing deployment base

- **Phase:** Phase 7 static preparation.
- **Branch / PR:** `codex/gpu-observability-profile`, PR #46, rebased onto PR #45's
  documented passing head and the follow-up documentation commit.
- **Starting state:** PR #45 all-checks run `45990929878` passed on `31348c3`; a later
  docs-only commit `caa9b37` records the result. PR #46 was still based on the older
  PR #45 head `bb9ad9c`.
- **Action:** rebased PR #46 onto `caa9b37`. Conflicts in the persistent goal, journal,
  and PR #45 ticket were reconciled by preserving the newer PR #45 root cause/result
  and retaining the older observability work-session entry as historical context.
  Updated ticket46 to point to the actual capacity-demo fix and new CI gate.
- **Validation:** `make gpu-compose-config`, `make gpu-observability-validate`, and
  `git diff --check` passed after rebase. This validates static configs only; no
  monitoring service or GPU was started.
- **CI / cloud / cost:** new PR #46 checks are pending after the rebase. No AWS calls,
  GPU hours, model downloads, or spend.
- **Next:** publish the rebased PR #46 head and watch one check run; then rebase the
  benchmark preparation branch onto that resulting head.


## 2026-11-27 — Publish observability preparation PR

- **Phase:** Phase 7 static preparation; no live GPU evidence.
- **Branch / PR / commit:** `codex/gpu-observability-profile`, PR #46 against PR #45,
  initial head `3f26111`.
- **Starting state:** native monitoring-config validators and Compose parsing passed;
  documentation records static-only evidence and no AWS cost.
- **Action:** pushed the observability package and opened PR #46. The PR explains the
  configuration, validation, privacy controls, cost boundaries, and remaining runtime
  checks.
- **Validation:** PR workflow started after publication; final check result is pending
  and will be recorded after its single watcher reaches a terminal state.
- **Cloud and cost:** no AWS resource, GPU runtime, or model was used.
- **Next:** inspect the #46 CI result, resolve any reviewable validation issue, then
  continue non-billable deployment preparation while quota and appeal outcome remain
  unresolved.

## 2026-11-27 — Prepare direct vLLM benchmark matrix

- **Phase:** Phase 8 static preparation; no inference measurement or GPU execution.
- **Branch:** `codex/gpu-benchmark-preparation`, prepared on top of the current PR #46
  head before PR #45's current CI run completes. PR #47 is not yet open.
- **Starting state:** existing `benchmarks/load_test.py` is marked local-mock and
  launches all requests together even though it reports a concurrency field; it does
  not measure vLLM TTFT/TPOT or authenticate requests to the gateway.
- **Research:** reviewed the official vLLM 0.34.0 `bench serve` reference for the
  OpenAI chat backend, random token lengths, max concurrency, warmups, aggregate
  output, metadata labels, and TTFT/TPOT/ITL/end-to-end percentiles.
- **Changes:** added a benchmark-client Compose profile with no GPU reservation, a
  three-shape synthetic matrix, a runner that checks context bounds and one-L4
  metadata, aggregate-only output saved outside Git, and a `make gpu-benchmark-plan`
  dry-run included in `make verify`. Concurrency 16 is opt-in after lower-load memory
  checks. The direct test is documented as excluding gateway and tenant overhead.
- **Validation:** `python3.12 -m py_compile`, Ruff, `make gpu-benchmark-plan`,
  `make gpu-compose-config`, and `git diff --check` passed. Dry-run produced 11 cases
  and 33 commands; opt-in concurrency 16 produced 12 cases and 36 commands. No Docker
  profile service was started and no benchmark API request was sent.
- **Security and cost:** output is outside public Git; detailed request payload output
  is not enabled. No AWS or model resources, GPU hours, or spend were used.
- **Outstanding:** an authenticated gateway benchmark is still needed, and vLLM CLI
  flags/pins must be verified inside the exact image before the authorized batch. No
  actual performance/cost result exists.
- **Troubleshooting:** an attempt to parse `make gpu-benchmark-plan` stdout as raw JSON
  failed because Make echoes its command line; invoking the Python dry-run directly
  produced the intended JSON record. The Make target itself completed successfully.
- **Next:** finish the static review, then publish PR #47 after reconciling the
  PR #45/#46 stack.

## 2026-11-27 — Fix benchmark timeout container targeting

- **Phase:** Phase 8 static preparation; PR #47 candidate branch.
- **Branch:** `codex/gpu-benchmark-preparation`; PR #47 is not open yet.
- **Starting state:** PR #45's capacity demo fix is pushed and its CI watcher is active.
  Review of the stacked benchmark runner found a potential cleanup mismatch after the
  first benchmark repetition.
- **Finding:** Compose names each client container from workload, concurrency, and
  repetition. The timeout handler used the overall run index, so later timeouts could
  ask Docker to stop a different, nonexistent container and leave the actual client
  alive.
- **Change:** one helper now creates the container name for both `compose run --name`
  and timeout/interruption cleanup. Added a targeted regression test for repetition 3.
- **Validation:** first test attempt could not collect the test because the standalone
  pytest environment did not include the repository root on `sys.path`; the test now
  adds that root explicitly. The workstation's default Python 3.12 has no pytest, so
  `uvx --python 3.12 --from pytest pytest -q gateway/tests/test_gpu_benchmark_runner.py`
  ran the targeted test in a temporary tool environment: 1 passed. Ruff, Python 3.12
  bytecode compilation, and `git diff --check` passed. No Docker container or GPU
  benchmark was launched.
- **Cost/security:** local validation only; no AWS resources, GPU hours, or spend.
- **Next:** await PR #45's existing CI watcher, then reconcile the PR #46/#47 branch
  stack and run CI against the corrected cleanup code.

## 2026-11-27 — Rebase and revalidate benchmark preparation

- **Phase:** Phase 8 static preparation.
- **Branch / parent:** `codex/gpu-benchmark-preparation`, rebased to PR #46 head
  `6df97e7`, which includes PR #45's passing capacity-demo fix.
- **Action:** transplanted only the two benchmark-specific commits onto the updated
  observability branch. A first broad rebase attempt began replaying PR #46's commits
  and encountered documentation conflicts; it was aborted without changing the branch.
  The focused rebase using the original PR #46 base then applied the benchmark package
  cleanly apart from status documentation, which was reconciled to retain current PR
  #45/#46 facts and show the benchmark as a candidate, not an open PR.
- **Validation:** `make gpu-benchmark-plan` produced 11 cases and 33 commands within
  120 minutes; a targeted cleanup-name regression test passed (1 test); Ruff,
  `make gpu-compose-config`, and `git diff --check` passed. No Docker profile, model,
  AWS resource, or GPU request was started. The first JSON parsing attempt included
  Make's echoed command; parsing after that line succeeded, as noted in ticket47.
- **CI / cost:** PR #46 new-head run is in progress. No AWS spend or GPU hours.
- **Next:** push the updated branch and open PR #47 against PR #46, then watch its CI.

## 2026-11-27 — Correct Trivy severity input parsing

- **Phase:** Phase 11 static CI preparation; discovered while reviewing PR #46 checks.
- **Branch / PR:** `codex/gpu-benchmark-preparation`, PR #47.
- **Finding:** PR #46's workflow emitted `Unexpected input(s) 'CRITICAL'` from the
  Trivy action. The inline YAML map left the comma-separated severity value unquoted,
  so `CRITICAL` was parsed as a separate action input rather than part of `HIGH,CRITICAL`.
- **Change:** rewrote that action's `with` section as a normal mapping and quoted the
  combined severity string so both requested severities are passed as one value.
- **Validation:** pending the next PR #47 CI run; inspect the action log for the
  absence of the warning. No AWS or GPU activity.
- **Validation:** Ruby's YAML parser accepted `.github/workflows/ci.yml`; `git diff
  --check` passed. The PR #47 workflow must still confirm the Trivy action accepts the
  value without warnings.
- **Next:** push the fix and watch the resulting PR #47 run; no local clean-room rerun.

## 2026-11-27 — Confirm rebased observability and benchmark CI

- **Phase:** Phases 7/8/11, static validation only.
- **PR #46:** rebased head `6df97e7` passed all five required checks in run
  `45992409372`, including the dedicated GPU observability schema job. No monitoring
  stack or GPU was started.
- **PR #47:** head `33a1586` passed all five required checks in run `45993312156`:
  local E2E, manifests, Python, supply-chain, and GPU observability. The supply-chain
  log now passes `HIGH,CRITICAL` as a single Trivy severity input without the earlier
  malformed-input warning.
- **Evidence:** both runs are indexed in `EVIDENCE_MANIFEST.md`; ticket46/ticket47 and
  implementation status record the static-only boundary.
- **Cloud and cost:** no AWS resource, GPU hour, model download, inference benchmark,
  or goal-specific AWS spend.
- **Next:** continue static preparation for evaluation and incident exercises, then
  refresh shared status docs and PR descriptions. The single-L4 experiment still
  requires quota approval and the complete $25 cost/plan authorization gate.

## 2026-11-27 — Prepare a deterministic LLM evaluation suite

- **Phase:** Phase 9 static preparation; no model evaluation.
- **Branch:** `codex/gpu-evaluation-preparation`, based on the passing PR #47 stack.
- **Starting state:** the repository had governed ONNX model-release demos but no
  versioned evaluation suite for the planned Qwen/vLLM runtime.
- **Change:** added seven synthetic cases covering arithmetic/factual response,
  structured JSON, instruction following, subjective summarization, simple reasoning,
  technical explanation, and malformed JSON input. Added a stdlib Python evaluator,
  deterministic check helpers, a no-network dry-run, owner-only aggregate output
  outside the repository, and a required model-revision field for actual execution.
  Prompts and response text are not written to the report; a response digest and token
  counts are recorded when available. The subjective summary remains a human-review
  item and does not become an automatic pass.
- **Troubleshooting:** the first exact-number matcher rejected a correct answer ending
  with sentence punctuation. A focused test caught this; the expression now allows
  punctuation while not accepting a larger number or a decimal prefix. Ruff also
  identified one unused import, which was removed.
- **Validation:** `make gpu-evaluation-plan` reported seven cases and zero network
  requests. Four Python 3.12 tests passed; Ruff, bytecode compilation, JSON parsing,
  and `git diff --check` passed. No vLLM, model, Docker evaluation service, AWS
  resource, or GPU was used.
- **Security and cost:** optional API credentials are read only from the environment;
  reports are excluded from public Git by default. No AWS spend or GPU hours.
- **Next:** publish the evaluation-preparation PR and validate its CI. On the L4,
  confirm actual OpenAI response shape, usage fields, malformed-input status, and
  candidate report output before connecting evaluation to governed release decisions.

## 2026-11-27 — Tighten evaluation review and report safeguards

- **Phase:** Phase 9 static preparation; no request to the model.
- **Branch:** `codex/gpu-evaluation-preparation`, based on PR #47 head `9936e11`.
- **Finding and change:** an evaluation with all deterministic checks passing could
  still need a person to inspect the subjective summary. The CLI now returns exit
  code 2 for that state, so an automated release step cannot treat it as approved. A
  separate `--show-subjective-response` flag allows an operator to inspect the
  synthetic answer interactively; by default it is not printed or saved. Reports are
  created with owner-only mode from the initial file descriptor, not chmodded only
  after writing.
- **Troubleshooting:** five focused tests pass after the numeric punctuation fix. A
  shell-quoted f-string used only to summarize dry-run output failed to parse; the
  reporting command was changed to `str.format`, and the dry-run then confirmed seven
  cases and zero network requests. No evaluation behavior depended on that shell
  one-liner.
- **Validation:** targeted Python 3.12 tests: 5 passed; Ruff across repository Python
  source/test/benchmark/evaluation/script paths passed; bytecode compilation,
  `make gpu-evaluation-plan`, and `git diff --check` passed.
- **Cloud and cost:** no model, Docker evaluation service, AWS operation, GPU hour, or
  spend. PR #48 CI remains pending.

## 2026-11-27 — Open evaluation preparation PR

- **Phase:** Phase 9 static evaluation preparation.
- **Branch / PR / commit:** `codex/gpu-evaluation-preparation`, PR #48 against PR #47,
  initial head `b67d74e`.
- **Action:** opened PR #48 with the task suite, evaluator, tests, CI dry-run, README,
  ticket, and evidence/status links. The PR description states the exact local checks
  and the limitations before GPU execution.
- **Validation before publication:** `make gpu-evaluation-plan` reported seven cases
  and zero network requests; five Python 3.12 tests passed; Ruff across source,
  tests, benchmarks, evaluations, and scripts passed; bytecode, JSON/workflow parsing,
  and `git diff --check` passed.
- **Related CI:** PR #47's updated documentation head `9936e11` passed all five
  required jobs in run `45994609421`. PR #48's required checks are now pending.
- **Cloud and cost:** no LLM request, AWS resource, GPU hour, or goal-specific AWS
  spend.
- **Next:** watch PR #48's checks, fix any real failure, then continue preparing the
  CUDA lab and incident drill without claiming runtime evidence.
