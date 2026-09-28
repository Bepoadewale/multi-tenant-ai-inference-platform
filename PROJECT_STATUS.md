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
- Admin-controlled weighted routing reaches the selected candidate runtime; ordinary tenant and agent identities cannot administer rollouts.
- Redis metering stores metadata-only usage and survives a gateway restart.
- OTel Collector, Tempo, Prometheus, and Grafana receive generated local gateway traffic.
- Clean-room workflow passed twice: bootstrap, smoke, successful inference, bounded timeout failure, validation, project-scoped cleanup, then a second bootstrap/demo.

## Implemented but Not End-to-End Validated

- CPU-safe local stack and its failure/recovery paths are validated. Production vLLM, GPU, and Kubernetes adapters remain static contracts.

## Simulated

- No CPU backend generation is simulated: the local classifier is a real ONNX model. GPU/DCGM/KV-cache behavior and production cost allocation remain unexecuted.

## Architecture / Contracts Only

- GPU serving, Kubernetes/EKS deployment/autoscaling, real cloud model hosting, and production durable metering/outbox.

## Known Failures

- None known. Required PR checks were green at the latest validated revision; future commits still require green CI.

## Current P0 Objective

Add the next flagship vertical slice: an explicitly simulated-GPU capacity and admission decision that is exercised by the local serving path.

## Completion Blockers

- None for the existing inference-core completion gate.
- Capacity, SLO/FinOps, remediation, secure-agent,
  developer-self-service and optional edge slices are not yet executed here.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.

## Last Validation

- `make lint`, `make test`, `make smoke`, `make demo-model-registry`, and `make demo-release-control`: passed locally. The release demo exercised independent approval denial/grant, shared canary, promotion, and rollback.
- `make demo-local`, `make demo-overload`, `make demo-routing`, `make demo-metering`, `make demo-observability`, `make demo-failure`, `make demo-timeout`, and `make demo-recovery`: passed against the Docker stack.
- PR #4 GitHub checks: `python`, `manifests`, `supply-chain`, and `local-e2e` passed.

## Last Updated

2026-09-21, Week 3 branch.

## Clean-Room Reproducibility

**Status: VALIDATED**

Two clean-room cycles were executed on 2026-09-21. Each began after `make clean-local`, used
`make install`, `make bootstrap-local`, and `make smoke`; the first ran the full demo/validation
suite and the second reran the primary success and bounded-timeout failure demos. The cleanup
asserted project Compose resources and generated artifacts were absent. An unrelated Redis
sentinel container survived project cleanup.
