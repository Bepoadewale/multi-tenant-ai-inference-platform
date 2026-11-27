# GPU Lab Execution Journal

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
