# GPU Lab Validation Record

This file records execution specific to the single-L4 project. Historical local CPU validation remains in [`../governance/VALIDATION.md`](../governance/VALIDATION.md). Do not treat this record as GPU evidence until a real L4 execution is recorded.

## 2026-11-26 — Baseline repository and read-only AWS preflight

- **Repository SHA:** `c8f02ed` baseline; subsequent implementation and validation entries identify their own branch and commit.
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

## 2026-11-27 — PR #33 streaming review fixes

- **Scope:** addressed two review findings in the local streaming boundary. No live
  vLLM server, Redis, AWS resource, or GPU was used.
- **Research:** current vLLM OpenAI chat-completion server code has a streaming error
  path that can emit an error response after the HTTP stream has started. The adapter
  now treats a JSON event with an `error` field as a failed stream.
- **Changes:** added regression coverage for in-band upstream error events and for
  estimated usage in string-yielding backends. When requested, the gateway now emits
  one final usage chunk after successful metering if the backend did not report usage.
  Backend-reported usage continues to be emitted once.
- **Validation:** Ruff passed; `gateway/tests/test_vllm_streaming.py` reported **10
  passed**; `make verify` passed Ruff, **60 tests**, `pip-audit` with no known
  vulnerabilities, and Docker Compose configuration. One existing Starlette/httpx
  deprecation warning remains.
- **Limitations:** all upstream streams were mocked. The final usage contract still
  needs verification against the exact pinned vLLM build before GPU integration.
- **Cloud boundary:** no AWS resources were created or changed; goal-specific spend is
  `$0`, GPU instance-hours are `0`, and the quota request remains separate from apply
  authorization.

## 2026-11-27 — PR #34 Redis lease safety review fixes

- **Scope:** bounded Redis lease renewal and cleanup of orphaned reservation metadata.
  This was local non-billable work; no AWS resource or GPU was used.
- **Changes:** the gateway now bounds each asynchronous renewal wait to one third of
  the lease after sleeping for one third, then cancels the request owner on timeout or
  failed renewal before the lease expires. Redis refuses to renew an already-expired
  lease. New admissions prune expired lease members and delete their hash metadata,
  while minute/day token-ledger entries remain until the quota windows expire.
- **Validation:** `make verify` passed Ruff, **75 tests**, pip-audit with no known
  vulnerabilities, and Docker Compose config. Two optional Redis tests were skipped in
  the general run. With a disposable Redis 7.4 container, the lease/in-memory suite
  reported **7 passed**, including repeated crash cleanup and the bounded renewal test.
- **Environment:** the first bounded-renewal regression test also verifies that the
  owner is cancelled in less than the configured lease duration. The Redis test
  container was stopped after the integration run.
- **Limitations:** this establishes Lua behavior against one local Redis server and
  cancellation behavior in one Python process. It does not prove independent gateway
  processes, a Redis outage under live traffic, live vLLM, or GPU behavior.
- **Cloud boundary:** no AWS changes; project-specific spend remains `$0` and GPU
  instance-hours remain `0`.

## 2026-11-27 — Model-aware token preflight prework

- **Branch:** `codex/tokenizer-admission-preflight`, based on PR #34.
- **Scope:** bounded chat input, tenant-specific input/output token limits, vLLM
  chat-tokenizer adapter, model context validation, request-rate/concurrency admission
  before tokenization, and atomic exact token reservation before inference. This is
  local-only preparation; no AWS resource, live vLLM, or GPU was used.
- **Official research:** vLLM's current protocol describes chat messages and returns
  token count plus max context length. Its security guide documents that `/tokenize`,
  metrics, and health endpoints are not covered by the server API key, and shared
  processes share runtime/cache state. See `RESEARCH_NOTES.md` and `RISK_REGISTER.md`.
- **Commands/results:** Ruff passed; focused tests reported **22 passed, 2 optional
  Redis skips**. Full `make verify` passed with **72 passed, 2 optional Redis skips**,
  one existing Starlette deprecation warning, and `pip-audit` reporting no known
  vulnerabilities. `docker compose config --quiet` and `git diff --check` passed.
  Both Redis integration tests passed against disposable local Redis 7.4.
- **Fixes during validation:** Ruff first reported unsorted imports in the new Redis
  service and limiter test; Ruff auto-fixed import order and the rerun passed. A
  gateway test verifies that an exact quota overrun is rejected before backend
  inference and that reservation/capacity state is released.
- **Limits:** vLLM responses are mocked; Redis is one local server with two limiter
  clients. This does not prove live vLLM compatibility, independent gateway processes,
  private Compose-network enforcement, cache salt behavior, AWS, GPU, or production
  availability. The request-count/content bounds and token preflight are code evidence
  only until the runtime is pinned and exercised.

## 2026-11-27 — PR #35 lease renewal during tokenizer preflight

- **Scope:** prevent the concurrency reservation from expiring during a valid but slow
  vLLM tokenizer request. No cloud resource or GPU was used.
- **Change:** start the lease watcher immediately after shared admission, retain it
  through tokenization and exact reservation adjustment, and stop it on success or all
  preflight failure/cancellation paths. The normal generation/stream path starts its
  own watcher after preflight.
- **Regression:** a local `TenantLimiter` with a 30 ms lease and an async tokenizer
  delay of 100 ms completes the request and releases reservation state. Targeted tests:
  21 passed.
- **Validation:** `make verify` passed Ruff, **87 tests**, pip-audit, and Docker Compose
  configuration; two opt-in Redis tests were skipped. A disposable local Redis 7.4
  integration run passed **2 tests**. `git diff --check` passed.
- **Limitations:** tokenizer and inference use mocks; Redis tests use one local Redis
  process. This does not verify a live vLLM release, separate gateway processes,
  production network failure, or GPU execution. Commit `59cca44` was local at capture.

## 2026-11-27 — PR #36 rebased failure-path suite

- **Scope:** retain cancellation, unavailable-admission, and tokenizer timeout tests on
  top of the PR #35 lease-renewal fix. No cloud or GPU was used.
- **Validation:** `make verify` passed Ruff, **90 tests**, pip-audit, and Compose config;
  2 optional Redis tests were skipped, and one existing Starlette warning remains.
  `git diff --check` passed.
- **Limits:** test doubles and HTTPX `MockTransport` only; not a real Redis outage,
  live vLLM timeout, GPU, or independent gateway process. Local PR #36 code is based on
  PR #35 head `5cd8dfb`; fresh CI is pending publication.

## 2026-11-27 — PR #35 CI failure and single-run policy

- **Commit:** `97bfcfc` on `codex/tokenizer-admission-preflight`.
- **Evidence:** GitHub runs `45921908625` (`push`) and `45921912244`
  (`pull_request`) ran the same `local-e2e` workflow. Both passed smoke, then failed
  in `make demo-flagship` → `demo-local`. The prior assertions did not print which
  expectation failed. These were duplicate CI event runs, not a request for two
  clean-room reproductions.
- **Policy:** one complete clean-room cycle is sufficient; repeat only after a failed
  cycle or a relevant fix. The two successful CPU clean-room cycles under PR #31 are
  retained as historical evidence and will not be repeated for this goal.
- **Root cause:** the gateway treated every `VllmBackend` HTTP adapter as a vLLM
  model. The local CPU ONNX target also uses an HTTP adapter, but has no `/tokenize`
  endpoint. The GPU preflight therefore failed on the existing CPU streaming demo.
- **Fix and local result:** the gateway now invokes tokenizer preflight only when the
  catalog declares `runtime: vllm`; a vLLM model with a non-vLLM backend fails closed.
  A regression test covers the ONNX HTTP target. `make verify` passed with **73
  passed, 2 optional Redis skips**, one existing Starlette deprecation warning, no
  known dependency vulnerabilities, and valid Compose configuration. The first
  attempt exposed a positional argument mistake in the new test's `Usage` fixture;
  switching it to named fields fixed the test.
- **Next CI:** `demo-local.sh` now reports the failed stream or HTTP assertion and its
  synthetic response. CI is configured for pull requests and pushes to `main`, so
  feature-branch commits run once. Bash syntax, workflow YAML parsing, and
  `git diff --check` pass.
- **Verified fix:** commit `ee4b46c` passed all four required jobs in one PR-triggered
  workflow (`45923987903`). Its fresh-runner `local-e2e` job passed, including the
  previously failing streaming demo. This was local CPU CI evidence, not an AWS/GPU
  clean-room reproduction.
- The subsequent documentation head `a8e63b8` also passed all four jobs in one
  workflow (`45925070365`). This rerun followed a documentation commit; it was not
  requested as a second clean-room gate.

## 2026-11-27 — Preflight timeout, cancellation, and Redis outage tests

- **Branch:** `codex/vllm-preflight-failure-cleanup`, based on PR #35; PR not yet open.
- **Scope:** local tests for cancellation during tokenization, an unavailable Redis
  admission dependency, and tokenizer HTTP read-timeout handling. No service or cloud
  infrastructure was started.
- **Commands/results:** `make verify` passed Ruff, **76 tests**, 2 optional Redis
  skips, pip-audit with no known vulnerabilities, and `docker compose config --quiet`.
  One existing Starlette deprecation warning remains.
- **Limits:** Redis outage is tested with a deterministic client double; timeout is
  simulated through HTTPX `MockTransport`; no live Redis outage or vLLM server was
  used. No AWS, GPU, or clean-room execution is claimed.
- **CI:** PR #36 commit `69365aa` passed all four jobs in one PR-triggered run
  (`45926383360`), including local-e2e. This is routine CI validation; the project
  still requires one final clean-room reproduction in Phase 12.

## 2026-11-27 — PR #56 host release-controller focused validation

- **Branch:** `codex/gpu-release-host-controller`, stacked on PR #55.
- **Commands:** `.venv/bin/ruff check scripts/gpu_release_controller.py gateway/tests/test_gpu_release_controller.py`;
  `PYTHONPATH=.:gateway/src .venv/bin/pytest -q gateway/tests/test_gpu_release_controller.py`;
  `make gpu-release-controller-help`; `make gpu-compose-config`; `git diff --check`.
- **Result:** Ruff passed; 16 focused tests passed; CLI help and GPU Compose parsing
  passed; whitespace check passed.
- **Coverage:** deterministic fake-based tests cover plan approval and bounded config,
  full snapshot digest including Hub cache symlinks, rejection of paths outside cache,
  loopback vLLM/gateway readiness ports, active container image/arguments/cache mount,
  private file writes, redirect rejection for authenticated requests, successful
  candidate deployment, readiness-failure rollback, active restoration, incomplete
  transaction guard, integer-only tensor-parallel settings, and non-apply CLI output.
- **Limit:** no live Compose host, authenticated gateway inference request, AWS,
  model/image download, GPU, rollback after process interruption, or billing evidence.
  Full `make verify` passed Ruff, **144 tests** (2 skipped), the dependency audit,
  Compose and monitoring validation, and benchmark/evaluation/CUDA dry-run plans.
  Initial head `ad10699` passed all five PR jobs in run `46039778508`; updated head
  `852c873` passed all five jobs, including the required clean-room cycle, in run
  `46040861818`. See the updated-head record below.

## PR #56 host release controller updated-head clean-room validation

**Date:** 2026-11-27 17:21 UTC

**Branch / PR:** `codex/gpu-release-host-controller`, PR #56, source head `852c873`.

GitHub Actions run [46040861818](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/actions/runs/46040861818)
passed all five required jobs plus the repository's `local-e2e` clean-run job. That
job executed the following on a fresh Linux runner:

```console
make install
make bootstrap-local
make smoke
make demo-flagship
make verify
make clean-local
```

The run passed after a code change fixed acceptance of `1.0` where the runtime
requires an integer. This is the one clean-room cycle for the material follow-up.
It proves local CPU and static repository flows on GitHub's runner; it does not prove
AWS, Docker-on-L4, model deployment, live inference, or rollback on the EC2 host.
No cloud resource or spend was used.

## PR #57 Ansible preparation local validation

**Date:** 2026-11-27 17:42 UTC

**Branch:** `codex/gpu-ansible-host-configuration`, stacked on PR #56 head `852c873`.

The Ansible 2.21.6 universal hash lock installed successfully into an isolated
`/tmp/gpu-ansible-venv` using `--require-hashes`. `make gpu-ansible-validate` passed;
`ansible-playbook --list-tasks` enumerated the host checks, package/repository setup,
PyTorch lock installation, Docker runtime setup, and verification tasks. A temporary
local assertion with a representative `lspci` L4 line also passed. No role task was
executed on the workstation or an EC2 host.

The new worktree initially lacked the project's `.venv`; `make install` created it,
then `make verify` passed Ruff, **144 tests** (2 skipped), the dependency audit,
Compose and monitoring validation, and GPU benchmark/evaluation/CUDA dry-run plans.
The first bare system-Python pip dry-run was rejected by macOS's externally managed
environment guard; the actual hash-locked Ansible install was performed in the
isolated temporary virtual environment. `git diff --check` and relative Markdown-link
validation passed. These are local/static checks, not package or GPU execution.

## GPU tenant fixtures and manual reproduction guide preparation

**Date:** 2026-11-27 18:19 UTC

**Branch:** `codex/gpu-manual-reproduction-guide`, stacked on PR #57 head `4795f12`.

The first `make verify` stopped because this worktree did not yet have its project
`.venv`. After `make install`, `make verify` passed Ruff, **146 tests** (2 skipped),
the dependency audit with no known vulnerabilities, GPU Compose validation,
Prometheus/Alertmanager/dashboard validation, and benchmark/evaluation/CUDA dry-run
plans. The new tests confirm three tenant profiles have different quotas and model
access, existing CPU tenants remain available, and generated Ed25519 tokens carry the
expected tenant claims. They also check the signing key and token file are mode `0600`
and the gateway-readable public key is mode `0644`.

The guide's initial relative-link and documented Make-target checks passed. PR #58
runs `46049398387` and `46050614853` passed Python, manifests, GPU observability, and
Ansible. Their supply-chain jobs failed before scanning: first on default Trivy
`v0.70.0`, then on published Trivy `v0.76.2` because the installer could not resolve
its tag. Run `46052092657` passed the checksum-verified official Trivy scan and every
job except local E2E. Its named smoke assertion identified an empty edge-device
inventory. Source inspection showed that the edge services ran as image UID `65532`
while the recently secured token file is owner-only (`0600`) and owned by the local
bootstrap user; the agents caught the file-read error, kept retrying, and still
reported healthy. Commit `d759b8e` made only those local simulation containers use the
bootstrap UID/GID and waits for their registration. All six CI jobs passed on that
head in run `46054114999`; the fresh local E2E sequence completed install, bootstrap,
smoke, flagship demo, verification, and scoped cleanup. After that CI run, automated
review findings led to further documentation-only changes for wrapper inputs, the
separate billable state bootstrap, manual vLLM handoff, and workstation teardown.
Static review on this final guide draft parsed all 40 Bash blocks, matched all eight
documented Make targets, checked relative links, parsed workflow YAML, and passed
`git diff --check`. The final guide changes still need the normal PR CI. No AWS
command, model download, GPU operation, or cloud spend occurred.

These checks establish source behavior and document consistency only. They do not
establish cross-process Redis behavior for these named tenants, a real signed request
through either GPU gateway, model denial on live vLLM, or GPU hardware isolation.

## Authenticated gateway benchmark preparation

On 2026-11-27, the non-GPU gateway benchmark client passed three focused tests,
including an HTTP mock transport that returned a sentinel completion and verified
the client result record contained neither that completion nor the bearer token.
`make gpu-gateway-benchmark-plan`, Python compilation, Ruff, and `git diff --check`
passed. The plan makes no network request. Initial review caught a missing local
`httpx` import in the dry-run path; the dependency is now loaded only for live requests.
Ruff also caught an import-order issue, which was corrected before the final passing
checks. No live gateway request, model output, AWS call, or GPU measurement occurred.

The direct-versus-gateway latency delta is an exploratory comparison, and semaphore
wait is client-side queueing. Neither is claimed as isolated server overhead or
server queue depth. Cancellation uses the separate stream-cancellation drill.

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
