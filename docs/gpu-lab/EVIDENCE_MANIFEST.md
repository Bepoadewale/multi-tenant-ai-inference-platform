# GPU Lab Evidence Manifest

This file indexes evidence as it is collected. It distinguishes source inspection,
static validation, local execution, AWS planning, actual AWS infrastructure, and GPU
execution. A document that describes a proposed component is not proof that it ran.

## Evidence entries

| Item | Captured | Phase / PR / commit | Type | Demonstrates | Does not demonstrate |
| --- | --- | --- | --- | --- | --- |
| `REPOSITORY_AUDIT.md` | 2026-11-26 to 2026-11-27 | Phase 1 / PR #30 / `336c1b4` | Static source inspection | Existing source boundaries, specific gateway/admission gaps, reusable local paths, and why the EKS contract is separate. | GPU execution, AWS provisioning, or a complete line-by-line security review of every unrelated module. |
| `../governance/VALIDATION.md` baseline section | 2026-11-26 | Phase 1 / PR #30 / baseline `c8f02ed` | Local execution | Baseline Ruff/tests and the initial dependency audit failure, plus separate Terraform/Compose/cloud-delivery static checks. | AWS apply, GPU runtime, vLLM, or production performance. |
| `../tickets/ticket31.md` and `../governance/VALIDATION.md` PR #31 section | 2026-11-26 | Phase 1 / PR #31 / `9710932` | Local clean-room execution | Dependency-audit repair, two successful CPU/local clean-room cycles, and the documented stateful 429 failure before the final clean run. | GPU or AWS runtime and complete dependency pinning. |
| [PR #30 checks](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/30) | 2026-11-26 | Phase 1 / PR #30 / `336c1b4` | GitHub Actions | Both workflow runs passed Python, manifests, supply-chain, and local-e2e checks. Runs: `45907563245`, `45907567492`. | Human review/merge, cloud jobs, or GPU execution. |
| [PR #31 checks](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/31) | 2026-11-26 | Phase 1 / PR #31 / `9710932` | GitHub Actions | Both workflow runs passed Python, manifests, supply-chain, and local-e2e checks. Runs: `45906309837`, `45906313982`. | Human review/merge, cloud jobs, or GPU execution. |
| `RESEARCH_NOTES.md`, `COST_REPORT.md`, and `ARCHITECTURE.md` | 2026-11-26 to 2026-11-27 | Phases 1–2 / PR #30 / `80ca94e` plus current uncommitted corrections | Official-source research and estimate | Recorded AWS/NVIDIA/vLLM/PyTorch pricing and architecture inputs, a provisional bounded estimate including the repository-required DynamoDB lock table, current zero quota, and explicit checks still required. | A provider invoice, settled billing, an exact current Terraform plan, or permission to apply. |
| Read-only AWS summaries in goal and research notes | 2026-11-26 | Phase 1 / PR #30 / `336c1b4` | Authenticated AWS read-only queries | Expected AWS account was confirmed locally; exact project-tagged resource queries were empty; G/VT quota was zero; G6 offerings and Price List result were observed. | Proof that no untagged/differently tagged resource exists; no resource creation, capacity reservation, GPU access, or actual spend. |

## No execution evidence yet

As of 2026-11-27, this goal has created no AWS resources, used zero GPU instance
hours, and recorded `$0` goal-specific AWS spend. There are no genuine GPU console or
terminal screenshots, CUDA outputs, PyTorch GPU results, vLLM responses, live GPU
metrics, GPU benchmarks, GPU incidents, clean-room cloud records, or teardown
verification to index yet. Do not create or label synthetic images as execution
evidence.

## Entry format for future evidence

For every new item, record:

- **Filename and capture time:** use UTC and a stable, readable name.
- **Phase, PR, and commit:** identify the exact source state.
- **Evidence class:** static, local, simulated, AWS plan, real AWS infrastructure,
  real GPU compute, real GPU inference, benchmark, incident, or teardown.
- **Demonstrates:** state only what the artifact directly proves.
- **Does not demonstrate:** state important limits, such as one host or one sample.
- **Sanitization:** list removed account IDs, addresses, headers, secrets, prompt data,
  or other sensitive values. Never save credentials, private keys, raw Terraform
  state/plans, or unchecked environment dumps in this repository.
- **Source/reference:** link to the PR, workflow, command record, dashboard, or external
  secure artifact location when raw data cannot be public.

Store future sanitized image evidence below `evidence/` by phase. Keep large raw logs,
model files, Terraform plans, Terraform state, and sensitive artifacts outside public
Git history. Export and index evidence before destroying the authorized lab.
