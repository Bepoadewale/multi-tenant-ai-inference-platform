# GPU Lab Implementation Status

**Overall:** ACTIVE — Phase 2 infrastructure is prepared but blocked on quota; Phase 4 CUDA lab is in static PR review. No GPU cloud execution has occurred in this goal.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only; quota blocked | Separate root, account/quota/AZ/AMI preflight, checksum-gated plan/apply/destroy scripts, guest plus AWS expiry, and read-only cleanup verifier are drafted. PR #40 pins the reviewed Canonical Ubuntu 24.04 AMI; preflight checks owner, image family, x86_64 architecture, and availability. Local validation passed; all four required checks passed in runs `45949421928`, `45950217355`, and `45951027403`. A fresh AWS-backed local-state preview proposes 14 creates for one `g6.xlarge` in `us-east-1c` (plan digest in ticket42); it is not a remote-state or apply-ready plan. Regression tests cover passing both remote-lock settings to Terraform init, but real lock behavior is untested. AWS email says the 4-vCPU request was denied, while quota history still says `CASE_OPENED`. The owner reports manually submitting an appeal through the existing Support Center case; no AWS reply is confirmed. Applied quota remains zero. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Not started | Manual host and container GPU computation, followed by repeat Ansible run. |
| 4. CUDA performance lab | Prepared — static PR #49 open | CUDA vector-add and synchronized PyTorch matrix experiments, bounded sizes, a no-GPU plan, tests, and instructions are prepared on `codex/gpu-cuda-lab-preparation`. All five required CI checks passed in run `45998860857` on code head `ce8bbba`. The `.cu` source is not compiled; L4 measurements and profiler evidence remain outstanding. |
| 5. vLLM and Qwen serving | Prepared — static only | Separate one-GPU Compose profile and pinned image/model candidates exist; no image pull, model download, L4 load, or inference has occurred. |
| 6. Multi-tenant GPU gateway | Prepared — static integration | Opt-in catalog selection routes `chat-default` to one vLLM endpoint; existing ONNX defaults remain. Gateway readiness checks backend and shared capacity state. No real GPU requests, quota accounting, or cancellation behavior has been verified. |
| 7. GPU/AI observability | Prepared — static only | PR #46 passed all five required checks after rebasing, run `45992409372`. It configures digest-pinned exporters, Prometheus, Grafana, Alertmanager, a privacy-filtered OTel Collector, Tempo, rules, and dashboards. It has not started on a GPU; current metric names/units, PromQL, exporter compatibility, host access, alerts, and trace propagation still need runtime validation. |
| 8. Benchmarks and FinOps | In progress — static PR #47 | A direct vLLM matrix and bounded runner are prepared on `codex/gpu-benchmark-preparation`; its cleanup regression test and all five required CI checks passed in run `45994609421` on head `9936e11`. No L4 measurements exist. |
| 9. Evaluation and releases | In progress — static PR #48 | Seven synthetic cases, deterministic checks, a human-review marker, metadata-safe report output, and a no-network dry-run passed all five required checks on head `71637d7` in run `45997259460`. No LLM evaluation, candidate decision, or rollback has run. |
| 10. Incidents and recovery | Not started | Safe real fault injection, diagnosis and verified recovery reports. |
| 11. Automation and CI | In progress — static only | `make verify` validates the dedicated single-GPU Compose file. PR #45's latest full run `45990929878` passed all four required checks, including the capacity demo and queue path. Terraform apply, Ansible roles, and cloud execution remain unrun. |
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
- On-Demand G and VT applied quota: **0 vCPUs** (`L-DB2E81BA`) in `us-east-1`, `us-east-2`, and `us-west-2`. One 4-vCPU request was submitted for a single `g6.xlarge`. AWS email reports denial; read-only quota history still reports `CASE_OPENED`. The owner reports manually submitting an appeal through the existing Support Center case; no AWS reply or quota change is confirmed. Do not submit a duplicate request.
- Price List API on 2026-11-26: Linux shared On-Demand `g6.xlarge` **$0.8048/hour**. An 8–12 hour instance window costs **$6.44–$9.66** before all other charges. A provisional 12-hour envelope including IPv4, gp3, repository S3/DynamoDB state requests, expiry, egress, tax contingency, and reserve is about **$18.35**; see `COST_REPORT.md` for assumptions and exclusions. This is not a final quote or authorization.
- Credentials are never recorded here.

**GPU preparation:** [GPU batch runbook](GPU_BATCH_RUNBOOK.md) groups preflight,
manual driver/CUDA/container/PyTorch setup, vLLM, tenant validation, telemetry,
benchmark/evaluation, evidence export, and teardown. It is a static procedure only;
all package candidates must be rechecked and no L4 command has run. A fresh
read-only AWS check on 2026-11-27 verified the configured key profile is in the
expected project account, applied G/VT quota is still zero, and exact project-tag
EC2/resource-group queries returned no resources in `us-east-1`. A separate EC2
Compose profile now statically configures one vLLM GPU service, two loopback-only
gateway replicas, and shared Redis. Catalog routing and health checks are opt-in and
unit-tested; the profile has not run on an L4.

## Current Next Actions

1. Validate the rebased PR #46 observability branch in CI after the parent PR #45
   capacity demo passed all four required checks in run `45990929878`.
2. Preserve the accurate owner-reported appeal status; quota remains zero and no
   follow-up should duplicate the submitted appeal.
3. Continue remote-state, expiry, cost, and local gateway correctness work without
   applying infrastructure or duplicating the submitted appeal.
4. Keep work in the PR-only workflow. All current project PRs remain unmerged; human
   review is outstanding. PR #46 contains the rebased, static GPU observability
   preparation; live GPU validation remains outstanding.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
