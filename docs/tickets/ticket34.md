# Ticket 34 — Redis-backed request reservations and lease recovery

## Objective

Make the gateway reserve estimated token usage and concurrency capacity per request,
then reconcile quota records with backend-reported token usage when available. Ensure
stale active slots from a crashed request expire and active long requests renew their
leases. Keep the existing in-memory implementation for local use and tests.

## Current state

- Branch: `codex/redis-admission-leases`, rebased onto PR #33 head `c5de757`; lease fixes are in code commit `4cffc60`.
- Pull request: [#34 — request-scoped Redis admission leases](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/34), open against `codex/gateway-stream-accounting` (PR #33); the rebase and review fixes are recorded in the current branch history.
- Phase: non-billable Phase 6 prework. The active cloud phase remains Phase 2, with the
  AWS GPU launch gated by the pending quota request and the $25/apply checks.
- No AWS infrastructure, GPU, or live vLLM server was used.

## Current behavior and design

The limiter returns an `AdmissionReservation` containing a unique request ID and the
initial token estimate. Redis stores that estimate in rolling one-minute and one-day
ledgers and tracks active requests in an expiry-scored sorted set. This replaces the
old scalar concurrency counter, which could remain stuck after a process crash.

The gateway renews a long-running reservation in the background. If renewal fails or
Redis reports that the lease no longer exists, the owning request is cancelled so the
gateway does not continue serving work after losing its admission reservation. On
release, backend-reported usage replaces the estimate in both rolling token ledgers.
If usage is unknown, the estimate remains for the full quota window to avoid silently
under-counting. Release is idempotent by request ID.

Redis scripts keep the quota decision, reservation, lease, and release atomic across
limiter clients. The integration tests use two clients connected to one local Redis
server. This is shared local state, not proof of separate gateway processes or AWS.

Renewal now has a deadline of one third of the lease after sleeping for one third of
the lease. If Redis does not reply in that time, the gateway cancels the owner while
one third of the lease remains. A renewal also refuses to revive an already-expired
lease. Each new admission removes reservation metadata for expired leases, while the
minute/day token-ledger entries remain until their rolling quota windows expire. This
keeps quota accounting conservative if the request died before usage reconciliation.

## Implementation tasks

- [x] Add an `AdmissionReservation` type and request-specific in-memory accounting.
- [x] Reserve estimated tokens in the rolling minute and daily windows.
- [x] Use expiring request leases for concurrent-request limits.
- [x] Add renewal and fail-closed gateway behavior when renewal fails.
- [x] Bound an unresponsive lease renewal and cancel its owner before the lease expires.
- [x] Remove expired request metadata independently while retaining conservative token
  ledger entries until their quota windows expire.
- [x] Reconcile known backend token use once; preserve estimates when use is unknown.
- [x] Add idempotent Redis release and crash-expiry tests across two limiter clients.
- [x] Test that an unresponsive renewal cancels the request owner before its lease
  deadline.
- [x] Configure Python CI with a Redis service so integration tests run instead of skip.
- [ ] Add gateway-level tests for heartbeat cancellation, disconnect before stream start,
  backend timeout, Redis outage, and exact capacity release behavior.
- [ ] Validate measured usage and streaming behavior against a pinned live vLLM build.
- [ ] Add tokenizer-aware prompt/context bounds and test model-specific limits.
- [ ] Run the existing full validation and Redis integration tests in CI after opening
  the pull request.

## Research and references

Redis Lua scripting is used because the server runs each script atomically, avoiding
a race where two gateway replicas both observe spare capacity. Sorted-set scores hold
request timestamps or lease expiry times so scripts can remove expired entries by
score. Redis key expiry bounds temporary queue/reservation records. See the official
[Lua scripting](https://redis.io/docs/latest/interact/programmability/eval-intro/),
[sorted-set](https://redis.io/docs/latest/develop/data-types/sorted-sets/), and
[expiry](https://redis.io/docs/latest/commands/expire/) references. The local test
does not claim production persistence, replication, or failover behavior.

## Commands executed and results

- `.venv/bin/ruff check gateway/src gateway/tests/test_vllm_streaming.py gateway/tests/test_redis_admission_leases.py gateway/tests/test_tenant_limiter_reservations.py` — passed.
- `.venv/bin/pytest -q` — latest full suite **62 passed, 2 skipped**, one existing Starlette deprecation warning. The two skips are opt-in tests requiring Redis.
- `REDIS_TEST_URL=redis://127.0.0.1:16379/15 .venv/bin/pytest -q gateway/tests/test_redis_admission_leases.py` — **2 passed** against a disposable local Redis 7.4 container.
- `make verify` — passed after updating the ignored local virtual environment's pip
  from 25.3 to 26.3; Ruff, tests, and `pip-audit` passed. The first run identified
  ten current advisories in the local pip 25.3 tool and later exhausted the audit
  registry retries. No repository dependency pin changed for that local tool.
- Review found a local deque-ordering issue when reconciling an older token entry;
  reconciliation now updates the entry in place. Negative reported usage retains the
  estimate. The regression test was added, and the latest `make verify` passed with
  **62 tests passed and 2 optional Redis skips**.
- GitHub Actions Python workflow now declares a Redis 7.4 service and sets
  `REDIS_TEST_URL`; both PR #34 workflow runs passed all four check groups at head
  `1188a86`.

## Issues discovered and troubleshooting

The first Redis integration run failed during test cleanup because the asynchronous
Redis clients were closed from event loops different from the loops that created them.
The tests now create and close both clients inside one `asyncio.run` loop. A rerun
passed both tests. This was a test-lifecycle bug, not a production-code workaround.

The queue counter remains a separate bounded queue mechanism. Redis errors while
releasing a queue slot are tolerated because its key has a 60-second expiry; the
follow-up review should confirm this behavior remains bounded under cancellation.

## Security and financial considerations

Only synthetic tenant IDs and token counts are written by these tests. No prompts,
responses, credentials, or account data are stored. The temporary Redis container is
local and disposable. No cloud resources or charges were created. The project AWS
ceiling remains $25; quota approval does not authorize an AWS apply.

## Evidence collected

See `docs/gpu-lab/VALIDATION.md` and `docs/gpu-lab/EVIDENCE_MANIFEST.md`. Evidence is
classified as local execution against one Redis process and is not real AWS or GPU
evidence.

## Outstanding work and acceptance status

**Acceptance: partial.** Source tests and local Redis integration pass. The full
multi-tenant GPU acceptance criteria require gateway behavior across replicas and
real vLLM-backed inference on the authorized L4; neither has been exercised. Review
gateway cleanup paths, finish PR/CI, then proceed with independent non-billable work
while the quota request is pending.

## Review follow-up — 2026-11-27

Automated review identified two lease-lifecycle gaps. A Redis renewal command could
hang longer than the active lease; it now has a bounded await, and the request owner is
cancelled before another replica can reuse the slot. Expired reservation hash fields
could also accumulate when tenants stayed active; admission now removes metadata for
expired leases without deleting their conservative token ledger entries. Direct renew
of an already-expired lease also fails and removes its stale metadata.

After these changes, `make verify` passed Ruff, **75 tests**, dependency audit, and
Compose validation; two opt-in Redis tests were skipped in that run. A disposable local
Redis 7.4 container then ran the lease/renewal suite: **7 passed**, including repeated
crash recovery and orphan-field cleanup. The container was stopped after the test.
No AWS resource, GPU, or live vLLM process was used.
