# Roadmap

## Flagship evolution

The completed milestones below are the preserved inference core. The next milestones
are additive vertical slices, each requiring real local execution and a failure path:

- [x] F1 MLflow-backed registry, evaluation, verified canary, approval and rollback.
- [x] F2 simulated-GPU capacity/admission policy: Redis-shared allocation, bounded queueing, tenant rejection, and CPU fallback; no physical GPU claims.
- [x] F3 request/release/SLO/estimated-cost correlation.
- [x] F4 governed incident/remediation and verification.
- [x] F5 delegated agent tools and developer self-service requests.
- [x] F6 narrow edge adapter: signed device registration, durable local inventory,
  compatible device local ONNX, constrained-device public fallback, and privacy/LOCAL_ONLY denial. Hardware profiles are simulated; OTA/fleet rollout remains separate.
- [x] F7 bounded sandboxed agent execution: short-lived delegated identity, named task
  contract, real hardened disposable Docker child, patch/containment proof, durable
  metadata-only audit, cleanup, and restart recovery.
- [x] F8 integrated clean-room success and rollback demonstration: two full
  bootstrap → smoke → `demo-flagship` → verify → safe-cleanup cycles passed on
  2026-09-29.

- [x] M1 gateway, deterministic mock test backend, real CPU ONNX Runtime local backend, OpenAI-compatible chat/streaming, and tests.
- [x] M2 authenticated fixture identity, tenant authorization, quotas, metering.
- [x] M3 vLLM runtime configuration and Kubernetes/Helm contracts.
- [x] M4 aliases, weighted routing, healthy backend behavior.
- [x] M5 Prometheus metrics, provisioned local dashboard, and OTLP export to Tempo for generated traffic.
- [x] M6 benchmark/load client and report artifacts.
- [x] M7 KEDA inference-demand scaling contract.
- [x] M8 GPU scheduling/DCGM/GPU Operator documentation and manifests.
- [x] M9 canary/rollback design.
- [x] M10 usage/cost/capacity API design.
- [x] M11 opt-in AWS GPU Terraform contract.
- [x] M12 security, failure-mode, interview documentation.
- [x] Production contracts: vLLM adapter, Redis Lua admission contract, strong admin endpoint guard, streaming semantics, and API tests.
- [ ] Environment-dependent hardening: OIDC/JWKS, live Redis/PostgreSQL/outbox, vLLM adapter integration tests, live GPU benchmarks, GitOps controller, Karpenter implementation.
