# Ticket 60 — prepare an authenticated gateway benchmark

## Objective

Prepare a bounded client that compares direct vLLM requests with authenticated
gateway requests, reports how the three synthetic tenants are admitted, and records
latency/throughput without retaining tokens or request/response content. Keep
cancellation in the existing focused cancellation drill and require a verified L4 for
any live benchmark run.

## Starting state

- Work is on `codex/authenticated-gateway-benchmark`, based on PR #58 head `59925fd`.
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
- Require HTTPS or loopback HTTP for endpoints; send bearer credentials only to the
  gateway requests, never to the direct vLLM comparison.
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
- [x] PR #60 implementation head `2e2d177` passed all six required jobs, including
  local E2E, in run `46072579851`.
- [ ] Human review completes; no merge without authorization.
- [ ] Actual benchmark execution remains a GPU-phase acceptance item, not this PR.

## Rebase and follow-up validation — 2026-11-28

PR #58 was advanced with the manual reproduction guide, so PR #60 was rebased onto
its updated head. Its implementation history is preserved; current head checks must
be distinguished from the prior CI result above.

- Rebased PR #60 onto PR #58 head `59925fd`; implementation head before this record:
  `840f8c0` (`fix: preserve gateway benchmark samples on failures`).
- `PYTHONPATH=.:gateway/src .../bin/python -m pytest gateway/tests/test_gpu_gateway_benchmark.py -q`
  — 8 passed.
- Focused Ruff check and `git diff --check` — passed.
- Fresh CI for the rebased head is pending; the prior run `46072579851` applies only
  to the former head `2e2d177` and is not proof for the current source.
- No GPU, AWS, network inference, clean-room run, or spend was involved.

## Commands and results

- `.venv/bin/python -m pytest -q gateway/tests/test_gpu_gateway_benchmark.py` — 8 passed.
- `.venv/bin/ruff check benchmarks/gpu_inference/run_gateway_benchmark.py gateway/tests/test_gpu_gateway_benchmark.py` — passed.
- `python3 -m py_compile benchmarks/gpu_inference/run_gateway_benchmark.py` — passed.
- `make gpu-gateway-benchmark-plan` — printed the bounded synthetic plan; no network,
  identity file, AWS call, model request, or GPU was used.
- `git diff --check` — passed.
- PR run `46072579851` passed `python`, `manifests`, `supply-chain`, `ansible`,
  `gpu-observability`, and `local-e2e` on implementation head `2e2d177`.
- Initial dry-run failed because importing `httpx` at module load time required the
  project environment. Replaced it with Python's standard-library `urllib` so the EC2
  host does not need the repository virtual environment; this also enabled explicit
  redirect refusal. Ruff identified import-order issues during development; corrected
  them before the final passing checks.

## Review findings

- Automated review reproduced a truncated HTTP 200 response that raised
  `http.client.IncompleteRead` and aborted `asyncio.gather()`. The client now converts
  HTTP protocol/read errors into a sanitized per-request `transport_error` result so
  other samples and the final report can complete.
- Review found that baseline P50 included 401/429/backend failures and could present an
  invalid gateway-overhead delta. The comparison now uses only HTTP 200 inference
  samples and returns `null` if either side has no successful sample.
- Added regressions for both findings. Eight focused tests pass; Ruff, compilation,
  dry-run, and whitespace validation pass. The fixes require fresh PR CI.

## Risks and limitations

The sequential P50 difference is an exploratory comparison, not isolated gateway
overhead. Semaphore wait is measured in the client and is not server queue depth.
Client cancellation and lease recovery are tested separately. A status distribution
from one short run is not a production admission guarantee. No real gateway, vLLM,
AWS, L4, cancellation, server queue depth, benchmark, or cost result is claimed.


## 2026-11-28 restack and local verification

PR #60 was restacked from former PR #58 head `59925fd` onto current PR #58 head
`fa4d819`; this PR is a sibling of PR #59, not its descendant. Eight PR-specific
commits were replayed. The worktree did not have a `.venv`, so the first direct test
command stopped before collection; the existing PR #58 Python 3.12 environment was
used without changing dependency state.

The focused test suite passed **8 tests**, Ruff passed, and the no-network dry run
reported 18 planned requests at concurrency 6 for all three tenants with no content
saved. `git diff --check` passed. No real inference request, GPU, model download, AWS
operation, or spend occurred. PR #58 run `46162221680` subsequently passed all six required checks; sibling PR #59 run `46162611345` remained in progress. Refreshed CI remains to be triggered on the new PR #60 head.
