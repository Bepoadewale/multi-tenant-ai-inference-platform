# Ticket #56 — Add a host-only sequential model release controller

## Objective

Prepare the single EC2 host to apply an independently approved language-model
release without giving the gateway Docker access. Before deployment, compare the
approved champion with private active state, verify the running model service and
cached model bytes, then replace the one vLLM process in sequence and recover the
known champion if candidate readiness fails.

## Current state

- PR #55 provides the authenticated planning and approval API. Its latest recorded
  head `de4c6e7` passed all five required jobs in GitHub run `46034523863`.
- [PR #56](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/56)
  is open as a draft on `codex/gpu-release-host-controller`, stacked on PR #55's
  `codex/gpu-llm-release-api` branch. Initial source commit: `70a0227`; a focused
  type-safety follow-up is being prepared.
- No AWS resource, EC2 host, GPU, model download, or GPU hour was used.
- The controller has local fake-based tests only. Deployment, rollback, interruption
  recovery, and GPU behavior remain unverified on a real host.

## Research and design

Keep the Docker control plane on the host. The gateway can create and approve exact
plans, but it does not mount the Docker socket. A host-only Python command fetches the
approved plan over HTTPS (or a loopback URL for the local SSM-forwarded API), prompts
for a short-lived platform-admin token without echoing it, and applies the exact
candidate manifest.

The controller checks the release plan and manifest digests, two distinct actors,
the fixed `single-l4-lab` environment, bounded single-GPU settings, and the private
active champion record. It inspects the running vLLM image, command arguments, health,
and named model-cache volume. It hashes a sorted manifest of every file in the pinned
Hugging Face snapshot, resolving cache symlinks and refusing paths outside the cache.
It then changes only model-serving variables in `.env`, recreates only vLLM, and
starts the two gateway replicas after the new model is ready. A private transaction
journal allows a later recovery command to restore the last active manifest.

The digest format is a tree digest: SHA-256 of a canonical JSON list containing each
relative path, byte size, and file SHA-256. It differs from the existing verifier's
single-weight-file digest and must be labeled accordingly in reports. The host
controller checks HTTP readiness and the served model alias; it does not send a
tenant-authenticated inference request itself. The operator's smoke-test procedure
must verify real inference through the gateway after deployment.

The runtime cache must already contain both pinned snapshots before `apply`; the
controller does not download model weights. This keeps downloads and license checks
inside the planned GPU batch, before the controlled release operation.

## Implementation tasks

- [x] Add a host-only CLI for snapshot digest, metadata manifest creation, champion
  initialization, approved apply, interrupted-transaction recovery, and restoration
  after candidate evaluation.
- [x] Verify the approved plan, distinct requester/approver, target environment,
  bounded single-L4 configuration, active manifest, container image/arguments/cache
  volume, HTTP readiness, and full snapshot digest.
- [x] Restrict API transport to HTTPS or loopback and read the API token through
  `getpass`; do not log or persist it.
- [x] Keep Docker control out of gateway containers and write private state/journal
  and `.env` files atomically with mode `0600`.
- [x] Test candidate success, candidate failure with verified rollback, cache symlink
  validation, mount/image mismatch, plan approval, environment updates, and CLI
  recovery output with local fakes.
- [ ] Validate interruption recovery, candidate rollout, and rollback on the approved
  L4 host after quota and cost gates pass.
- [ ] Run the authenticated tenant inference smoke test through the gateway after a
  live rollout.

## Validation

- `.venv/bin/ruff check scripts/gpu_release_controller.py gateway/tests/test_gpu_release_controller.py` — passed.
- `PYTHONPATH=.:gateway/src .venv/bin/pytest -q gateway/tests/test_gpu_release_controller.py` — 16 passed.
- `make gpu-release-controller-help` — passed; displays commands without Docker or AWS access.
- `make gpu-compose-config` — passed after adding host-loopback-only model readiness access.
- Redirects from the authenticated release API are rejected so a bearer token is not
  forwarded to a new host or URL; a focused handler test covers this rule.
- Initial champion creation uses the host release lock, and candidate restoration
  refuses to overwrite an incomplete transaction without explicit recovery.
- Runtime validation rejects a floating-point `tensor_parallel_size` value instead
  of allowing an invalid CLI argument to reach vLLM.
- `make verify` — passed after the type-safety follow-up: Ruff, 144 tests (2 skipped), dependency audit with no known
  vulnerabilities, base/GPU Compose parsing, monitoring configuration validation,
  and benchmark/evaluation/CUDA dry-run plans. One existing Starlette/httpx
  deprecation warning remains.
- Relative Markdown link check across 13 changed documentation files passed;
  `git diff --check` passed.
- PR #55's latest check run `46034523863` passed all five required jobs. PR #56
  initial head `ad10699` passed all five jobs, including its single clean-room cycle,
  in run `46039778508`. The follow-up that rejects floating-point tensor-parallel
  values is a material safety fix and needs its own required CI run.
- During implementation, Ruff first found unused/reordered imports and a test had
  missing model-artifact environment mapping; these were corrected and the focused
  suite rerun. Review also caught that non-`apply` CLI commands lacked `plan_id` in
  their final success message; a regression test now covers `recover`.

## Security and financial considerations

The controller stores no token. State and transaction records are private host files.
The gateway remains unable to control Docker. API credentials must use TLS except
when the URL is loopback on the host. The controller will restart a single vLLM
service and cause downtime; it does not implement a simultaneous canary or high
availability. Candidate snapshots and images must be staged before the approved
release command. No cloud action is authorized by this ticket; the project ceiling
remains $25 and the current GPU quota is zero.

## Evidence and limits

The unit tests use temporary files, fake subprocess results, and mocked HTTP calls.
They prove local control-flow behavior only. They do not prove Docker Compose behavior
on Ubuntu, safe file ownership on the target host, vLLM readiness, gateway inference,
NVIDIA GPU access, rollback timing, or recovery after EC2 interruption.

## Acceptance status

**Static controller implementation and the full repository suite are locally tested.
PR #56 CI, human review, and all live L4 acceptance criteria remain pending.**
