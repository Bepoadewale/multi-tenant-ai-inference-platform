# Incident: local Redis outage returned HTTP 500

## 1. Incident details

- **Identifier:** `INCIDENT-LOCAL-REDIS-001`
- **Date and time:** 2026-11-27 20:57:42 UTC
- **Environment:** GitHub Actions local end-to-end runner; Docker Compose CPU stack
- **Phase:** Phase 6 integration preparation and Phase 10 incident practice
- **Affected components:** gateway `gateway-1`, the shared Redis service, and the
  gateway's shared rollout-state reader
- **GPU/AWS impact:** none; this was not a GPU host or AWS incident
- **Status:** root cause identified and code fix plus unit tests prepared; the fixed
  end-to-end drill still needs a new CI run

## 2. Expected behavior

The test deliberately stops only the project's Redis container. A chat request must
fail closed with HTTP 503 because the gateway cannot confirm shared rollout state
before routing or admission. After Redis starts again, both gateway replicas must
report admission readiness.

## 3. Fault injection

The new `make demo-redis-outage` drill first checks that the local stack is healthy,
then runs `docker compose stop redis`. It sends an authenticated request to port 8081
and expects HTTP 503 with the shared-admission error. An exit trap starts Redis and
waits for Redis `PING`, even when an assertion fails.

The drill had not reached gateway 8082 or its post-recovery readiness assertions when
the first gateway returned the wrong status.

## 4. Observed behavior and detection

GitHub Actions run [`46066808334`](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/actions/runs/46066808334),
job `local-e2e`, recorded:

- `gateway-1` returned HTTP **500** where the test expected HTTP 503.
- The failure was detected by the explicit status assertion in
  `scripts/demo-redis-outage.sh`.
- The script's exit trap issued `docker compose start redis`; the Redis container
  started and passed the script's `redis-cli ping` recovery loop. Gateway readiness
  after recovery was not reached in this failed run.
- There was no Alertmanager or production alert. The test was running in the local
  CI stack, which has no live AWS/GPU monitoring incident.
- The failure script originally printed the status but not the response detail or
  server traceback. It now prints a sanitized JSON detail for future diagnosis.

The same CI job had already passed ten client-cancelled streaming requests across
both gateway processes. The process-local active-request metric and shared Redis
lease count returned to zero after each cancellation.

## 5. Investigation and root cause

The request reaches `GatewayService.chat`, which reads the shared rollout configuration
before it attempts Redis-backed admission. `RolloutStore.get_context` used a
synchronous Redis client without catching connection errors. When Redis was stopped,
that exception escaped the API handler and FastAPI returned HTTP 500. The later
admission code correctly maps Redis errors to 503, but it was never reached.

The same review found that rollout updates changed process-local target weights before
writing shared Redis state. If that write failed, one gateway could retain a routing
change that its peer could not see.

## 6. Alternatives considered

- Treat Redis outage as an empty rollout: rejected because the gateway cannot know
  whether shared routing intent exists, and silently using local state could split
  routing between replicas.
- Return a generic HTTP 500: rejected because it hides a known dependency outage and
  prevents clients and operators from distinguishing it from an application defect.
- Return HTTP 503 and fail closed: selected because shared routing and admission
  state are required to make a safe decision.

## 7. Fix prepared

- Map Redis errors from shared rollout reads and writes to HTTP 503 with the generic
  message `shared rollout state unavailable`.
- Persist rollout changes before mutating process-local target weights. A failed
  Redis write leaves both local weights and the audit list unchanged.
- Add tests for a failed shared-state read and a failed rollout write.
- Keep the end-to-end Redis outage drill checking both replicas, the exact 503 detail
  `shared rollout state unavailable`, Redis recovery, and post-recovery gateway
  readiness.

## 8. Validation and recovery

- Targeted local command: `.venv/bin/python -m pytest -q
  gateway/tests/test_rollouts.py gateway/tests/test_api.py` — **10 passed**.
- Ruff passed for the changed gateway source and tests.
- The initial run verified that the Redis service starts again and passes `PING` in
  the exit trap, but it did not verify gateway readiness because the expected-503
  assertion failed first.
- The fixed full outage drill has not yet run. The next PR workflow is the recovery
  verification gate.
- **Measured recovery duration:** not available. The first run logged container
  `Starting` and `Started`, but did not retain the time of the successful Redis `PING`
  or gateway readiness.

## 9. Preventive improvements

- All Redis-backed control paths used before routing must map dependency errors to a
  documented 503 and avoid silently selecting stale local state.
- Persist shared control-plane state before changing process-local routing state.
- Keep two-replica outage and cancellation drills in CPU-only local CI so they can be
  run before an L4 is approved.
- Preserve response detail only when it is a generic, sanitized dependency message;
  never log bearer tokens or prompts.

## 10. Production implications and limitations

This controlled CI fault exposed an availability bug before an AWS deployment. HTTP
503 lets clients distinguish temporary dependency unavailability and apply bounded
retry policy. It does not make Redis highly available, protect against a Redis data
loss, or establish production recovery time. The local test uses one Redis container
and two gateway processes on one host; it does not prove multi-AZ resilience or GPU
failure recovery.

## References

- [PR #58](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/58)
- [Failing CI run `46066808334`](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/actions/runs/46066808334)
- `scripts/demo-redis-outage.sh`
- `scripts/demo-gateway-cancellation.py`
- `gateway/src/inference_gateway/routing/rollout_store.py`
- `gateway/src/inference_gateway/services/gateway.py`
- `gateway/tests/test_rollouts.py`
