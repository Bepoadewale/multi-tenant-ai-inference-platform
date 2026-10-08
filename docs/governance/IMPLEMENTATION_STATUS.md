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
| Narrow edge routing adapter | ✅ EXECUTED LOCALLY | Two independent edge-agent containers use distinct signed device identities to register/heartbeat into SQLite control state. A compatible agent executes local CPU ONNX; a constrained agent gets central fallback only for public traffic. Restricted/`LOCAL_ONLY` traffic is denied and inventory survives control restart. Hardware profiles are simulated. |
| Bounded sandboxed agent execution | ✅ EXECUTED LOCALLY | A five-minute signed delegated agent invokes only named fixture tasks. The trusted controller creates hardened disposable Docker children; a real repository test/patch and blocked outbound-network probe execute, arbitrary command input is rejected, child resources are removed, and SQLite metadata-only audit survives restart. |
| Unified operator console foundation | ✅ EXECUTED LOCALLY | Local BFF at port 8091 serves packaged browser assets, retrieves cross-slice evidence, and forwards only fixed scoped release/sandbox actions. Browser-held platform credentials are not used. |
| Operator-console drill-down views | ✅ EXECUTED LOCALLY | Linked tenant, model/release, incident, agent/sandbox, developer, and edge detail routes are served through the packaged local BFF. Model details use fixed server-side Prometheus queries for request/outcome, p95 latency/TTFT, token, SLO, release-phase, and estimated fixture-cost evidence, with a model-filtered Grafana deep link. Two dedicated clean-room cycles are recorded in validation evidence. |
| Operator-console workflow UI | ✅ EXECUTED LOCALLY | Guided release, bounded remediation, developer-profile, named sandbox-task, and explicit simulated edge-network controls call only fixed BFF endpoints that forward to existing service state machines. Two clean-room cycles exercised the packaged UI/BFF alongside the cumulative flagship demo. |
| Flagship scenario orchestration | ✅ EXECUTED LOCALLY | A read-only, linked nine-stage narrative composes evidence from tenant admission, CPU inference, releases, observability, remediation, agents, developer profiles, edge routing, and sandbox execution. Two clean-room cumulative demos generated and asserted the evidence. |
| Temporary public walkthrough | ✅ EXECUTED LOCALLY | `make public-demo` cleanly bootstraps the local platform, runs the flagship scenario, creates a temporary credential-free Cloudflare Quick Tunnel, prints its URL, and stops only the tunnel on exit. It is not hosted deployment. |
| Intended AWS cloud-pilot topology and operations contract | 📐 ARCHITECTURE / CONTRACT ONLY | Checked-in icon-based topology, cloud operations guide, trust boundary, and staged acceptance criteria are reviewed documentation; no AWS resources have been created or validated. |
| Terraform state/bootstrap guardrails | 🟡 IMPLEMENTED / NOT FULLY EXECUTED | Separate S3/DynamoDB/budget/tag Terraform root passes backend-free initialization and validation. No plan or apply has created a bucket, lock table, or budget. |
| Private AWS runtime contracts | 🟡 IMPLEMENTED / NOT FULLY EXECUTED | Terraform contract covers VPC/EKS CPU nodes, ECR, encrypted RDS/Redis/S3, secret containers, and a gateway-only IRSA role. Backend-free validation passes; no cloud plan/apply has run. |
| Cloud GitOps and ingress contracts | 🟡 IMPLEMENTED / NOT FULLY EXECUTED | Helm renders a PDB, IRSA hook, digest field, and opt-in ALB ingress; an Argo Application defines protected desired-state delivery. No cluster, Argo sync, image push, ALB, or browser route has executed. |
| Cloud operations and GitHub OIDC automation | 🟡 IMPLEMENTED / NOT FULLY EXECUTED | Account-guarded plan/apply/destroy scripts and a manual confirmation-gated GitHub OIDC workflow are present. No OIDC role assumption, workflow run, cloud metric, alert, rollback, cost query, or teardown has executed. |
| gVisor/Firecracker/Kubernetes sandboxing | 📋 ROADMAP | Local Docker child hardening is executed. Stronger runtime isolation and Kubernetes execution are separate adapters and are not claimed. |
| Edge OTA/fleet rollout/mobile hardware | 📋 ROADMAP | Signed packages, staged OTA, offline buffering, mobile/NPU execution, thermal/battery measurement, and managed fleet control remain in the standalone edge project or production adapters. |
| CPU model quality, cost, and performance | 🔵 SIMULATED / OUT OF SCOPE | The deterministic fixture validates platform flow, not quality or production economics. |
| vLLM, physical GPU, DCGM, KV cache | 📐 ARCHITECTURE / CONTRACT ONLY | No accelerator runtime or GPU telemetry was executed; simulated capacity must not be interpreted as hardware scheduling. |
| Kubernetes/EKS autoscaling | 📋 ROADMAP | Static manifests/Terraform only; not locally deployed or cloud-executed. |

## Clean-room evidence boundary

Clean-room reproducibility is ✅ EXECUTED LOCALLY. The historical inference-core
cycles remain recorded in `VALIDATION.md`; on 2026-09-29 two complete cumulative
flagship cycles ran `make install`, `make bootstrap-local`, `make smoke`,
`make demo-flagship`, `make verify`, and project-scoped `make clean-local`. On
2026-09-30 the equivalent `make public-demo` path, including its temporary Quick
Tunnel URL, passed two clean-room cycles. The second started after the first cleanup
and both left no project Compose resources, project-labelled sandbox children, `.local`,
`.venv`, or generated models. See
`VALIDATION.md`.
