# GPU Lab Implementation Status

**Overall:** ACTIVE — Phase 2 infrastructure is prepared but blocked on quota. The deployment stack is statically prepared through PR #53 and includes PRs #33–#36. PR #53's code head `e623b75` passed all five checks in `46023306230`; its documentation follow-up `2153942` passed all five checks in `46025160292`. PR #54 passed all five required jobs in `46028053505`; PR #55 passed all five in `46034523863`; PR #56 updated head passed all five in `46040861818`. PR #57 head `4795f12` passed all six jobs, including one fresh-runner clean-room cycle, in `46045068200`; PR #57 is ready for review and remains open. PR #58 adds the manual reproduction guide and GPU tenant identities. Run `46052092657` passed the checksum-verified Trivy scan and all checks except local smoke's edge-device inventory. Source review traced this to the mode-`0600` token file not being readable by edge-agent containers running as UID `65532`; the unrun follow-up matches those local containers to the bootstrap UID/GID and waits for device registration. No GPU cloud execution has occurred in this goal.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only; quota blocked | Dedicated Terraform root, one-instance/account/region/AMI guards, encrypted gp3, IMDSv2, SSM, one-time expiry, plan digest checks, destroy safeguards, and read-only cleanup verification are prepared. The pinned-AMI local-state preview proposes 14 creates for one `g6.xlarge`; it is not a remote-state or apply-ready plan. Real state locking, SSM registration, expiry, provisioning, and teardown remain untested. AWS denied the initial quota request by email; the owner reports manually appealing through the existing case. Applied quota remains zero. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Prepared — static host automation | PR #50 provides an ordered host-install manifest and 29-package hashed PyTorch lock. PR #57 adds the hash-locked Ansible 2.21.6 controller and host role for pinned Ubuntu/NVIDIA/CUDA/Docker packages, signed repositories, runtime configuration, PyTorch, and post-reboot verification. All six CI jobs passed on head `4795f12` in `46045068200`. No package has been installed on an EC2 host. The manual learning pass and second-run idempotency check remain open. |
| 4. CUDA performance lab | Prepared — static PR #49 | Bounded CUDA vector-add, synchronized PyTorch experiments, and no-GPU planning are prepared. All five required jobs pass on the current restacked head. The `.cu` source is not compiled and there are no L4 measurements or profiler results. |
| 5. vLLM and Qwen serving | Prepared — static only | The isolated Compose profile and immutable image/model candidates are prepared. The profile is now stacked after the gateway stream, admission, tokenizer, and cleanup work in PRs #33–#36. No image layer or model weights were downloaded; no L4 load, inference, or streaming result exists. |
| 6. Multi-tenant GPU gateway | Prepared — static integration | PRs #33–#36 add stream usage/cancellation handling, request-scoped Redis admission leases, model-aware token reservations, and cleanup tests; PR #45 integrates the GPU profile. This branch adds named customer-support, internal-engineering, and research tenant profiles with different quotas/model permissions and signed identities. No real GPU request, quota reconciliation, cross-replica GPU request, or client cancellation has been verified on vLLM. |
| 7. GPU/AI observability | Prepared — static only | PR #46 configures pinned exporters, Prometheus, Grafana, Alertmanager, OpenTelemetry, Tempo, rules, and dashboards. All five required jobs pass on the current restacked head. No live device metrics, alert, dashboard, or trace has been observed. |
| 8. Benchmarks and FinOps | Prepared — static only | PR #47 includes a bounded direct vLLM serving matrix and metadata collection. All five required jobs pass on the current restacked head. No L4 benchmark or measured inference cost exists. |
| 9. Evaluation and releases | In progress — static implementation | PR #48 has seven synthetic evaluation cases and a privacy-safe dry-run. PR #51 designs sequential LLM release. PR #52 adds private MLflow tracking and report publication. PR #54 adds local manifest/plan controls. PR #55 adds authenticated plan/read/approval routes, checks candidate metadata against a finished MLflow run and sanitized report, and stores manifests in shared single-host SQLite. Latest five-check run `46034523863` passed. PR #56 head `852c873` passed all five checks in `46040861818`, including the required clean-room cycle. Live host/inference/recovery checks remain open. No real LLM evaluation or release has occurred. |
| 10. Incidents and recovery | Not started | Safe real fault injection, diagnosis and verified recovery reports. |
| 11. Automation and CI | In progress — static only | PR #53 adds a hash-locked container build and a lock coverage check; its Linux image build passed. PR #57's Ansible hash-lock and syntax job passed with the other five jobs. Terraform apply, Ansible host execution, and cloud execution remain unrun. |
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
- On-Demand G and VT applied quota: **0 vCPUs** (`L-DB2E81BA`); the latest read-only `us-east-1` check on 2026-11-27 confirmed the expected account, quota `0.0`, and the existing 4-vCPU request still `CASE_OPENED`. AWS email reports denial; the owner reports manually appealing through the existing Support Center case. No API-confirmed appeal result or quota change is available. Do not submit a duplicate request.
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

1. Validate the edge-agent UID fix and run PR #58's next CI cycle; confirm a successful clean-room smoke sequence with the checksum-verified scanner.
2. Keep AWS work read-only until the manually submitted appeal is decided and applied G/VT quota is nonzero; do not send another appeal or request.
3. Continue non-billable research and deployment preparation without claiming host execution; manual NVIDIA setup still precedes running Ansible.
4. Recheck signed package indexes, image digest, model revision/license/hash, capacity, current prices, and exact bounded plan immediately before any authorized GPU batch.
5. Obtain human review for the open PR chain. Nothing has been merged; no direct changes to `main` were made.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
