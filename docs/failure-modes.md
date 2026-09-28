# Failure modes

Flagship context: release and simulated-capacity slices are executed locally; remediation
and agent-tool slices must add their own failure scenarios rather than relying on this
core-gateway list.

vLLM crash/node loss/model load failure: readiness removes targets; router stops routing and returns bounded 503 when no fallback exists. Slow backends: timeout/circuit state avoids retry storms. GPU OOM: quarantine/restart and reduce unsafe concurrency/context configuration after diagnosis. Redis failure: fail closed for distributed quota admission. Prometheus failure must not block serving. Scheduling/capacity failure leaves rollouts pending; never silently substitute CPU.

Simulated capacity exhaustion: the gateway returns a controlled 429 for a tenant slot
limit or a full/bounded capacity queue. A model that explicitly permits CPU fallback
can continue on real local ONNX CPU; a capacity-required model does not silently fall
back. This is scheduling-policy evidence, not GPU failure evidence.

Client disconnect during streaming cancels upstream work where the runtime supports it; do not replay a stream. Duplicate non-streaming requests should use client request IDs/idempotency policy only where semantics allow.
