# Roadmap

## Flagship evolution

The completed milestones below are the preserved inference core. The next milestones
are additive vertical slices, each requiring real local execution and a failure path:

- [x] F1 MLflow-backed registry, evaluation, verified canary, approval and rollback.
- [ ] F2 simulated-GPU capacity/admission policy; no physical GPU claims.
- [ ] F3 request/release/SLO/estimated-cost correlation.
- [ ] F4 governed incident/remediation and verification.
- [ ] F5 delegated agent tools, self-service requests and optional edge adapter.
- [ ] F6 integrated clean-room success and rollback demonstration.

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
