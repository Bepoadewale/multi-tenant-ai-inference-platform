# Implementation Status

| Capability | Status | Validation |
| --- | --- | --- |
| Gateway + OpenAI-compatible API | ✅ EXECUTED LOCALLY | Two FastAPI gateways in Docker; authenticated chat and SSE demos. |
| CPU ONNX Runtime inference | ✅ EXECUTED LOCALLY | Two runtime containers load the generated ONNX classifier with `CPUExecutionProvider`. |
| Ed25519 JWT tenant/RBAC | ✅ EXECUTED LOCALLY | Issuer, audience, expiry, signature, tenant, and role negatives covered by tests. |
| Redis distributed admission | ✅ EXECUTED LOCALLY | Lua limits proved across two gateway instances; quota and overload demos return 429. |
| Weighted candidate routing | ✅ EXECUTED LOCALLY | Admin weight mutation routes real traffic to the v2 runtime. |
| Privacy-safe usage + restart recovery | ✅ EXECUTED LOCALLY | Redis metadata records persist through a gateway restart; raw prompt/output are excluded. |
| OTel / Prometheus / Tempo / Grafana | ✅ EXECUTED LOCALLY | Generated traffic is queryable in Prometheus and Tempo; Grafana is provisioned locally. |
| CPU model quality, cost, and performance | 🔵 SIMULATED / OUT OF SCOPE | The deterministic fixture validates platform flow, not quality or production economics. |
| vLLM, GPU, DCGM, KV cache | 📐 ARCHITECTURE / CONTRACT ONLY | No accelerator runtime or GPU telemetry was executed. |
| Kubernetes/EKS autoscaling | 📋 ROADMAP | Static manifests/Terraform only; not locally deployed. |

## Clean-room evidence boundary

Clean-room reproducibility is ✅ EXECUTED LOCALLY. Two bootstrap → smoke → demo/failure → validation → project-scoped cleanup cycles were run on 2026-09-21; the second started after cleanup, and an unrelated Docker sentinel survived the cleanup test. See `docs/VALIDATION.md`.
