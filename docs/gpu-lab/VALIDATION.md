# GPU Lab Validation Record

This file records execution specific to the single-L4 project. Historical local CPU validation remains in [`../governance/VALIDATION.md`](../governance/VALIDATION.md). Do not treat this record as GPU evidence until a real L4 execution is recorded.

## 2026-11-26 — Baseline repository and read-only AWS preflight

- **Repository SHA:** `c8f02ed` baseline; docs are being prepared on `codex/single-l4-gpu-goal`.
- **Scope:** Phase 1 audit and read-only preflight. No AWS mutation, Terraform plan/apply, EC2 launch, or GPU execution.
- **Identity:** the configured `ai-platform-pilot-key` profile returned the expected AWS account. Account identifier is intentionally not repeated in this public file.
- **Current project resources:** Resource Groups Tagging API query for exact `project=multi-tenant-ai-inference-platform` returned `[]`; EC2 query for the same project tag returned `[]` in `us-east-1`. These exact-tag queries do not exclude untagged or differently tagged resources.
- **Quota:** `Running On-Demand G and VT instances` returned `0.0 vCPUs`, quota `L-DB2E81BA`.
- **Offerings:** `g6.xlarge` and `g6.2xlarge` are listed in multiple `us-east-1` Availability Zones. Offering is not a capacity guarantee.
- **Price lookup:** AWS Price List API filtered for shared Linux On-Demand `g6.xlarge` in US East (N. Virginia) returned `$0.8048/hour`. Twelve instance hours would be `$9.6576` before other charges.

### Local checks

| Command | Result |
| --- | --- |
| `make verify` | **Failed overall** at `make audit`. Ruff passed; pytest reported **50 passed**, one Starlette deprecation warning; pip-audit found **84 known vulnerability records across 7 packages** and exited 2 after the Makefile retried the audit as if the registry request had failed. Since the audit target stopped the Makefile, Compose validation was not reached inside this command. |
| `docker compose config --quiet` | Passed when run separately. |
| `make terraform-validate` | Passed both bootstrap and existing AWS EKS-contract Terraform roots using `init -backend=false` and `validate`. No AWS plan or mutation. |
| `make cloud-delivery-validate` | Passed Helm lint and checked cloud-delivery manifest contracts. No AWS resource or cluster was contacted. |

The dependency audit reported packages `certifi`, `filelock`, `gitpython`, `mlflow`, `opentelemetry-api`, `pillow`, and `pyasn1`. It reported 84 records, including repeated advisories; this is a pre-existing baseline result, not introduced by the docs-only goal registration. Identify safe fixes in a separate focused change and rerun the full gate.

### What this evidence does and does not establish

This establishes current local lint/test/static configuration outcomes and read-only account/quota/resource queries. It does not establish absence of untagged AWS resources, successful GPU launch, a quota increase, instance capacity, driver/CUDA compatibility, inference performance, actual billed cost, or cloud cleanup.

## Future GPU execution template

- Date/time and commit SHA:
- PR and phase:
- Exact AWS identity/region check (redact account identifier in public evidence):
- Exact reviewed Terraform plan summary and resources:
- Quota/availability/price check date:
- Approved budget and maximum runtime:
- Instance ID/type and launch/termination timestamps:
- GPU/driver/CUDA/PyTorch/vLLM/model revision:
- Commands, expected behavior, and observed results:
- Sanitized evidence paths and manifest entries:
- Estimated and settled cost status:
- Destroy result and independent provider-side absence checks:
- Explicitly unexecuted claims:
