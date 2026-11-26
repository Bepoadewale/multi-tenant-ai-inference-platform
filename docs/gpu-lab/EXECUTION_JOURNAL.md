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
