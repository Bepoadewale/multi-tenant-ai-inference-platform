# Project Status

## Current Maturity

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE for the multi-tenant inference core.

The repository is now the public flagship. Flagship integrations are planned work and
must not be represented as executed until they have their own local evidence.

## Maturity Model

`FOUNDATION` → `PARTIALLY VALIDATED` → `LOCAL END-TO-END VALIDATED` → `PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE`.

## Executed and Verified

- Two independent FastAPI gateways authenticate Ed25519 JWTs and derive tenant/role server-side.
- Redis Lua admission enforces shared request, token, concurrency, daily-budget, and bounded queue limits across both gateways.
- Two Dockerized CPU ONNX Runtime targets return real deterministic classifier output through the OpenAI-compatible and SSE paths.
- A local MLflow server records stable and candidate ONNX artifacts with real SHA-256 digests, CPU fixture evaluation metrics, and `champion`/`candidate` aliases.
- Release control persists SQLite plans, binds them to MLflow versions/digests, requires a distinct `release.approve` identity, uses Redis-shared canary weights across gateways, and verifies promotion and rollback with live ONNX traffic; a stale transition is rejected in tests.
- Redis-shared simulated-capacity admission enforces a fixed local pool and tenant allocation. The demo proves admission, bounded waiting, tenant quota rejection, and an explicit CPU fallback; all inference still runs through CPU ONNX Runtime.
- Admin-controlled weighted routing reaches the selected candidate runtime; ordinary tenant and agent identities cannot administer rollouts.
- Redis metering stores metadata-only usage and survives a gateway restart.
- OTel Collector, Tempo, Prometheus, and Grafana receive generated local gateway traffic.
- A platform-admin-only request-analysis API retrieves Redis-backed, metadata-only
  evidence linking a real request to its Tempo trace ID, selected target/version,
  active release plan/phase, local fixture SLO, and Decimal-calculated local token
  estimate. A real bounded backend timeout persists as an SLO violation.
- A separate remediation-control service consumes a real metadata-only failed canary
  request, persists a SQLite incident/plan/timeline, requires a distinct
  `remediation.approve` JWT, rechecks exact Redis/SQLite rollout state, applies only
  the bounded stable rollback, verifies real ONNX recovery, and survives controller
  restart. Its cooldown/action budget blocks repeat remediation loops.
- A separate delegated-agent-tools service validates a five-minute Ed25519 agent JWT,
  filters discovery to same-tenant evidence and canary-plan preparation, denies
  cross-tenant evidence, and persists metadata-only hashed tool-call audit records.
  The agent cannot approve or execute the resulting remediation plan.
- Clean-room workflow passed twice: bootstrap, smoke, cumulative flagship demos,
  validation, project-scoped cleanup, then a second bootstrap/demo.

## Implemented but Not End-to-End Validated

- CPU-safe local stack and its failure/recovery paths are validated. Production vLLM, GPU, and Kubernetes adapters remain static contracts.

## Simulated

- No CPU backend generation is simulated: the local classifier is a real ONNX model. The `simulated-l40s` pool is Redis quota accounting only. GPU/DCGM/KV-cache behavior and production cost allocation remain unexecuted. Request cost is a versioned local fixture estimate, not billing.

## Architecture / Contracts Only

- GPU serving, Kubernetes/EKS deployment/autoscaling, real cloud model hosting, and production durable metering/outbox.

## Known Failures

- None known. Required PR checks were green at the latest validated revision; future commits still require green CI.

## Current P0 Objective

Add developer self-service through a narrow, validated golden-path contract without
turning this repository into a portal rewrite.

## Completion Blockers

- None for the existing inference-core completion gate.
- Developer-self-service and optional edge slices are not yet executed here.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.

## Last Validation

- Delegated-agent slice: two clean bootstrap → smoke → `make demo-agent-tools` →
  teardown cycles passed on 2026-09-28. The live demo exercised filtered discovery,
  same-tenant evidence, cross-tenant denial, plan-only authority, independent
  approval/execution, Prometheus tool metrics, durable hashed audit, service restart,
  and real stable-ONNX recovery. Static validation after the second run passed Ruff,
  37 pytest tests, and Compose configuration. The full all-slice clean-room rerun is
  still an explicit flagship completion item.
- Two clean-room cycles on the governed-remediation revision passed. Both started from
  `make clean-local`, ran `make install`, `make bootstrap-local`, `make smoke`, core
  and cumulative flagship demos including `make demo-remediation`, `make verify`, and
  `make clean-local`. The remediation demo created a real candidate-runtime outage,
  persisted an incident, denied self-approval, accepted independent approval, rolled
  traffic back to stable, verified ONNX inference, and recovered its audit after a
  controller restart.
- `make demo-local`, `make demo-overload`, `make demo-routing`, `make demo-metering`, `make demo-observability`, `make demo-failure`, `make demo-timeout`, and `make demo-recovery`: passed against the Docker stack.
- PR #4 GitHub checks: `python`, `manifests`, `supply-chain`, and `local-e2e` passed.

## Last Updated

2026-09-28, governed-remediation slice validated on
`codex/flagship-agent-tool-governance`; this slice's second clean-room cycle and final
GitHub CI evidence will be recorded before review.

## Clean-Room Reproducibility

**Status: VALIDATED**

Historical core and operational-evidence validation remains recorded below. The
governed-remediation slice completed two clean-room cycles on 2026-09-28. Both ended
with no project Compose resources, `.local`, or `.venv`; the second bootstrap ran after
the first cleanup.
