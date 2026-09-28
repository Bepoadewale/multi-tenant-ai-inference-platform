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
- Clean-room workflow passed twice: bootstrap, smoke, successful inference, bounded timeout failure, validation, project-scoped cleanup, then a second bootstrap/demo.

## Implemented but Not End-to-End Validated

- CPU-safe local stack and its failure/recovery paths are validated. Production vLLM, GPU, and Kubernetes adapters remain static contracts.

## Simulated

- No CPU backend generation is simulated: the local classifier is a real ONNX model. The `simulated-l40s` pool is Redis quota accounting only. GPU/DCGM/KV-cache behavior and production cost allocation remain unexecuted.

## Architecture / Contracts Only

- GPU serving, Kubernetes/EKS deployment/autoscaling, real cloud model hosting, and production durable metering/outbox.

## Known Failures

- None known. Required PR checks were green at the latest validated revision; future commits still require green CI.

## Current P0 Objective

Add the next flagship vertical slice: correlate request, model release, latency/SLO evidence, and an explicitly estimated cost without weakening the existing serving path.

## Completion Blockers

- None for the existing inference-core completion gate.
- SLO/FinOps, remediation, secure-agent,
  developer-self-service and optional edge slices are not yet executed here.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.

## Last Validation

- `make lint`, `make test`, `make smoke`, `make demo-model-registry`, `make demo-release-control`, and `make demo-capacity`: passed locally. The capacity demo exercised shared simulated-pool admission, bounded capacity queueing, tenant rejection, and real CPU fallback inference.
- `make demo-local`, `make demo-overload`, `make demo-routing`, `make demo-metering`, `make demo-observability`, `make demo-failure`, `make demo-timeout`, and `make demo-recovery`: passed against the Docker stack.
- PR #4 GitHub checks: `python`, `manifests`, `supply-chain`, and `local-e2e` passed.

## Last Updated

2026-09-28, `37c0da0` capacity-policy implementation; `974397a` recorded local evidence; `86f945e` hardened dependency-audit service selection. See PR #7 for current CI evidence.

## Clean-Room Reproducibility

**Status: VALIDATED**

Two clean-room cycles were executed on 2026-09-21. Each began after `make clean-local`, used
`make install`, `make bootstrap-local`, and `make smoke`; the first ran the full demo/validation
suite and the second reran the primary success and bounded-timeout failure demos. The cleanup
asserted project Compose resources and generated artifacts were absent. An unrelated Redis
sentinel container survived project cleanup.
