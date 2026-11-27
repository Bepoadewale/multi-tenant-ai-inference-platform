# GPU Lab Implementation Status

**Overall:** ACTIVE — Phase 2, isolated EC2 Terraform preparation. This is static-only work; no GPU cloud execution has occurred in this goal.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only | Separate root, account/quota/AZ preflight, checksum-gated plan/apply/destroy scripts, guest plus AWS expiry, and read-only cleanup verifier are drafted. Ten fake-CLI regression cases cover profile propagation, absent Scheduler group, wrong account/quota, missing apply confirmation, changed create/destroy plan checksums, destroy account guard, and destroy-only plan generation. `make verify` passes locally (60 tests). PR #32 head `da2567e` passed all four required CI jobs in run `45933749318`. Backend-free validation passed; latest AWS-backed local-state preview proposed 14 creates for one `g6.xlarge` in `us-east-1c`, not an apply plan. Applied quota remains zero; the increase request is `CASE_OPENED`. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Not started | Manual host and container GPU computation, followed by repeat Ansible run. |
| 4. CUDA performance lab | Not started | Synchronized real-GPU experiments and profiler evidence. |
| 5. vLLM and Qwen serving | Not started | Pinned artifacts and actual L4 inference/streaming. |
| 6. Multi-tenant GPU gateway | Local correctness work in progress; no GPU integration | PR #33 checks passed. PR #34 head `b51aedd` passed all four checks in run `45936485832`; both review threads are resolved. PR #35 head `5cd8dfb` passed all four checks in run `45937540562`; both review threads are resolved. PR #36 head `438e470` is pushed on the updated stack; fresh CI is running. Latest `make verify`: 90 passed, 2 optional Redis skips; PR #35 Redis 7.4 integration: 2 passed. No live vLLM, separate gateway-process failure, or GPU routing evidence exists. |
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
- The prior CPU baseline has two recorded clean-room cycles. This GPU goal requires one successful end-to-end clean-room reproduction; rerun only to recover from a failure or verify a material fix.

## Authorization and resource tracking

- Initial project ceiling: **USD $25 maximum**. No billable apply is authorized until the full bounded execution estimate and exact resource plan fit under that ceiling and the expiry/teardown controls are ready.
- GPU instance-hours used: **0 verified in this goal**.
- AWS resources created by this goal: **none**.
- Exact-name read-only checks on 2026-11-26 found the planned repository state bucket,
  DynamoDB lock table, and `$10` budget were all absent. They appear as creates in the
  7-resource bootstrap preview; no bootstrap apply has occurred.
- Read-only `us-east-1` resource-group tag and EC2 instance lookups for the exact project tag: **no matches**. Untagged or differently tagged leftovers are not excluded.
- EC2 instance type offerings list G6 in multiple `us-east-1` AZs; this is not a capacity reservation.
- On-Demand G and VT applied quota: **0 vCPUs** (`L-DB2E81BA`). A request for **4 vCPUs** for one `g6.xlarge` was submitted after the user's direct instruction; its AWS status is **PENDING**. The request does not allow launch until AWS approves it and the separate cost/apply gates pass.
- Price List API on 2026-11-26: Linux shared On-Demand `g6.xlarge` **$0.8048/hour**. An 8–12 hour instance window costs **$6.44–$9.66** before all other charges. A provisional 12-hour envelope including IPv4, gp3, repository S3/DynamoDB state requests, expiry, egress, tax contingency, and reserve is about **$18.35**; see `COST_REPORT.md` for assumptions and exclusions. This is not a final quote or authorization.
- Credentials are never recorded here.

## Current Next Actions

1. Resolve PR #33 CI results and remaining review feedback; keep it stacked on #32.
2. Resolve human review for PR #32; keep it stacked on #30 until the goal
   registration base is merged.
3. Track the pending four-vCPU G/VT quota request while preparing the exact
   remote-state plan and full resource/cost summary. Do not apply.
4. Keep PRs #30–#36 on their current review branches; none is merged or has been pushed
   directly to `main`.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
