# Project Status

## Current Maturity

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE

## Maturity Model

`FOUNDATION` → `PARTIALLY VALIDATED` → `LOCAL END-TO-END VALIDATED` → `PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE`.

## Executed and Verified

- Two independent FastAPI gateways authenticate Ed25519 JWTs and derive tenant/role server-side.
- Redis Lua admission enforces shared request, token, concurrency, daily-budget, and bounded queue limits across both gateways.
- Two Dockerized CPU ONNX Runtime targets return real deterministic classifier output through the OpenAI-compatible and SSE paths.
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

Maintain the validated local-first control loop; take the highest-value P1 hardening item only after preserving clean-room reproducibility.

## Completion Blockers

- None for the local-first completion gate. P1/P3 work remains below.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.

## Last Validation

- `make verify`: passed — Ruff, 20 pytest tests, pip-audit, and Compose configuration.
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
