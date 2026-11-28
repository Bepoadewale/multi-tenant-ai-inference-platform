# Ticket #55 — Add authenticated LLM release planning and approval

## Objective

Connect the single-L4 release records to the existing role-token checks and private
MLflow evaluation service. Keep deployment separate: the gateway must not control the
Docker daemon or restart vLLM.

## Current state

- PR #54 supplies local immutable manifest/plan records and an SQLite approval store.
- PR #52 runs a private MLflow service and uploads a sanitized evaluation report.
- PR #55 adds `/gpu-release/v1` endpoints for plan creation, plan retrieval, and
  independent approval. It also records the candidate manifests in the shared,
  single-host SQLite volume.
- [PR #55](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/55)
  is open on branch `codex/gpu-llm-release-api`, based on PR #54. The previous head
  passed all five required jobs; the rebased head needs a fresh CI run.
- This is local/static validation only. No AWS or GPU resources have been used.

## Research and design

The existing `platform_admin` and `release_approver` dependencies verify Ed25519-signed
role tokens in JWT mode and return the signed subject as the actor. Plan creation
requires `platform.admin`; approval requires `release.approve`; the SQLite store rejects
the same subject approving their own plan.

The API reads the supplied finished MLflow run, checks its runtime/privacy tags,
model ID and revision, source commit, declared model artifact digest, pinned vLLM
image, runtime-configuration digest, deterministic gate metrics, and sanitized report
artifact. The report's model ID is logged as MLflow metadata so a candidate cannot
silently name another model after evaluation.

The champion manifest remains caller-supplied. The API does not inspect the active
vLLM process or independently hash model files. It does not deploy, restart, or roll
back vLLM. The SQLite named volume is shared only on this EC2 Docker host; it is not a
distributed database or a high-availability design. A future host controller must
verify live state and model bytes before it acts on an approved plan.

## Implementation tasks

- [x] Add authenticated plan, read, and approval routes without altering ONNX release
  routes.
- [x] Require the signed platform-admin and release-approver roles.
- [x] Read the finished MLflow evaluation and its sanitized artifact; compare candidate
  provenance, including model ID, with the evaluation record.
- [x] Persist exact champion and candidate manifests beside the plan in the shared
  SQLite store; enable SQLite write-ahead logging and a bounded lock wait.
- [x] Pass the exact Compose runtime settings to the evaluator and include them in
  evaluation provenance.
- [x] Add a test that rejects a candidate model ID that differs from the evaluated
  model.
- [ ] Add host-side live-champion checks and independently recompute model-file
  digests.
- [ ] Implement sequential vLLM deployment, readiness verification, and rollback.
- [ ] Validate release and rollback using the authorized L4.

## Validation

- Focused local test command: `PYTHONPATH=.:gateway/src .venv/bin/pytest -q
  gateway/tests/test_gpu_release_api.py gateway/tests/test_gpu_llm_release_control.py
  gateway/tests/test_gpu_llm_evaluation.py` — 18 passed, with one existing Starlette
  test-client deprecation warning.
- Ruff passed on the changed Python files after removing one duplicate test-fixture key.
- An initial test run used `PYTHONPATH=gateway/src` and failed to import the root
  `evaluations` namespace package. The Makefile and pytest configuration now include
  the repository root (`.`); the rerun with the corrected path passed.
- A test-only failure initially reached the model-revision mismatch before the intended
  model-ID assertion. Adding the matching revision to the fake MLflow run made the
  regression test exercise the intended rejection.
- Full `make verify` passed Ruff, 128 tests (2 skipped), the dependency audit, base and
  GPU Compose parsing, monitoring-config validation, and benchmark/evaluation/CUDA
  dry-run plans. One existing Starlette/httpx deprecation warning remains.
- An older release database may have the plan table but not the newly added manifest
  table. Store initialization now creates both tables; a regression test covers this
  upgrade shape.
- `git diff --check` passed.
- PR #55 head `b94fc27` passed all five required jobs in run `46033196309`, including
  Python, manifests, GPU observability, supply-chain, and local end-to-end.

## Security and financial considerations

The route accepts no prompt or completion content. It downloads only the sanitized
evaluation report from the fixed MLflow tracking URI. The API has no Docker socket or
host deployment permission. Release records contain model metadata and digests, not
weights or credentials. The claimed artifact digest still comes from the evaluation
configuration and is not an independent proof of file bytes.

All work is local and non-billable. AWS quota remains zero; do not provision a GPU.

## Evidence and outstanding work

Focused tests prove the local API/MLflow interaction through a fake client and role
dependencies. They do not prove a real signed-token request against a live MLflow
service, correct model artifact bytes, active champion identity, vLLM deployment,
rollback, or GPU behavior.

## Acceptance status

**Authenticated release planning and independent approval are implemented and locally
tested. The previous head passed all five required PR checks; CI for the rebased head
is pending. Deployment, live state and artifact verification, GPU execution, and
rollback remain incomplete.**
## Rebase follow-up — 2026-11-28

PR #54 added a guard that requires every stored plan to remain pending and
unapproved until the separate approval action runs. PR #55 was rebased onto that
change. The rebase exposed an overlap in the shared plan store and its tests; the
final code keeps both safeguards: it verifies the champion and candidate manifest
digests against the plan, then rejects any inserted plan with approval fields set.
The test suite now passes the manifest inputs required by the updated store API.

- Focused release-control and API tests: **13 passed**.
- Ruff and `git diff --check`: passed.
- One existing Starlette/httpx deprecation warning remains.
- The PR head and its CI checks are being updated. No AWS, GPU, model download, or
  cloud spend was used.
- The single integrated clean-room run remains planned for after the static PR stack
  has settled. No second local clean-room run was started.
