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
- **Findings and decision candidates:** prefer Terraform's versioned, private,
  encrypted S3 backend with native `use_lockfile=true`; HashiCorp marks DynamoDB
  locking deprecated, so a lock table is unnecessary. Session Manager itself has no
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
