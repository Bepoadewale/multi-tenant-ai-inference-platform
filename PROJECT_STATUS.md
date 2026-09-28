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
- Clean-room workflow passed twice: bootstrap, smoke, successful inference, bounded timeout failure, validation, project-scoped cleanup, then a second bootstrap/demo.

## Implemented but Not End-to-End Validated

- CPU-safe local stack and its failure/recovery paths are validated. Production vLLM, GPU, and Kubernetes adapters remain static contracts.

## Simulated

- No CPU backend generation is simulated: the local classifier is a real ONNX model. The `simulated-l40s` pool is Redis quota accounting only. GPU/DCGM/KV-cache behavior and production cost allocation remain unexecuted. Request cost is a versioned local fixture estimate, not billing.

## Architecture / Contracts Only

- GPU serving, Kubernetes/EKS deployment/autoscaling, real cloud model hosting, and production durable metering/outbox.

## Known Failures

- None known. Required PR checks were green at the latest validated revision; future commits still require green CI.

## Current P0 Objective

Add governed remediation: use observed incident evidence to create a bounded, policy-gated action and verify recovery without weakening the existing serving path.

## Completion Blockers

- None for the existing inference-core completion gate.
- Remediation, secure-agent,
  developer-self-service and optional edge slices are not yet executed here.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.

## Last Validation

- `make lint`, `make test`, `make smoke`, `make demo-model-registry`, `make demo-release-control`, `make demo-capacity`, and `make demo-operational-evidence`: passed locally. The operational-evidence demo correlated a live request during a canary with a Tempo trace, release plan, local SLO and explicit fixture cost; it also persisted an actual timeout as an SLO violation.
- `make demo-local`, `make demo-overload`, `make demo-routing`, `make demo-metering`, `make demo-observability`, `make demo-failure`, `make demo-timeout`, and `make demo-recovery`: passed against the Docker stack.
- PR #4 GitHub checks: `python`, `manifests`, `supply-chain`, and `local-e2e` passed.

## Last Updated

2026-09-28, operational-evidence slice validated on `codex/flagship-operational-evidence`; final GitHub CI evidence will be recorded before review.

## Clean-Room Reproducibility

**Status: VALIDATED**

Historical core clean-room validation remains recorded below. The operational-evidence
slice additionally completed two clean-room cycles on 2026-09-28: each ran installation,
bootstrap, every core/release/capacity/operational demo, `make verify`, and safe cleanup.
Post-cleanup checks confirmed project Compose resources, `.local`, and `.venv` were absent.
After the CI timing fix, two additional clean boot → operational-evidence demo → cleanup
cycles passed; one also ran `make verify`.
