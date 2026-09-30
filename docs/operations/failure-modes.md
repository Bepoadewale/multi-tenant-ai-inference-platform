# Failure modes

Flagship context: release, simulated-capacity, request-level operational-evidence, and
governed remediation slices are executed locally. Agent-tool slices must add their own
failure scenarios rather than relying on this core-gateway list.

vLLM crash/node loss/model load failure: readiness removes targets; router stops routing and returns bounded 503 when no fallback exists. Slow backends: timeout/circuit state avoids retry storms. GPU OOM: quarantine/restart and reduce unsafe concurrency/context configuration after diagnosis. Redis failure: fail closed for distributed quota admission. Prometheus failure must not block serving. Scheduling/capacity failure leaves rollouts pending; never silently substitute CPU.

Simulated capacity exhaustion: the gateway returns a controlled 429 for a tenant slot
limit or a full/bounded capacity queue. A model that explicitly permits CPU fallback
can continue on real local ONNX CPU; a capacity-required model does not silently fall
back. This is scheduling-policy evidence, not GPU failure evidence.

Client disconnect during streaming cancels upstream work where the runtime supports it; do not replay a stream. Duplicate non-streaming requests should use client request IDs/idempotency policy only where semantics allow.

Bounded backend timeout: the request receives a controlled 502 and an
`X-Request-ID`. Its metadata-only usage record is retained with `outcome=backend_error`
and the local request SLO evaluates it as `VIOLATED`; the raw prompt and output are not
retained. For an active `chat-default` canary, that metadata-only failure can create a
governed remediation incident. The controller refuses successful requests, unknown
models, or non-canary release context. A plan whose Redis weights or release state
changed is rejected as stale; self-approval is denied; per-model cooldown/action budget
rejects repeat action; and verification failure leaves the incident failed rather than
claiming recovery. The executed local demo proves a candidate runtime outage,
independent approval, bounded stable rollback, controller restart recovery, and
post-action real ONNX inference.

## Local troubleshooting runbook

| Symptom | Check | Safe response |
| --- | --- | --- |
| console or gateway refuses connection | `make status` then `make smoke` | run `make bootstrap-local`; do not hand-start partial containers |
| token is rejected | confirm `.local/identity/tokens.json` exists and rerun `make bootstrap-local` | local tokens are short-lived; never paste them into issues or docs |
| request is `429` | inspect the tenant's quota and bounded queue evidence in the console | wait for the window or use an assigned tenant; do not bypass Redis admission |
| request is controlled `502` | run `make demo-failure` or `make demo-timeout` to reproduce | inspect metadata-only analysis/trace; do not replay side-effecting requests |
| candidate rollout is unhealthy | use release/remediation evidence and the bounded rollback flow | never mutate Redis weights manually |
| local state seems stale | `make clean-local`, then `make install`, `make bootstrap-local`, `make smoke` | cleanup is project-scoped; it does not prune unrelated Docker resources |

Use readiness checks rather than arbitrary sleeps. If the reproducible sequence fails,
capture the command output and update validation evidence before changing a claim.
