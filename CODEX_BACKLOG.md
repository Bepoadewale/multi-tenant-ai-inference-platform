# Completion Target

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE

# Current Completion Blockers

None for the local-first flagship gate. Preserve the executed core and clean-room
workflow while pursuing production hardening only as P1/P3 work.

# Cloud-Pilot Readiness Program

Cloud work is separate from the completed local-first gate. Do not select an AWS
apply until the relevant design, Terraform, security, delivery, observability, and
operator safeguards have been reviewed and statically validated.

- [x] CP0: establish the cloud architecture, plain-language boundary, and repository-specific acceptance gate.
- [x] CP1: add the intended icon-based topology, cloud operations contract, trust-boundary documentation, and production-evolution boundary. This is documentation/static evidence only.
- [x] CP2: add a dedicated encrypted/versioned S3 state backend, DynamoDB lock design, account/region/tag/budget guards, and Terraform foundation validation. Static validation only; no AWS apply.
- [ ] CP3: define the private EKS/ECR/RDS/Redis/S3/MLflow security and state boundaries using least-privilege IAM/IRSA and Secrets Manager.
- [ ] CP4: define GitOps delivery, a narrow ALB Console/API/identity entry point, and project-scoped bootstrap/smoke/destroy automation.
- [ ] CP5: define cloud observability, rollback, HA, bounded-load, cost-evidence, post-destroy verification drills, and confirmation-gated GitHub Actions OIDC plan/apply/destroy workflows without stored AWS keys.
- [ ] CP6: execute a separately authorized, time-boxed AWS create → validate → destroy pilot and record only measured evidence.

# Flagship P0 — Integrated Platform Story

- [x] Model release control: MLflow registry, artifact integrity, fixture evaluation,
  durable plan, independent approval, shared canary, promotion and rollback.
- [x] Capacity policy: simulated-GPU capacity/admission decision with explicitly
  simulated hardware labels, Redis-shared allocation, bounded queueing, rejection, and CPU fallback.
- [x] Operational evidence: correlate request, release, latency/SLO and estimated cost.
- [x] Governed remediation: incident evidence, bounded approved action and verification.
- [x] Secure agent governance: delegated platform-tool access without privilege amplification.
- [x] Developer self-service: durable tenant/model-bound integration profiles,
  token-free starter artifacts, generated-client inference, idempotency, isolation,
  agent denial, restart recovery, and metrics.
- [x] Narrow edge adapter: signed device registration, durable inventory, independent
  local ONNX, public-only central fallback, privacy/LOCAL_ONLY denial, and restart recovery.
- [x] Bounded sandboxed agent execution: short-lived delegated identity, fixed task
  contract, real hardened disposable Docker child, patch/containment proof, durable
  audit, cleanup, and restart recovery.
- [x] Operator console foundation: local BFF, packaged browser assets, scoped release/
  sandbox actions, cross-slice evidence view, Docker UI smoke check, and two-cycle
  clean-room validation.
- [x] Operator-console drill-downs: two dedicated clean-room cycles validated linked
  tenant, model/release, incident, agent/sandbox, developer, and edge routes backed by
  scoped local BFF detail APIs, including fixed Prometheus-backed model evidence and
  Grafana deep links. Both cycles passed on 2026-09-29.
- [x] Integrated clean-room success and failure demonstration with safe teardown.

# P0 — Required for Portfolio Claim

P0 items block PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE; do not select P1/P2 work first.

- [x] Run CPU-safe real local inference through authenticated tenant admission.
- [x] Prove Redis quota/rate-limit enforcement across two gateway instances.
- [x] Add bounded queue/backpressure and exhaustion tests.
- [x] Emit end-to-end traces and Prometheus metrics with generated traffic.
- [x] Exercise tenant isolation, canary routing, and backend failure.

# P1 — Production Hardening

- Circuit persistence, request cancellation, durable PostgreSQL/outbox metering, load-test reporting, and richer dashboard provisioning.
- [x] Add an evidence-first flagship reference: system/API maps, model-release
  contract, real local console screenshots, safe client examples, threat model,
  troubleshooting, issue templates, release-note policy, and explicitly deferred
  pilot/production work.
- [x] Complete the operator-console workflow UI: two clean-room cycles proved
  scoped release, remediation, developer-profile, sandbox, and simulated edge-network
  actions through the browser BFF; retain the existing service state machines as the
  authority.

# P2 — Enhancements

- Model catalog administration and richer cost attribution.

# P3 — Future / Cloud / Hardware

- vLLM on GPUs, DCGM, EKS and production autoscaling.
- [ ] Execute the staged [real-workload pilot](docs/delivery/real-workload-pilot.md):
  first add encrypted, locked Terraform state and reviewed provision/destroy plans;
  then run one time-boxed GPU runtime and a cost-controlled Kubernetes pilot. Record
  measured evidence and Terraform-verified teardown; do not promote this documentation
  to execution.
# Clean-Room Completion Evidence

- [x] Pass the full clean-room reproducibility gate: deterministic bootstrap, smoke, inference and overload/failure demos, safe cleanup, a second clean bootstrap, and recorded evidence.
