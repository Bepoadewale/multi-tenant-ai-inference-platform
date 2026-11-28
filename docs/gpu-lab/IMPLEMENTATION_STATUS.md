# GPU Lab Implementation Status

**Updated:** 2026-11-28. The quota is approved at 4.0 On-Demand G/VT vCPUs; project remote state and Budget controls are absent, and no apply is authorized. Refreshed CI passed on #59 `46162611345`, #60 `46162969703`, #61 `46163194154`, #62 `46163327188`, #63 `46163484312`, #64 `46163910205`, #65 `46164362977`, #66 `46164644804`, and #67 `46164896175`. PR #68 head `ff88165` run `46165126075`, #69 head `f5915e8` run `46165420078`, #70 head `1679aa7` run `46165597103`, and #71 head `127d0a8` run `46166173924` are active. PR #72 head `0b1f4df` is rebased locally and needs fresh CI. No AWS resources, GPU execution, or spend.

**Overall:** ACTIVE — Phase 2 infrastructure remains static-only; GPU quota is approved, but budget, remote-state, exact-plan, expiry, and separate apply gates remain open. The deployment stack is statically prepared through PR #53 and includes PRs #33–#36. PR #53's code head `e623b75` passed all five checks in `46023306230`; its documentation follow-up `2153942` passed all five checks in `46025160292`. PR #54 passed all five required jobs in `46028053505`; PR #55 passed all five in `46034523863`; PR #56 updated head passed all five in `46040861818`. PR #57 head `4795f12` passed all six jobs, including one fresh-runner clean-room cycle, in `46045068200`; PR #57 is ready for review and remains open. PR #58 adds the manual reproduction guide and GPU tenant identities; head `fa4d819` passed all six refreshed checks in run `46162221680`. Run `46052092657` passed the checksum-verified Trivy scan but smoke found the edge-device inventory empty because edge agents could not read the owner-only token file. Commit `d759b8e` matches the two local agents to the bootstrap UID/GID; all six jobs, including the fresh-runner clean-room cycle, passed in `46054114999`. Commit `a1616ec` addresses three automated operator-guide findings; all review threads were resolved on those historical heads and CI runs `46055428111`, `46056755505`, `46057657498`, and runbook follow-up `46058891531` each passed all six jobs, including local E2E. The batch and manual vLLM procedures now share the model-cache volume and served alias; a direct non-streaming adapter contract test is added. No GPU cloud execution has occurred in this goal.

**Interview preparation:** PR #61 contains 106 questions across 18 technical areas, follow-up prompts, and evidence-grounded STAR examples. Its rebased Markdown links pass local validation; fresh CI is pending.

**Documentation follow-up:** PR #61 includes 106 questions and answers with evidence-grounded examples. PR #62 adds draft benchmark and incident handbooks; its benchmark table remains explicitly “Not measured” until real L4 evidence exists. Both documentation packages are awaiting refreshed CI.

**Report draft:** PR #63 includes 28 chapters but remains explicitly pre-GPU; the quota status now reflects 4.0 applied vCPUs and the report does not claim L4 execution, measured benchmarks, actual billing, incidents, or teardown.

**Latest Phase 6 evidence:** PR #58 head `56a0493` passed all six checks in run
`46065078837`, including its automatic local E2E job. The signed-tenant API test
denies a customer-support request for engineering-only `embeddings`, even when the
request supplies `X-Tenant: internal-engineering`. Follow-up head `6f73e42` passed
the cancellation drill across both local gateways, but its outage check caught an
HTTP 500 instead of 503; five jobs passed and local E2E failed in run `46066808334`.
The fix maps shared rollout read/write failures to 503 and persists weights before
local mutation. Ten focused API/rollout tests and Ruff pass locally; this fix awaits
the next PR run.

| Phase | Status | Evidence / next gate |
| --- | --- | --- |
| 1. Audit, research, architecture | Complete | Baseline, direct request/admission audit, proposed diagrams, official-source research notes, risk register, cost estimate, backlog, evidence manifest, and passing PR checks are recorded. PR human review/merge remains open; exact package versions and cost inputs are rechecked before implementation/apply. |
| 2. Single-L4 EC2 Terraform | In progress — static only; launch controls pending | Dedicated Terraform root, one-instance/account/region/AMI guards, encrypted gp3, IMDSv2, SSM, one-time expiry, plan digest checks, destroy safeguards, and read-only cleanup verification are prepared. The pinned-AMI local-state preview proposes 14 creates for one `g6.xlarge`; it is not a remote-state or apply-ready plan. Real state locking, SSM registration, expiry, provisioning, and teardown remain untested. On 2026-11-28, read-only AWS CLI checks confirmed `CASE_CLOSED` and 4.0 applied On-Demand G/VT vCPUs; this is enough by quota for one `g6.xlarge`, but does not reserve AZ capacity or authorize an apply. |
| 3. Ubuntu/NVIDIA/CUDA/Ansible | Prepared — static host automation | PR #50 provides an ordered host-install manifest and 29-package hashed PyTorch lock. PR #57 adds the hash-locked Ansible 2.21.6 controller and host role for pinned Ubuntu/NVIDIA/CUDA/Docker packages, signed repositories, runtime configuration, PyTorch, and post-reboot verification. All six refreshed CI jobs passed on head `fcc5651` in run `46161064613`; no package has been installed on an EC2 host. No package has been installed on an EC2 host. The manual learning pass and second-run idempotency check remain open. |
| 4. CUDA performance lab | Prepared — static only; PR #65 requires fresh CI | PR #49 prepares bounded CUDA vector-add, synchronized PyTorch experiments, and no-GPU planning. PR #65 adds a bounded Triton vector-add runner and Nsight Systems/Compute procedures. The prior #65 head passed CI, but current stack is rebased; no kernel has been compiled on L4 and there are no measured profiler results. |
| 5. vLLM and Qwen serving | Prepared — static only | The isolated Compose profile and immutable image/model candidates are prepared. The profile is now stacked after the gateway stream, admission, tokenizer, and cleanup work in PRs #33–#36. No image layer or model weights were downloaded; no L4 load, inference, or streaming result exists. |
| 6. Multi-tenant GPU gateway | Local integration fix verified; fresh stacked CI pending; L4 unverified | PR #58's signed customer-support API denial test passed in run `46065078837`. Run `46066808334` proved ten cancellations release active gauges and shared Redis leases, then found rollout-state lookup returned HTTP 500 during Redis outage. The local fix maps Redis rollout read/write errors to 503 and avoids partial local writes; 10 focused tests pass. The corrected outage/recovery drill has passed on the prior PR #58 head; the current restacked head requires fresh CI. No real GPU request, token reconciliation against vLLM, or live GPU cancellation has been verified. |
| 7. GPU/AI observability | Prepared — static only | PR #46 configures pinned exporters, Prometheus, Grafana, Alertmanager, OpenTelemetry, Tempo, rules, and dashboards. All five required jobs pass on the current restacked head. No live device metrics, alert, dashboard, or trace has been observed. |
| 8. Benchmarks and FinOps | Prepared — static only | PR #47 includes a bounded direct vLLM serving matrix. PR #60 adds authenticated gateway benchmarking across three tenants, comparison with direct vLLM, bounded client waits, failure-safe sample retention, and an L4 guard for live runs. Eight focused tests, Ruff, and a no-network dry run pass after rebasing on PR #58 head `fa4d819`; fresh CI is pending. No L4 benchmark or measured inference cost exists. |
| 9. Evaluation and releases | In progress — static implementation | PR #48 has seven synthetic evaluation cases and a privacy-safe dry-run. PR #51 designs sequential LLM release. PR #52 adds private MLflow tracking and report publication. PR #54 adds local manifest/plan controls. PR #55 adds authenticated plan/read/approval routes, checks candidate metadata against a finished MLflow run and sanitized report, and stores manifests in shared single-host SQLite. Latest five-check run `46034523863` passed. PR #56 head `852c873` passed all five checks in `46040861818`, including the required clean-room cycle. Live host/inference/recovery checks remain open. No real LLM evaluation or release has occurred. |
| 10. Incidents and recovery | First local incident recorded; GPU drills pending | `INCIDENT-LOCAL-REDIS-001.md` records the real CI 500, root cause, and incomplete recovery verification. The cancellation drill passed; the outage drill fix awaits CI. No controlled L4 failure/recovery report exists yet. |
| 11. Automation and CI | In progress — host operator statically prepared | PR #64 fixes the first-configuration guard: configuration checks IMDSv2 instance identity before drivers exist; deployment and GPU workload actions still require one visible L4. Twenty focused tests and full local verification passed on its earlier base; refreshed CI is pending. Terraform apply, Ansible host execution, and cloud execution remain unrun. |
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
- On-Demand G and VT applied quota (`L-DB2E81BA`): **4.0 vCPUs** in `us-east-1`; read-only history reports `CASE_CLOSED`. No new request is needed. This quota does not reserve instance capacity or permit an apply.
- Price List API on 2026-11-26: Linux shared On-Demand `g6.xlarge` **$0.8048/hour**. An 8–12 hour instance window costs **$6.44–$9.66** before all other charges. A provisional 12-hour envelope including IPv4, gp3, repository S3/DynamoDB state requests, expiry, egress, tax contingency, and reserve is about **$18.35**; see `COST_REPORT.md` for assumptions and exclusions. This is not a final quote or authorization.
- Credentials are never recorded here.

**GPU preparation:** [GPU batch runbook](GPU_BATCH_RUNBOOK.md) groups preflight,
manual driver/CUDA/container/PyTorch setup, vLLM, tenant validation, telemetry,
benchmark/evaluation, evidence export, and teardown. It is a static procedure only;
all package candidates must be rechecked and no L4 command has run. A fresh
read-only AWS check on 2026-11-28 confirmed the applied G/VT quota is 4.0 vCPUs;
exact-name state bucket, lock table, and project Budget checks returned absent, and
project-tag EC2/resource-group queries returned no resources in `us-east-1`. A separate EC2
Compose profile now statically configures one vLLM GPU service, two loopback-only
gateway replicas, and shared Redis. Catalog routing and health checks are opt-in and
unit-tested; the profile has not run on an L4.

## Current Next Actions

1. Keep PRs #56–#58 open for review, finish their updated CI, and resolve review threads. Do not merge without owner authorization.
2. Keep AWS work read-only until the exact project state/lock and Budget alert recipient are established, the exact saved plan and cost fit under $25, expiry safeguards are checked, and separate apply authorization is recorded.
3. Continue non-billable research and deployment preparation without claiming host execution; the 2026-11-27 CLI check found all currently pinned NVIDIA and Docker package candidates in official vendor package indexes, and the documented signing-key/keyring hashes matched downloaded vendor artifacts. Recheck versions before any paid batch; manual NVIDIA setup still precedes running Ansible.
4. Recheck signed package indexes, image digest, model revision/license/hash, capacity, current prices, and exact bounded plan immediately before any authorized GPU batch.
5. Obtain human review for the open PR chain. Nothing has been merged; no direct changes to `main` were made.

Update this table and the detailed goal after each implementation package. A phase is complete only when its acceptance gate has actual evidence.
