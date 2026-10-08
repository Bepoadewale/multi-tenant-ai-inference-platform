# Observability, SLOs, and FinOps

## Executed request evidence

`make demo-operational-evidence` proves a request-level evidence path across the
existing local stack. A live request while the shared canary is active stores its release plan
and phase, captures the current OpenTelemetry trace ID, reaches Tempo, and is exposed
through the platform-admin request-analysis endpoint with the real route/version,
token usage, an explicit local fixture SLO result, and a versioned estimated cost.
The demo also invokes the bounded timeout fixture: its `backend_error` record is
retained as an SLO violation rather than being lost as a 502.

Gateway metrics cover requests/outcomes, prompt/completion tokens, throttles, active requests,
queue depth/wait, end-to-end latency, TTFT, and simulated-capacity decisions/allocation/queue depth.
They also include `inference_gateway_estimated_cost_usd_total`,
`inference_gateway_request_slo_evaluations_total`, and
`inference_gateway_release_correlated_requests_total`. Cost and SLO labels are local
fixture evidence; no physical GPU or provider billing telemetry is implied.
Local Compose exports OTLP through the Collector to
Tempo and exposes Prometheus metrics; generated demo traffic is queryable in both systems. The
executed trace surface is FastAPI request and HTTP client instrumentation, with request correlation
where provided. Explicit child spans for admission, routing, backend call, and metering are
production observability hardening rather than executed local evidence. vLLM `/metrics` and DCGM
Exporter would supply serving/GPU telemetry in GPU mode, which is not executed here. Capacity
metrics label the local pool as simulated and must not be read as DCGM or physical utilization.

The executed request evaluator uses a 750ms latency and 600ms TTFT fixture threshold,
plus successful outcome, to make the demo deterministic. These are **not** production
SLO commitments. Production objectives must be agreed per workload and use aggregated
error-budget windows. Dashboard views should answer: who is throttled, where tail
latency originates, which model is saturated, and—in actual GPU deployments—what
hardware telemetry says about capacity.

## FinOps evidence boundary

`make demo-operational-evidence` sends a real request through a verified canary and
retrieves metadata-only request analysis. The analysis is correlated to model,
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

## Planned cloud-pilot evidence — not executed

CP6 must turn the following design into recorded AWS evidence before this repository
can claim a cloud pilot. It must not be inferred from the local stack or Terraform
contracts alone.

| Concern | Pilot evidence required |
| --- | --- |
| Metrics and dashboards | Prometheus scrapes the deployed gateway and supporting services; Grafana shows tenant admission, queueing, route/version, release state, errors, latency, and availability. |
| Traces and audit | The deployed request path exports OTel traces to Tempo (or the selected tracing backend) and correlates only metadata-safe request, release, and audit records. |
| Alerting | A deliberately injected bounded failure causes a defined alert to fire; alert routing and acknowledgement are recorded without claiming an on-call service. |
| Availability | Two or more gateway replicas and a PDB are deployed. Deleting one pod proves traffic and readiness continue through the remaining replica, then return to the desired replica count. |
| Recovery | A known-bad candidate image or bounded backend failure produces a visible unhealthy state and uses the governed known-good rollback path. Redis admission remains fail-closed when shared admission is unavailable. |
| Load | A short bounded authenticated load sample records duration, concurrency, request count, outcomes, and environment. It is availability evidence, not a benchmark or capacity claim. |
| Cost | Cost Explorer queries include account, region, tag/filter, query time, and result status. Values are labelled estimated until AWS publishes settled billing data, commonly 24–48 hours later. |

The intended operational order is documented in the [cloud-pilot runbook](../cloud-pilot-runbook.md).
