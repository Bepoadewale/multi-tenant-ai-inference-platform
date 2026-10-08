# Definition of Done

## Cloud-Pilot Readiness Gate

This is deliberately separate from the completed local-first gate. Check an item only
after its stated evidence exists; Terraform code, manifests, diagrams, and static
validation alone are not cloud execution evidence.

- [x] Plain-language AWS architecture and trust-boundary documentation identify what
  is planned, private, public, simulated, and intentionally unexecuted.
- [x] An icon-based, checked-in cloud topology and source/generator describe the
  repository-specific runtime rather than generic platform boxes.
- [x] A dedicated Terraform bootstrap root defines an encrypted/versioned S3 state
  bucket, DynamoDB lock table, project tags, and budget guardrail.
- [x] Pilot Terraform defines only resources needed for this repository: private VPC,
  EKS, ECR, required durable stores, IAM/IRSA, secrets boundary, and outputs.
- [x] Terraform formatting, backend-free initialization, and validation pass without
  creating AWS resources. A reviewed non-applying plan remains part of the future
  owner-authorized pilot gate.
- [ ] Cloud workloads have non-root/least-privilege settings, probes, resource bounds,
  NetworkPolicies, PDBs where relevant, and no public data-plane/observability paths.
- [ ] GitOps/image-delivery/bootstrap/smoke/validate/destroy commands are documented,
  bounded, and project-scoped. Static Helm/Argo delivery validation exists; no cloud
  bootstrap, smoke, or destroy execution is claimed.
- [ ] GitHub Actions has a future confirmation-gated OIDC plan/apply/destroy workflow
  with no stored AWS access key.
- [ ] Metrics, traces, dashboards, audit, failure/recovery, bounded-load, cost-query,
  and provider-side destroy evidence are specified for the future pilot.
- [ ] Applied cloud resources, if later authorized, are Terraform-destroyed and
  provider-side absence is recorded before any cloud-complete claim.

# Portfolio Complete — Local-First Scope Gate

## Flagship evolution gate

The existing checked items prove the inference core. Before describing the repository
as a complete *integrated flagship*, each planned vertical slice must have real local
evidence and the cross-slice demonstration must pass clean-room validation.

- [x] Verified model registry/evaluation/canary/approval/promotion-or-rollback path.
- [x] Explicit simulated-GPU capacity policy with real local admission evidence: Redis-shared allocation, bounded queueing, tenant rejection, and CPU fallback while inference remains real CPU ONNX.
- [x] Request-to-release trace/SLO/estimated-cost correlation with a real Tempo trace,
  active release-plan context, metadata-only Redis record, explicit Decimal fixture
  estimate, and a persisted timeout SLO violation.
- [x] Governed remediation consumes a real failed canary metadata record, persists a
  durable incident/plan/audit timeline, requires independent approval, rejects stale
  rollout state, applies only bounded stable rollback, prevents repeated action with a
  cooldown/action budget, verifies recovery through real ONNX inference, and survives
  controller restart.
- [x] Secure delegated agent tool path: short-lived delegated identity, filtered
  discovery, same-tenant metadata evidence, plan-only canary rollback preparation,
  independent approval/execution, durable hashed audit, cross-tenant denial, and
  restart recovery are executed locally. This facade does not claim MCP protocol execution.
- [x] Developer self-service is a narrow, independently executed contract: signed
  human developer identity, tenant/model authorization, durable idempotent profile,
  token-free starter artifacts, real generated-client ONNX request, cross-tenant/model/
  agent denials, restart recovery, and Prometheus evidence.
- [x] Narrow edge interface is independently executed: distinct signed device identities,
  durable inventory, local ONNX on a compatible agent, public-only central fallback on a
  constrained agent, restricted/LOCAL_ONLY denial, Prometheus evidence, and restart recovery.
- [x] Bounded sandboxed agent execution: a five-minute signed delegated agent can request
  only named fixture tasks; a trusted controller creates a real non-root, read-only,
  capability-dropped, socketless, host-bind-free, `network=none`, CPU/memory/PID-bounded
  Docker child; patch and containment probes execute, arbitrary command input is denied,
  child resources are removed, audit is durable, and control restart recovery is proven.
- [x] Unified operator console: a local-only browser-to-backend-for-frontend surface
  reads real cross-slice evidence, exposes only fixed scoped release/sandbox actions,
  serves packaged HTML/CSS/JS from the Docker image, and is exercised by the cumulative
  demo in two clean-room cycles. It does not expose platform tokens to the browser.
- [x] Operator-console drill-downs have passed their dedicated two-cycle clean-room
  validation: linked tenant, model/release, incident, agent/sandbox, developer, and
  edge detail views must all be served from the packaged image and exercised by the
  local BFF demo before this implementation PR is review-ready.
- [x] Operator-console workflow UI is clean-room validated: the packaged browser
  surface must create a governed release plan, expose approval/canary/rollback state,
  drive only the bounded remediation workflow, create a tenant-bound developer profile,
  run named sandbox tasks, and toggle only explicitly simulated known edge devices.
  It must never expose platform tokens, arbitrary commands, arbitrary URLs, or a
  browser-controlled policy/query proxy.
- [x] Integrated clean-room success and rollback demonstration: two full clean-room
  cycles ran `make demo-flagship`, including success, policy/failure, recovery,
  rollback and teardown evidence.

- [x] CPU-capable real model runtime returns output through the OpenAI-compatible API; streaming is exercised if claimed.
- [x] Signed/authenticated tenant identity, isolation, and no cross-tenant leakage are tested.
- [x] Redis-backed distributed quota/rate/concurrency enforcement is exercised across multiple gateway instances where practical.
- [x] Queue/backpressure is bounded and produces an explicit policy reject or queue result under overload.
- [x] Alias and claimed weighted/canary routing reach the intended real backend deterministically.
- [x] Quota exhaustion, backend unavailable, timeout, invalid model, and overload failure paths are executed.
- [x] Metering records request/usage without raw prompt leakage where policy forbids it.
- [x] OTel, Prometheus, and Grafana expose tenant/model/request signals; latency, errors, queue time, and TTFT where available are evidenced.
- [x] `make demo`/equivalent reproduces tenant → auth → quota → queue → runtime → response → usage → telemetry.
- [x] Unit, integration, local-E2E, and security/failure tests pass; required CI is green.
- [x] GPU/DCGM/KV-cache behavior remains simulated or unexecuted unless real hardware runs; README/status state the boundary.

## Maturity Levels

- **FOUNDATION:** architecture and core logic exist.
- **PARTIALLY VALIDATED:** important integrations run but the central story is incomplete.
- **LOCAL END-TO-END VALIDATED:** primary success runs locally with material evidence gaps remaining.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** every checked gate has executed evidence; do not omit the suffix without production validation.

# Clean-Room Reproducibility Gate

`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` requires two executed clean-room cycles: clone → install → bootstrap gateway, Redis, CPU runtime, telemetry → smoke → authenticated inference/quota/queue/routing demo → overload or backend-failure demo → validation → project-scoped cleanup → second clean bootstrap/demo. Executed commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-flagship`, `make verify`, `make clean-local`.

`make public-demo` is an additional executed walkthrough path: it repeats the local
bootstrap/demo and prints a temporary public Quick Tunnel URL. It is not persistent
hosting. Future cloud infrastructure is outside this local gate and must use Terraform
for both provisioning and teardown, with separate real-workload evidence.

- [x] Clean clone/bootstrap has no hidden state; primary and failure demos pass.
- [x] Cleanup removes only this project and unrelated resources survive.
- [x] Post-cleanup absence and second bootstrap/demo are recorded in `docs/governance/VALIDATION.md`.
