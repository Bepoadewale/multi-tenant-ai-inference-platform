# Ticket 35 — bounded model-aware token preflight

## Objective

Replace the word-count estimate on the GPU-backed path with the model's own chat
renderer and tokenizer. Enforce tenant and model input/output limits before inference,
reserve the prompt count plus requested output cap, and keep the vLLM tokenizer route
private because it is not protected by vLLM's API key.

## Current state

- Branch: `codex/tokenizer-admission-preflight`, based on PR #34.
- Pull request: [#35 — model-aware token reservations](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/35), draft and open against PR #34's `codex/redis-admission-leases` branch; head `34782b9`, CI running.
- Phase: non-billable Phase 6 prework. No live vLLM, AWS infrastructure, or GPU was
  used.
- PR #34's latest docs head `ae99959` passed all required checks and is ready for
  review.

## Research findings

The current vLLM protocol documents chat tokenization from the same messages and chat
template used by chat completion, and returns both a token count and model context
limit. This avoids counting whitespace words as if they were model tokens. The exact
schema must be checked against the pinned vLLM release when runtime versions are
selected.

The vLLM security guide states that `--api-key` protects selected endpoint prefixes;
`/tokenize`, `/metrics`, and health routes are not protected. The server port therefore
must remain private to the Docker network and the gateway must authorize the tenant
before sending a tokenizer request. Bound request size and message count and count the
request against its rate quota before tokenization, so the helper endpoint cannot be
used for unbounded CPU work outside admission control.

The same guide says tenants sharing one vLLM process share runtime state and prefix
cache behavior can expose timing signals. A random tenant-scoped `cache_salt` can
reduce cache sharing if the selected release supports it, but this is not hardware or
process isolation.

Official references are recorded in `docs/gpu-lab/RESEARCH_NOTES.md` and linked from
the risk register.

## Implementation tasks

- [x] Bound each message, message count, and total content bytes before upstream
  tokenization.
- [x] Enforce tenant-specific maximum prompt and completion tokens.
- [x] Add a vLLM `/tokenize` call using chat messages and the routed model with a short
  timeout; reject malformed responses and fail closed when the endpoint is unavailable.
- [x] Enforce prompt plus output cap against the configured model context and the
  upstream tokenizer response.
- [x] Charge request-rate and concurrency admission before tokenizer work, then
  atomically adjust token reservation to prompt plus output cap before generation.
- [x] Reconcile completed backend usage; preserve a conservative reservation when
  actual use is unavailable.
- [x] Keep ONNX and mock behavior compatible and run repository verification.
- [ ] Keep the vLLM server private and allow only gateway/tokenizer and intended
  telemetry access. This is a deployment requirement; the vLLM Compose profile is not
  implemented yet.
- [ ] Add tenant-scoped prefix-cache salt if supported by the pinned runtime; do not
  treat it as an isolation boundary.
- [ ] Add dedicated timeout, preflight cancellation, and Redis-outage tests.
- [ ] Validate `/tokenize` request/response compatibility against the pinned live
  vLLM release during the authorized GPU batch.

## Security, reliability, and cost boundaries

No prompt content or token IDs enter logs, traces, metrics, or quota keys. The code
calls `/tokenize` only after model authorization and shared request/concurrency
admission. The vLLM server must not publish an internet-facing port. The actual
private-network profile is not implemented yet.

Tokenizer work is CPU work and may be abused even when inference admission later
rejects the request. The implementation bounds content, charges request rate before
tokenization, uses a short timeout, and adjusts the token reservation atomically before
inference. Tokenization failure fails closed and releases concurrency.

## Validation and evidence

- Ruff passed for the gateway source and new tests.
- `make verify` passed: **72 passed, 2 optional Redis tests skipped**, one existing
  Starlette deprecation warning; `pip-audit` reported no known vulnerabilities.
- Both Redis integration tests passed against a disposable local Redis 7.4 container,
  including cross-client quota adjustment and lease recovery. The exact container was
  stopped and auto-removed.
- Tests use mocked vLLM endpoints. No live vLLM, AWS, or GPU was used.
- The PR's first GitHub validation at `97bfcfc` launched two `local-e2e` runs for
  the same commit because the workflow listened to both branch pushes and pull
  requests. Both passed smoke and failed inside `make demo-flagship`'s `demo-local`
  script. The old script stopped at an assertion without identifying which one.
  `scripts/demo-local.sh` now reports the expected HTTP/status assertion and
  sanitized fixture response; the CI workflow now runs on pull requests and on
  pushes to `main`, avoiding duplicate branch-push/PR runs. This is a diagnostic
  change, not a passing rerun; the code fix and next CI result were still pending at
  this point in the work.
- `bash -n scripts/demo-local.sh`, Ruby YAML parsing of `.github/workflows/ci.yml`,
  and `git diff --check` pass after the diagnostics and trigger change. No demo rerun
  has been performed yet.
- The single diagnostic CI run confirmed that the CPU ONNX runtime target returned
  `{"detail":"model tokenizer unavailable"}`. `GatewayService` had selected the
  tokenizer path by adapter class, but the local ONNX service also uses the HTTP
  adapter. Tokenizer preflight now follows the catalog's explicit `runtime: vllm`
  declaration; a misconfigured vLLM route fails closed. A regression test verifies
  that an HTTP-backed ONNX model does not call `/tokenize`.
- After correcting a positional `Usage` fixture in the new regression test,
  `make verify` passed: **73 passed, 2 optional Redis skips**, one existing
  deprecation warning, no known dependency vulnerabilities, and Compose configuration
  passed. This was the local result before the code fix was pushed.
- Commit `ee4b46c` passed all four jobs in the single PR-triggered workflow
  `45923987903`, including the fresh-runner `local-e2e` job. The streaming demo that
  previously failed now passed. This verifies one local CPU end-to-end cycle; it does
  not claim live vLLM, AWS, or GPU execution.
- Evidence and official source notes are indexed in `docs/gpu-lab/VALIDATION.md`,
  `docs/gpu-lab/EVIDENCE_MANIFEST.md`, and `docs/gpu-lab/RESEARCH_NOTES.md`.

## Acceptance status

**Partially complete.** The local token preflight, bounds, Redis reservation adjustment,
and tests pass. Live vLLM compatibility, private Compose-network reachability, cache
salting, and timeout/cancellation/outage drills remain outstanding. Mock tests do not
prove the deployed runtime protocol.
