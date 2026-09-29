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
| MLflow registry + artifact evidence | ✅ EXECUTED LOCALLY | Local MLflow stores stable/candidate ONNX artifacts, SHA-256 digests, CPU fixture metrics, and `champion`/`candidate` aliases. |
| Governed model release control | ✅ EXECUTED LOCALLY | SQLite plan binding, independent approval, Redis-shared canary, MLflow alias promotion and verified rollback run through real gateway traffic. |
| Simulated accelerator capacity policy | ✅ EXECUTED LOCALLY | Redis-backed pool/tenant allocation admits, queues, rejects, and CPU-falls-back through the real gateway path. `simulated-l40s` is quota accounting only. |
| Request-to-release operational evidence | ✅ EXECUTED LOCALLY | A platform-admin analysis retrieves a real Tempo trace ID, canary release plan/phase, route/version, local SLO result, and Decimal fixture cost. A bounded backend timeout is persisted as an SLO violation. |
| Governed canary remediation | ✅ EXECUTED LOCALLY | Separate controller consumes a real failed candidate canary record, persists SQLite incident/plan/audit state, requires independent approval, rejects stale rollout state, applies only stable rollback, verifies real ONNX recovery, exposes Prometheus metrics, and survives restart. |
| Delegated agent-tool governance | ✅ EXECUTED LOCALLY | Separate HTTP facade validates a short-lived delegated agent JWT, filters tool discovery, allows same-tenant metadata evidence and plan-only canary rollback preparation, denies cross-tenant reads and approval/execution, persists hashed audit metadata, and survives restart. It does not claim MCP protocol execution. |
| Developer self-service golden path | ✅ EXECUTED LOCALLY | Signed developers create durable, idempotent tenant/model-bound integration profiles and token-free starter artifacts; generated client executes real ONNX inference. Cross-tenant, unassigned-model, and agent attempts are denied; profile survives service restart. |
| Edge adapters | 📋 ROADMAP | Edge operations remain a separately validated future slice. |
| CPU model quality, cost, and performance | 🔵 SIMULATED / OUT OF SCOPE | The deterministic fixture validates platform flow, not quality or production economics. |
| vLLM, physical GPU, DCGM, KV cache | 📐 ARCHITECTURE / CONTRACT ONLY | No accelerator runtime or GPU telemetry was executed; simulated capacity must not be interpreted as hardware scheduling. |
| Kubernetes/EKS autoscaling | 📋 ROADMAP | Static manifests/Terraform only; not locally deployed. |

## Clean-room evidence boundary

Clean-room reproducibility is ✅ EXECUTED LOCALLY. Two bootstrap → smoke → demo/failure → validation → project-scoped cleanup cycles were run on 2026-09-21; the second started after cleanup, and an unrelated Docker sentinel survived the cleanup test. See `docs/VALIDATION.md`.
