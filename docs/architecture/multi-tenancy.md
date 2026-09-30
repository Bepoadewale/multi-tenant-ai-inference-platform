# Multi-tenancy

Flagship context: tenant isolation remains the boundary every later release, capacity,
agent and edge integration must preserve.

Tenant identity comes from authenticated credentials, never an untrusted header. Each tenant has allowed aliases, request/token/minute, concurrency, daily token budget, priority, environment, cost center, and simulated-capacity-slot limit. Admission checks fail closed. The local limiter is deterministic for tests; Redis Lua scripts implement the shared local admission path so multiple gateway replicas share quota state.

Shared inference enables continuous batching but needs fairness limits and queue bounds. The current `simulated-l40s` pool is a small Redis-accounted local fixture: it demonstrates admission behavior rather than accelerator performance. Dedicated pools trade GPU utilization for isolation/predictable latency; route a dedicated tenant to its own model deployment after authorization.
