# Ticket 33 — vLLM streaming usage and gateway cancellation accounting

## Objective

Improve the local gateway-to-vLLM streaming boundary before live GPU integration.
Parse actual vLLM usage when available, preserve OpenAI-compatible usage semantics,
measure the gateway's first-content delay, distinguish measured usage from estimates,
and record cancellation/error outcomes exactly once.

## Current state

- Branch: `codex/gateway-stream-accounting`, based on PR #32 commit `24336cf` (ready for review); implementation commit `1186e30`.
- Phase: local work supporting Phase 6; Phase 2 remains the active cloud phase.
- No vLLM server, AWS resource, or GPU was used for this ticket.
- AWS G/VT request for 4 vCPUs is pending. Applied quota remains zero.

## Research and design

vLLM documents that a streaming chat request must set
`stream_options.include_usage=true` to receive a final usage-only chunk with
`choices: []`; the chunk follows generated content. See the [official vLLM
per-request metrics guide](https://docs.vllm.ai/en/latest/features/per_request_metrics/).

The adapter therefore asks upstream vLLM for usage on every streaming request. It
emits content and usage as separate internal events. The gateway records backend
usage as `backend_reported`, or a word-based fallback as `gateway_estimate`. It sends
the final usage-only chunk to the client only when the client requested
`stream_options.include_usage`. First-content time is measured at the gateway from the
request's start, so it includes routing/admission and downstream startup. Non-streaming
backend duration is no longer mislabeled as TTFT.

## Implementation tasks

- [x] Add an internal content/usage event for streamed backend data.
- [x] Request, parse, and validate vLLM's final streaming usage chunk.
- [x] Expose OpenAI-compatible client `stream_options.include_usage` handling.
- [x] Count fallback output words across the complete emitted text rather than network
  chunks; mark that usage as estimated.
- [x] Measure first-content delay and record cancellation or stream errors.
- [x] Add mock-transport tests for final usage and malformed events, plus gateway tests
  for measured usage, TTFT, client usage chunks, stream failure, and cancellation
  cleanup.
- [ ] Test with a pinned live vLLM build and verify its actual SSE response.
- [ ] Add Redis integration tests and crash-safe per-request concurrency leases.
- [ ] Reconcile actual usage against quota reservations exactly once; define handling
  for partial output, upstream failure, and usage-less backends.
- [ ] Add tokenizer-aware prompt/context bounds before paid GPU use.

## Validation

- Ruff for gateway source and the new tests: passed.
- Targeted tests: 8 passed.
- Full local suite: 58 passed, one existing Starlette `TestClient` deprecation warning.
- Test initialization first failed because `.venv` and the ignored ONNX fixture were
  absent. A Python 3.12 project environment was installed and the repository's model
  generator created the missing ignored local fixture. No tracked model artifact was
  changed.
- One initial assertion expected bytes from a direct `StreamingResponse.body_iterator`
  but it yields strings in this unit-test path. The assertion was corrected to check
  the text representation; the final targeted and full suites passed.
- The first fake Redis-pipeline test did not model the client's positional `hset`
  overload and failed before checking the serialized field. The fake was updated to
  accept both call forms; the Redis serialization test and all final tests passed.

## Security, cost, and limitations

Tests use synthetic text only. The new usage-source field contains no prompt or output
content. The local in-memory cancellation test does not prove Redis cleanup across
replicas or recovery after a gateway process crash. The backend's word-count fallback
is not tokenizer-accurate. No measured vLLM TTFT or GPU performance is claimed.

No AWS resource was created or changed. Spend and GPU hours remain `$0`; the `$25`
ceiling and separate apply gate remain in effect.

## Next step

Complete the Redis reservation/lease design and tests as a separate focused package,
then validate this protocol against the pinned vLLM runtime after authorized GPU
infrastructure is available.
