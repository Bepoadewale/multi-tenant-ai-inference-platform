# Ticket 51 — Design a truthful single-L4 LLM release path

## Objective

Close the documented gap between the repository's existing ONNX canary/release API
and the one-vLLM-server GPU profile. Define a sequential candidate, approval,
deployment, and rollback path without implying that one L4 can run a concurrent
canary or provide high availability.

## Current state

- Existing `gateway/src/inference_gateway/api/release.py` manages the local ONNX model,
  its champion/candidate aliases, and weighted rollout targets.
- The GPU Compose catalog points at one vLLM service and one served-model alias. The
  existing weighted ONNX targets do not apply to that profile.
- The default local Compose runs MLflow, but the single-GPU profile has no MLflow
  service. The LLM evaluator produces a sanitized report but does not register it.
- No LLM model release or GPU rollback has run.
- This is static design preparation on branch `codex/gpu-sequential-release-design`,
  [PR #51](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/51),
  stacked on PR #50. All five required checks, including local end-to-end, passed on the prior head
  `b205929` in run `46013204318`. PR #51 has since been rebased onto the updated PR #50
  branch, which now includes PRs #33–#36. Fresh checks on the restacked head are required. No LLM release code or runtime behavior
  has changed. It makes no AWS call and spends no GPU hours.

## Research and decisions

- Use MLflow to store immutable model deployment manifests and sanitized evaluation
  evidence; keep large model weights at the pinned Hugging Face revision.
- Use separate LLM release records and approval state rather than changing the
  existing ONNX release flow.
- Bind approval to model, evaluation, runtime image, vLLM configuration, and current
  champion digests; reject stale plans.
- Deploy sequentially by restarting the one vLLM service and verify rollback to the
  known-good model if candidate startup or smoke checks fail.
- Treat host-local SQLite and artifact storage as temporary lab records only; include
  the MLflow service's memory and disk needs in host-fit checks.
- The current vLLM v0.34.0 release publishes the CUDA 13.0 OpenAI server image. Its
  release notes require Hugging Face Hub 2.0+ and describe a changed KV-cache sizing
  default. Preserve the model's 8,192-token context and low initial sequence limit,
  but explicitly validate the existing 85% memory-utilization setting against the
  release's sizing behavior before the live load. The official GPU guide lists L4 as
  supported; this is source compatibility, not runtime evidence.

## Changes

- Added `SEQUENTIAL_LLM_RELEASE_DESIGN.md` with the current incompatibility, proposed
  release state machine, deployment sequence, MLflow placement, and evidence-based
  acceptance criteria.
- Linked the design from the documentation index and implementation backlog.

## Validation

- Confirmed the incompatibility by inspecting the existing release API, model catalog,
  single-GPU Compose profile, and evaluation report schema.
- Local Markdown links and whitespace checks are required before publication.
- No model, package, image, or AWS resource was downloaded or installed.
- Official release and installation documentation were rechecked on 2026-11-27;
  versioned image digest and all configuration choices still require final preflight.
- All five required checks, including local end-to-end, passed on the prior design head
  `b205929` in run `46013204318`. After restacking behind gateway safety PRs #33–#36,
  current head `44c467a` passed all five required checks in run `46017455801`. These
  checks validate CPU-only workflows and configuration, not model serving or GPU
  behavior.
- The follow-up documentation head `855a52d` passed all five required jobs in run
  `46018929290`. No GPU image, model, AWS resource, or inference endpoint was used.

## Security and cost

The design keeps MLflow and release controls on the private Compose network and
requires independent approval. Reports must omit prompt/response text and secrets.
Any eventual deployment remains within one L4 and the $25 total budget ceiling.

## Outstanding work

- Implement the private MLflow service and an LLM model/evaluation manifest uploader.
- Implement immutable sequential release plans, independent approval, stale-plan
  protection, safe vLLM restart, and verified rollback.
- Add unit/integration tests and update Compose/config checks before any GPU work.
- Demonstrate candidate rejection, successful promotion, failure recovery, and
  rollback on the authorized single L4.

## Acceptance status

**Design only. No LLM candidate has been registered, approved, deployed, or rolled
back.**
