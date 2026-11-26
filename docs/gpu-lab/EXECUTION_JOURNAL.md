# GPU Lab Execution Journal

Preserve earlier entries. Record actual actions and outcomes; never replace failed attempts with a clean narrative. Keep credentials, tokens, private data, raw Terraform state, and sensitive logs out of this file.

## 2026-11-26 — Goal registration and initial audit

- **Phase:** 1 — repository audit, research, and architecture.
- **Branch / PR:** `codex/single-l4-gpu-goal` / registration PR not yet opened.
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
- **Next action:** deepen Phase 1 audit and official source research; identify safe baseline audit remediation as a separate focused package; then open the docs-only goal-registration PR.
- **Next action:** finish source audit, run `make verify` as explicitly requested, record exact outcomes, then complete read-only AWS inventory and official documentation research.
