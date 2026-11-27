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

The dependency audit reported packages `certifi`, `filelock`, `gitpython`, `mlflow`, `opentelemetry-api`, `pillow`, and `pyasn1`. It reported 84 records, including repeated advisories; this is a pre-existing baseline result, not introduced by the docs-only goal registration. The separate PR #31 repair and result are recorded below.

## 2026-11-26 — Local dependency repair evidence (PR #31)

The separate open [PR #31](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/31)
adds a shared constraints file to local and gateway-container installs. On that branch:

- `make install` selected patched minimums for all seven affected transitive packages.
- `docker build -t inference-gateway:dependency-audit -f gateway/Dockerfile .` passed
  on the local arm64 Docker engine.
- `make verify` passed Ruff, **50 pytest tests** (one existing Starlette/httpx
  deprecation warning), `pip-audit` (`No known vulnerabilities found`; editable
  project distribution skipped), and `docker compose config --quiet`.
- Two independent successful clean-room runs each passed install, bootstrap, smoke,
  `make demo-flagship`, full verification, and project cleanup.
- Rerunning the cumulative demo on already populated Redis state returned 429 in the
  agent-tools scenario after earlier synthetic requests used the tenant's minute
  quota. That was not counted as a clean-room pass; a clean reset and new bootstrap
  made the entire sequence pass. This is a repeat-run caveat, not GPU or cloud evidence.
- Final cleanup left no project Compose containers, generated `.venv`, or generated
  `models/`. A pre-existing local profile database was restored; the temporary image
  used for the Docker build was removed.

These are local CPU-platform results only. PR #31 GitHub checks must reach a terminal
state before review; no AWS, GPU, CUDA, or vLLM execution is claimed.

## 2026-11-27 — Phase 2 static Terraform root

- **Branch:** `codex/gpu-ec2-foundation`, based on PR #30 head `04cb564`.
- **Scope:** isolated, proposed `g6.xlarge` environment, scheduled expiry, state key,
  guarded plan/apply/destroy scripts, and inventory-only teardown verifier. No final
  remote-state plan, apply, quota request, or resource mutation was run.
- **`make terraform-validate`:** passed for bootstrap, the existing EKS contract,
  and the new GPU EC2 root using backend-disabled initialization.
- **Formatting and shell syntax:** `terraform fmt` completed; preflight, plan, apply,
  destroy-plan, destroy-apply, and verify-clean scripts passed `bash -n`.
- **`git diff --check`:** passed.
- **Account and AZ enforcement review:** initial Terraform `check` blocks were not
  suitable as hard mutation guards because failed check assertions are warnings.
  Replaced the account check with AWS provider `allowed_account_ids` in the GPU root
  and prerequisite bootstrap root. The type-offering test is now an EC2 lifecycle
  precondition. Backend-free validation and the updated AWS-backed read-only preview
  passed; no apply was run.
- **Earlier failed validation:** AWS provider `5.100.0` rejected
  `action_after_completion` for `aws_scheduler_schedule`. The optional field was
  removed instead of upgrading the provider. The one-time schedule has no recurrence
  and is removed by the normal Terraform destroy. The final three-root validation
  then passed.
- **Template inspection:** an attempted `terraform console` in the S3-backend root
  stopped with “Backend initialization required”; it made no AWS request and changed
  no state. The local-state preview copy was then used to render cloud-init, and the
  rendered YAML passed Ruby `YAML.safe_load(File.read(...))`. The first Ruby attempt
  used unavailable `safe_load_file`; switching to the supported API passed. This is
  static parsing only: cloud-init execution, Systems Manager registration, guest timer
  activation, and scheduled termination still require a real host.
- **Limits:** source/static validation does not prove a valid AWS plan, SSM online
  status, EC2 capacity, driver setup, GPU availability, or Scheduler execution. The
  quota remains 0 vCPUs, so no GPU apply is eligible.

- **AWS-backed preview:** separate local-state plans read AWS identity, Ubuntu AMI,
  and the selected type offering. The bootstrap preview proposed 7 creates; the latest
  source-updated GPU preview (`.local/gpu-ec2-preview-r3.tfplan`, SHA-256
  `5a0574c21199d11e6af5ccbb8226240cf7a7b672ddd9ebbb5f6c64f6814658e1`) proposed 14
  creates with one `g6.xlarge` in `us-east-1c`. The AMI resolved to
  `ami-0a951420c495183dc`. The GPU preview includes the revised SSM unit detection.
  Both preview plans removed the S3 backend in a local copy, and the bootstrap used
  `operator@example.invalid`; neither plan is apply-ready. The bootstrap plan SHA-256
  is `e1cd8a88e803b8cd15c1dd20fc9896aba03ffe40013d879cd6aff5928f69aaed`.

### What this evidence does and does not establish

This establishes current local lint/test/static configuration outcomes and read-only account/quota/resource queries. It does not establish absence of untagged AWS resources, successful GPU launch, quota approval, instance capacity, driver/CUDA compatibility, inference performance, actual billed cost, or cloud cleanup.

## 2026-11-27 — Local vLLM stream accounting and cancellation tests

- **Branch:** `codex/gateway-stream-accounting`, stacked on PR #32 (ready for review).
- **Scope:** source-level vLLM OpenAI-compatible streaming behavior and local
  cancellation. This is non-billable local validation, not vLLM or GPU execution.
- **Research:** the official vLLM guide documents a final usage chunk with
  `choices: []` when `stream_options.include_usage=true`.
- **Implementation:** the adapter requests and parses final usage; the gateway exposes
  the usage-only event only if its client asked for it. First-content delay is measured
  at the gateway. Non-stream backend duration is no longer reported as TTFT. Usage
  records identify backend-reported values versus gateway word estimates. Stream
  errors and cancellation receive one terminal record in the tested local path.
- **Commands/results:** `.venv/bin/ruff check gateway/src
  gateway/tests/test_vllm_streaming.py` passed; targeted pytest reported **8 passed**;
  `.venv/bin/pytest -q` reported **58 passed**, one existing Starlette
  `TestClient` deprecation warning.
- **Setup and failed attempts:** the worktree had no Python 3.12 virtual environment.
  The first Ruff invocation therefore failed because `.venv/bin/ruff` did not exist.
  Installed the repository's editable development dependencies into a new Python 3.12
  `.venv` and generated the missing ignored local ONNX fixture with the existing model
  script. The first test collection then failed on that missing fixture; rerun passed.
  One assertion initially expected bytes although direct `StreamingResponse` iteration
  yielded strings in the test; the assertion was corrected and rerun.
- The first fake Redis-pipeline test did not implement both `hset` call forms and
  failed before checking serialization. The fake was corrected, then both test runs
  passed.
- **Limitations:** vLLM SSE was tested using `httpx.MockTransport`, not a live vLLM
  process. Cancellation used the in-memory limiter. Shared Redis lease expiry,
  reservations/reconciliation, tokenizer-accurate input limits, and real GPU execution
  remain unverified. No AWS resources or spend were created.

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
