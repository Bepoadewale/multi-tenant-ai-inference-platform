# Ticket 60 — prepare an authenticated gateway benchmark

## Objective

Prepare a bounded client that compares direct vLLM requests with authenticated
gateway requests, reports how the three synthetic tenants are admitted, and records
latency/throughput without retaining tokens or request/response content. Keep
cancellation in the existing focused cancellation drill and require a verified L4 for
any live benchmark run.

## Starting state

- Work is on `codex/authenticated-gateway-benchmark`, based on PR #58 head `351f164`.
- PR #58's corrected local Redis outage and cross-gateway cancellation drills passed
  all six CI jobs in run `46068015904`.
- PR #59 handbook passed all six jobs in run `46069680564` and is ready for review.
- AWS applied G/VT quota remains zero. No AWS resource or GPU execution is authorized.
  The initial project ceiling remains $25.

## Design and implementation

- Add `benchmarks/gpu_inference/run_gateway_benchmark.py` with sequential direct and
  gateway baselines and a concurrent workload spread across the three signed tenant
  identities and two gateway URLs.
- Report only synthetic tenant name, HTTP status, latency, client-side semaphore wait,
  throughput, and runtime-reported token counts. Never save bearer tokens, prompts,
  completions, response bodies, or error details.
- Store result files with owner-only permissions under `.local/`.
- Use Python's standard library on the EC2 host; reject redirects so tenant bearer
  tokens cannot be forwarded to another destination.
- Require IMDSv2 to confirm `us-east-1`, an approved single-GPU G6 type, and exactly
  one visible NVIDIA L4 before a live run. Keep the run bounded to at most 60 requests,
  concurrency 2–16, and a 15-second request timeout.
- Add a no-network Make dry-run, local mocked-transport coverage, and operator notes.

## Acceptance criteria

- [x] A dry-run describes the selected tenants and does not make a network request.
- [x] Mocked-transport coverage verifies sensitive request data is not copied to
  result records; redirects and credential-bearing endpoint URLs are refused; and
  output files are unique and owner-only.
- [x] L4 checks and request/runtime bounds fail closed before live execution.
- [x] Report limitations distinguish gateway latency from pure overhead and client wait
  from server queue depth.
- [ ] PR #60 CI passes.
- [ ] Human review completes; no merge without authorization.
- [ ] Actual benchmark execution remains a GPU-phase acceptance item, not this PR.

## Commands and results

- `.venv/bin/python -m pytest -q gateway/tests/test_gpu_gateway_benchmark.py` — 6 passed.
- `.venv/bin/ruff check benchmarks/gpu_inference/run_gateway_benchmark.py gateway/tests/test_gpu_gateway_benchmark.py` — passed.
- `python3 -m py_compile benchmarks/gpu_inference/run_gateway_benchmark.py` — passed.
- `make gpu-gateway-benchmark-plan` — printed the bounded synthetic plan; no network,
  identity file, AWS call, model request, or GPU was used.
- `git diff --check` — passed.
- Initial dry-run failed because importing `httpx` at module load time required the
  project environment. Replaced it with Python's standard-library `urllib` so the EC2
  host does not need the repository virtual environment; this also enabled explicit
  redirect refusal. Ruff identified import-order issues during development; corrected
  them before the final passing checks.

## Risks and limitations

The sequential P50 difference is an exploratory comparison, not isolated gateway
overhead. Semaphore wait is measured in the client and is not server queue depth.
Client cancellation and lease recovery are tested separately. A status distribution
from one short run is not a production admission guarantee. No real gateway, vLLM,
AWS, L4, cancellation, server queue depth, benchmark, or cost result is claimed.
