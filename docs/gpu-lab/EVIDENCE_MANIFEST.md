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
| `.local/gpu-ec2-bootstrap-preview.tfplan` and `.local/gpu-ec2-preview-r2.tfplan` (ignored local artifacts; SHA-256 recorded here) | 2026-11-27, local time | Phase 2 / PR #32 branch / working tree before commit | AWS-backed read-only local-state Terraform preview | Bootstrap plan SHA-256 `e1cd8a88e803b8cd15c1dd20fc9896aba03ffe40013d879cd6aff5928f69aaed` proposed 7 creates. GPU plan SHA-256 `a91226c5be150e1972e9351c843837c0004d54f19072684389a1c035facdef5d` proposed 14 creates, one `g6.xlarge`, `us-east-1c`, and Canonical AMI `ami-0a951420c495183dc`; the plan includes the revised SSM unit detection in cloud-init. | Remote state locking, an apply-ready plan, capacity, successful provisioning, actual guest timer/SSM behavior, or actual charges. Preview plans are local only and are not approved for apply. Placeholder budget email is not verified. |
| `.local/gpu-ec2-preview-r3.tfplan` (ignored local artifact; SHA-256 recorded here) | 2026-11-27T00:00Z | Phase 2 / PR #32 branch / working tree before commit | AWS-backed read-only local-state Terraform preview from the account-enforced source | SHA-256 `5a0574c21199d11e6af5ccbb8226240cf7a7b672ddd9ebbb5f6c64f6814658e1`; proposed 14 creates, one `g6.xlarge` in `us-east-1c`, and Canonical AMI `ami-0a951420c495183dc`. This plan was generated after changing account enforcement to provider `allowed_account_ids` and moving the AZ check to an EC2 precondition. | Remote state locking, an apply-ready plan, capacity, successful provisioning, actual guest timer/SSM behavior, or actual charges. The local preview is not approved for apply. |
| AWS Service Quotas request `34647c8598cb4ac5a8e43b3e956ccd65ikyKx4Qy` | 2026-11-27T00:03Z | Phase 2 / PR #32 branch / commit `8f3bb44` | Authenticated AWS API request | Verified the key-profile caller identity, confirmed applied G/VT quota was 0 and no pending request existed, then submitted a 4-vCPU increase for `L-DB2E81BA`; follow-up API query returned `PENDING`. | Approval, increased applied quota, available EC2 capacity, permission to launch, or any billable resource. |
| `gateway/tests/test_gpu_ec2_scripts.py` and `make verify` output | 2026-11-27 | Phase 2 / PR #32 / `99b6b84` | Local automated tests and static validation | Two subprocess tests use fake AWS/Terraform commands to show plan/apply propagate the default profile and cleanup skips schedule listing when its group is absent. `make verify` passed Ruff, 52 tests, dependency audit, and Compose config; `bash -n` and `git diff --check` passed. | Real AWS authentication, Scheduler behavior, Terraform apply/destroy, GPU execution, or cleanup in AWS. This package creates no cloud evidence. |
| GitHub Actions runs `45928736210` and `45928742151` | 2026-11-27 | Phase 2 / PR #32 / `d67ec3a` | CI execution (duplicate event triggers) | Both runs passed Python, manifests, supply-chain, and local-e2e for the same commit. The duplicate showed that `push` and `pull_request` events both run for feature branches; a workflow correction is now prepared. | Two independent manual clean-room reproductions, AWS/GPU execution, or a cloud deployment. |
| GitHub Actions run `45929546262` | 2026-11-27 | Phase 2 / PR #32 / `528b52c` | Single PR-triggered CI execution | Python, manifests, supply-chain, and local-e2e passed after limiting branch-push CI to `main`; the local end-to-end job completed once for this head. | AWS provisioning, L4 hardware/CUDA/vLLM execution, or the final clean-room AWS reproduction. |
| GitHub Actions run `45930498661` | 2026-11-27 | Phase 2 / PR #32 / `d3cee0f` | Single PR-triggered CI execution | Python, manifests, supply-chain, and local-e2e passed on the documentation/evidence refresh. | AWS provisioning, L4 hardware/CUDA/vLLM execution, or the final clean-room AWS reproduction. |
| `gateway/tests/test_gpu_ec2_scripts.py` and `make verify` output | 2026-11-27 | Phase 2 / PR #32 / `7988b8f` | Local automated tests and static validation | Six fake-CLI regression cases cover safe profile propagation, cleanup when the Scheduler group is absent, wrong account, insufficient quota, absent apply confirmation, and changed saved-plan digest. `make verify` passed Ruff, 56 tests, audit, and Compose configuration; shell syntax and `git diff --check` passed. | Real AWS authentication or calls, an apply/destroy, GPU execution, or teardown. The commit was local when this record was added; CI was pending. |
| `gateway/tests/test_gpu_ec2_scripts.py` and `make verify` output | 2026-11-27 | Phase 2 / PR #32 / `ca3706b` | Local automated tests and static validation | Four more fake-CLI tests verify destroy confirmation, checksum and account guards, plus `terraform plan -destroy`. `make verify` passed Ruff, 60 tests, audit, and Compose configuration; shell syntax and `git diff --check` passed. | A real Terraform destroy, provider-side cleanup, GPU execution, or cloud recovery. The commit was local when this record was added; CI was pending. |
| Rendered `cloud-init.yaml.tftpl` from `.local/gpu-ec2-preview-r2` | 2026-11-27, local time | Phase 2 / PR #32 branch / working tree before commit | Static rendering and YAML parsing | Terraform console rendered the instance template and Ruby `YAML.safe_load(File.read(...))` parsed the rendered YAML successfully. | Cloud-init execution, SSM registration, timer activation, or scheduled EC2 termination on a real host. |
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
