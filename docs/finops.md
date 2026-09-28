# FinOps

## Executed local evidence

`make demo-operational-evidence` sends a real request through a verified canary and
retrieves its metadata-only request analysis. The analysis is correlated to model,
backend/version, release plan/phase, token usage, local SLO result, and Tempo trace
ID. Cost is calculated with `Decimal` from the versioned
`local-fixture-2026-09-v1` price catalog:

- prompt tokens: $0.20 per million;
- completion tokens: $0.80 per million.

The response labels its cost `ESTIMATED_LOCAL_TOKEN_ALLOCATION`. It is a transparent
local allocation signal, **not** a provider bill, invoice, realized margin, GPU-hour
cost, or cloud price. Prometheus exposes the accumulated estimate as
`inference_gateway_estimated_cost_usd_total`.

Usage records contain tenant/model/backend/version/token/latency/outcome and release
metadata, but never prompt or completion text. The direct request record is bounded
with a seven-day Redis TTL. Production allocation should incorporate versioned cloud
prices, GPU-hours, commitments, utilization, replicas, and tenant/model/cost-center
policy; those inputs are not executed here.
