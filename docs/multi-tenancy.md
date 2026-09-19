# Multi-tenancy

Tenant identity comes from authenticated credentials, never an untrusted header. Each tenant has allowed aliases, request/token/minute, concurrency, daily token budget, priority, environment, and cost center. Admission checks fail closed. The local limiter is deterministic for tests; Redis Lua scripts are the production distributed implementation so multiple gateway replicas share quota state.

Shared inference enables continuous batching but needs fairness limits and queue bounds. Dedicated pools trade GPU utilization for isolation/predictable latency; route a dedicated tenant to its own model deployment after authorization.
