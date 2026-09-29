# Project Status

## Current Maturity

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE.

The public flagship's preserved inference core and every currently scoped vertical
slice have executed together in two clean-room local cycles. Production/cloud/hardware
adapters remain explicitly outside this status.

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
- A separate developer-self-service service validates a signed human developer identity,
  persists a tenant/model-bound integration profile in SQLite, returns token-free
  starter artifacts, and proves the generated client executes real ONNX inference.
  Unassigned models, cross-tenant profile reads, and delegated-agent creation attempts
  are denied; the profile survives a service restart.
- Two independent edge-agent containers authenticate with distinct signed device
  identities, register and heartbeat into durable SQLite inventory, and expose
  policy-aware local-versus-central inference. The compatible agent executes its own
  CPU ONNX session; the constrained agent falls back only for public data. Restricted
  and `LOCAL_ONLY` requests without a local model are denied, and inventory survives
  edge-control restart. Device hardware labels are simulated.
- A separate sandbox-control service validates a five-minute signed delegated agent,
  accepts only named fixture tasks, and durably records metadata-only task evidence.
  Its trusted controller creates real disposable hardened Docker children: the patch
  task and blocked outbound-network probe executed; arbitrary task input is rejected;
  child container/workspace cleanup and control restart recovery were verified.
- A local Operator Console at port 8091 is served by a scoped backend-for-frontend.
  It provides linked tenant, model/release, incident, agent/sandbox, developer, and
  edge detail views over real cross-slice local evidence, and forwards only fixed
  release/sandbox actions. Browser-held platform credentials are not used.
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

Complete the two-cycle clean-room validation for the new Operator Console drill-down
routes; do not regress tenant isolation, bounded authority, or truthful evidence labels.

## Completion Blockers

- The newly implemented Operator Console drill-down views require dedicated two-cycle
  clean-room evidence before their implementation PR is review-ready. The prior
  console-foundation completion evidence remains valid only for that earlier scope.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM execution, DCGM/KV-cache signals, Kubernetes/EKS autoscaling, and production model hosting.
- gVisor/Firecracker/Kubernetes sandbox runtime execution.

## Last Validation

- **Cumulative flagship clean-room validation:** two complete clean-room cycles passed
  on 2026-09-29. Each ran `make clean-local`, `make install`,
  `make bootstrap-local`, `make smoke`, `make demo-flagship`, `make verify`, and
  `make clean-local`. The cumulative demo exercised authenticated inference, shared
  admission/overload, routing, metering, observability, backend failure/timeout,
  recovery, MLflow registry/release, simulated capacity, request evidence,
  self-service, delegated tools, remediation, edge policy, and hardened sandbox
  tasks. `make verify` passed Ruff, `44 passed` pytest tests, dependency audit, and
  Compose configuration. After each cleanup there were no project Compose resources,
  project-labelled sandbox children, `.local`, `.venv`, or generated models; cycle 2
  began only after cycle 1 cleanup.

- Sandboxed-agent slice: clean local bootstrap → smoke → `make demo-sandboxed-agent`
  passed on 2026-09-29. A five-minute signed delegated agent ran a real non-root
  fixture patch task in a disposable Docker child, an outbound network probe was
  blocked by `network=none`, arbitrary command input returned 422, child containers
  and volumes were absent after each task, Prometheus recorded both outcomes, and the
  SQLite task audit survived sandbox-control restart. Two clean container cycles
  passed; each included Ruff, `42 passed` pytest tests, Compose config validation, and
  project-scoped cleanup.
- Edge-adapter slice: two local container recreations passed on 2026-09-29. Each
  proved two independent signed device agents, SQLite inventory, real compatible-device
  local ONNX, constrained-device public gateway fallback, restricted/LOCAL_ONLY denial,
  Prometheus registration evidence, and edge-control restart recovery. Final static
  validation passed Ruff, `41 passed` pytest tests, and Compose config.
- Developer self-service slice: local Compose bootstrap → smoke →
  `make demo-self-service` passed on 2026-09-29. The live demo created a durable,
  idempotent `team-search` profile, executed its generated token-free client against
  real ONNX inference, denied an unassigned model, cross-tenant read, and delegated
  agent creation, exposed a Prometheus profile metric, and recovered the profile after
  a service restart. Two clean cycles passed: each began with `make clean-local`, then
  `make install`, bootstrap, smoke, demo, Ruff, 40 pytest tests, Compose config, and
  safe cleanup; the second started only after the first cleanup.
- Delegated-agent slice: two clean bootstrap → smoke → `make demo-agent-tools` →
  teardown cycles passed on 2026-09-28. The live demo exercised filtered discovery,
  same-tenant evidence, cross-tenant denial, plan-only authority, independent
  approval/execution, Prometheus tool metrics, durable hashed audit, service restart,
  and real stable-ONNX recovery. Static validation after the second run passed Ruff,
  37 pytest tests, and Compose configuration. The later cumulative flagship
  clean-room evidence above fulfilled the all-slice completion item.
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

2026-09-29, cumulative flagship clean-room evidence recorded on
`codex/flagship-final-cleanroom`; GitHub CI is required before review.

## Clean-Room Reproducibility

**Status: VALIDATED**

Two full cumulative cycles passed on 2026-09-29. Both ended with no project Compose
resources, project-labelled sandbox children, `.local`, `.venv`, or generated models;
the second bootstrap ran after the first cleanup. Detailed commands and evidence are in
`docs/VALIDATION.md`.
