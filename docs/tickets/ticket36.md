# Ticket 36 — vLLM preflight failure and cancellation cleanup

## Objective

Prove that interrupted tokenization and unavailable shared admission stop inference
without leaking the request reservation or the gateway's simulated capacity slot.
Also verify that tokenizer transport timeouts use the bounded timeout configured for
the vLLM preflight.

## Current state

- Branch: `codex/vllm-preflight-failure-cleanup`, based on ready PR #35.
- Phase: non-billable Phase 6 failure-path tests. No AWS, GPU, or live vLLM was used.
- The earlier CI failure and recovery are recorded in ticket #35 and the execution
  journal. This package adds focused coverage for the remaining timeout, cancellation,
  and Redis outage paths.

## Implementation tasks

- [x] Cancel a request while `/tokenize` is waiting; verify reservation, active count,
  and simulated capacity are released.
- [x] Simulate Redis admission unavailability; verify the request fails with 503 and
  capacity is released before inference.
- [x] Simulate an HTTPX tokenizer read timeout; verify it uses the configured short
  timeout and returns the adapter's generic failure without leaking request data.
- [x] Keep the tests deterministic and local; no external Redis server is required.
- [ ] Confirm the tests and documentation in the PR workflow.

## Validation and evidence

- `make verify` passed: Ruff, **76 passed, 2 optional Redis skips**, no known audited
  vulnerabilities, and Docker Compose configuration.
- One existing Starlette deprecation warning remains.
- The tests exercise local fakes and HTTPX `MockTransport`; they do not prove a real
  Redis network partition, a live vLLM timeout, AWS, GPU behavior, or production
  recovery.

## Security and cost boundaries

The fake Redis error is generated locally and contains no credentials or customer
data. The gateway continues to return generic public errors. No cloud mutation or
billable resource was used.

## Outstanding work

Private vLLM networking, cache-salt support, multi-process Redis integration during
preflight, and real `/tokenize` compatibility remain for the authorized runtime
package. This ticket does not complete Phase 6.

## Acceptance status

Local failure-path coverage is complete. PR review and CI remain pending.
