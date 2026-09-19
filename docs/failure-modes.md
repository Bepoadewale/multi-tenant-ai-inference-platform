# Failure modes

vLLM crash/node loss/model load failure: readiness removes targets; router stops routing and returns bounded 503 when no fallback exists. Slow backends: timeout/circuit state avoids retry storms. GPU OOM: quarantine/restart and reduce unsafe concurrency/context configuration after diagnosis. Redis failure: fail closed for distributed quota admission. Prometheus failure must not block serving. Scheduling/capacity failure leaves rollouts pending; never silently substitute CPU.

Client disconnect during streaming cancels upstream work where the runtime supports it; do not replay a stream. Duplicate non-streaming requests should use client request IDs/idempotency policy only where semantics allow.
