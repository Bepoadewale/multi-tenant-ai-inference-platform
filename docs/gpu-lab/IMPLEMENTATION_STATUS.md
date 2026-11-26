# GPU Lab Implementation Status

**Overall:** ACTIVE — Phase 2, isolated EC2 Terraform preparation. This is static-only work; no GPU cloud execution has occurred in this goal.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only | Prepare separate guarded root, state bootstrap, expiry, and teardown verification. No apply while G/VT quota is zero or until the exact plan and cost gates pass. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Not started | Manual host and container GPU computation, followed by repeat Ansible run. |
| 4. CUDA performance lab | Not started | Synchronized real-GPU experiments and profiler evidence. |
| 5. vLLM and Qwen serving | Not started | Pinned artifacts and actual L4 inference/streaming. |
| 6. Multi-tenant GPU gateway | Not started | Real routed requests, shared limits, failure and cancellation accounting. |
| 7. GPU/AI observability | Not started | Live metrics, dashboards, alert, trace correlation. |
| 8. Benchmarks and FinOps | Not started | Reproducible measured report with raw evidence references and cost method. |
| 9. Evaluation and releases | Not started | Actual evaluation, candidate rejection and rollback. |
| 10. Incidents and recovery | Not started | Safe real fault injection, diagnosis and verified recovery reports. |
| 11. Automation and CI | Not started | Repeatable Terraform/Ansible/Compose and gated non-billable PR CI. |
| 12. Clean-room and teardown | Not started | Independent recreation, export and provider-side absence checks. |

## Baseline verified directly

- FastAPI gateway with Ed25519 signed identities, tenant/model authorization, Redis-backed request/token/concurrency admission and metering, routing, streaming, telemetry, CPU ONNX and vLLM adapter modules.
- Local Compose and historical clean-room evidence use CPU ONNX. The current repository does not demonstrate GPU execution.
- Existing Terraform root is an EKS and managed-services contract; existing Kubernetes vLLM manifests are not the EC2 deployment.
- Gateway vLLM response accounting and token estimation need direct tests and design review before GPU integration.
- Baseline on `main` reported 84 advisory records across seven transitive packages and failed `make verify`. PR #31 adds shared minimum-version constraints; local full verification, image build, clean-room evidence, and all four required GitHub check names across two workflow runs passed. Human review/merge remains outstanding. See ticket #31 and `docs/governance/VALIDATION.md`.
- Historical validation is documented in `docs/governance/VALIDATION.md`; this session's local results are not GPU evidence.

## Authorization and resource tracking

- Initial project ceiling: **USD $25 maximum**. No billable apply is authorized until the full bounded execution estimate and exact resource plan fit under that ceiling and the expiry/teardown controls are ready.
- GPU instance-hours used: **0 verified in this goal**.
- AWS resources created by this goal: **none**.
- Read-only `us-east-1` resource-group tag and EC2 instance lookups for the exact project tag: **no matches**. Untagged or differently tagged leftovers are not excluded.
- EC2 instance type offerings list G6 in multiple `us-east-1` AZs; this is not a capacity reservation.
- On-Demand G and VT quota: **0 vCPUs** (`L-DB2E81BA`); G6 launch cannot proceed until increased.
- Price List API on 2026-11-26: Linux shared On-Demand `g6.xlarge` **$0.8048/hour**. An 8–12 hour instance window costs **$6.44–$9.66** before all other charges. A provisional 12-hour envelope including IPv4, gp3, state, expiry, egress, tax contingency, and reserve is about **$18.34**; see `COST_REPORT.md` for assumptions and exclusions. This is not a final quote or authorization.
- Credentials are never recorded here.

## Current Next Actions

1. Build the independent EC2 root, static guards, state bootstrap, dual expiry, and
   exact destroy/inventory verification; never apply it during this static package.
2. Run Terraform formatting and backend-disabled validation, then review the static
   plan shape without creating resources.
3. Continue local gateway correctness and reproducibility work in a separate focused
   PR before live vLLM tenant integration.
4. Keep PRs #30 and #31 open for human review; their required checks currently pass.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
