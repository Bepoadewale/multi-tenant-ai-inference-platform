# GPU Lab Execution Journal

## 2026-11-28 — Remove private quota request references from public records

- **Phase:** Phase 2 evidence hygiene; no AWS or GPU operation.
- **Branch/PR:** `codex/gpu-network-plan-review`, PR #84, starting at clean head
  `b27423f`.
- **Finding:** an inherited historical evidence row and journal entries included a
  private AWS quota-request reference. The identifier was not required to explain the
  decision or validate the current applied quota.
- **Change:** replaced the identifier in six documentation locations with a clear
  redaction marker; preserved the historical request status and evidence claims.
- **Validation:** `git diff --check` passed before adding this entry; documentation
  link validation and PR CI remain to run on the resulting commit.
- **Cost/resources:** no AWS query or mutation, plan/apply, GPU operation, model
  download, package installation, or spend.
- **Next:** validate and publish this sanitization on PR #84; then continue with
  independent PR conflict repair. Do not merge without owner review.

## 2026-11-28 — Refresh static package candidates and quota/backend status

- **Phase:** Phase 2 static infrastructure readiness; no AWS or GPU mutation.
- **Branch/PR:** `codex/gpu-network-plan-review`, PR #84, starting head
  `3aeef0278f67d525f16a700c3c20275e0677c8c5`; GitHub reports OPEN/CLEAN with no
  review decision.
- **Objective:** reconcile current quota approval reporting, avoid implying the
  remote backend or Budget exists, and refresh pinned software package metadata
  before any eventual GPU batch.
- **Research:** checked NVIDIA Ubuntu 24.04, NVIDIA Container Toolkit, and Docker
  Ubuntu Noble package indexes through Python's standard HTTP client; inspected the
  vLLM latest-release metadata through `gh`. Selected package versions and Compose
  checksum are recorded in `RESEARCH_NOTES.md`.
- **Changes:** corrected docs to say the owner reports quota approval and the CLI
  confirms a 4.0-vCPU applied quota while request history remains `CASE_OPENED`;
  clarified that the S3/DynamoDB backend and Budget are planned, not deployed; pinned
  the current Compose candidate to 5.8.1; and corrected a claim that metadata checks
  proved a tested vLLM stack.
- **Failed approaches:** the first broad documentation patch did not apply because
  the implementation-status paragraph did not match the expected text; no partial
  edit occurred. The edits were split into smaller patches.
- **Validation:** `make gpu-docs-validate` validated local links/headings in 35
  files; `make gpu-compose-config` passed; `make gpu-ec2-validate` passed Terraform
  formatting, validation, and all 12 mocked cases. `make gpu-ansible-validate`
  initially failed because Ansible was not on the default `PATH`; rerunning with
  `PATH=/tmp/gpu-ansible-venv/bin:$PATH` passed playbook syntax validation.
  `git diff --check` passed before these journal updates.
- **Previous-head CI:** while reviewing the diff, `gh pr checks 84` showed all six
  required jobs passing on the already-published head `3aeef02` in run
  `46151077506`. This does not validate the uncommitted edits recorded here.
- **Published follow-up CI:** commit `9520b6e` was pushed to PR #84. Its six required
  jobs passed in run `46152355082`; local end-to-end completed in 5m29s. Owner review
  is still pending.
- **Evidence closeout CI:** commit `e8675be` records the package/status work and prior
  CI result. Its six required jobs passed in run `46152999772`; local end-to-end
  completed in 6m00s. A separate AWS OIDC-labelled run had no jobs and no logs; the
  checked workflow only defines `workflow_dispatch`, and no cloud action was run.
- **Cost/resources:** no package downloads or installations, Docker build/container,
  AWS API call, Terraform plan/apply, model download, GPU operation, or spend.
- **Next:** keep PR #84 open for owner review; proceed with independent non-billable
  readiness tasks. Do not merge without owner review; do not apply AWS infrastructure.

## 2026-11-28 — PR #84 implementation checks passed

- **Phase:** Phase 2 static Terraform preparation; no AWS/GPU operation.
- **Branch/PR:** `codex/gpu-network-plan-review`, PR #84, implementation head
  `724c45a`, stacked on PR #83.
- **CI evidence:** run `46147292091` passed all six required jobs: Python, manifests,
  supply chain, Ansible, GPU observability, and local end-to-end. The end-to-end job
  completed successfully after 6m14s.
- **Local evidence:** 43 focused plan/wrapper tests passed; Ruff, docs-link validation
  across 35 files, and `git diff --check` passed.
- **Change:** the saved-plan validator now checks the project VPC/subnet values and
  network resource bindings. See ticket84 for scope and limits.
- **Limits/cost:** CI and fixtures do not prove a live AWS provider plan, network
  routing, Session Manager access, or a GPU host. No AWS resource, GPU hour, model
  download, local clean-room run, or project spend occurred.
- **Next:** keep PR #84 open for owner review; continue remaining non-billable
  readiness work. No merge or cloud apply is authorized by this entry.

## 2026-11-28 — Verify saved-plan network topology

- **Phase:** Phase 2 static Terraform preparation; no AWS or GPU operation.
- **Starting state:** PR #83 head `4c75115` passed 39 focused plan/wrapper tests and
  all six required CI jobs in run `46146275508`. Its earlier failure on
  `d3c2264` was caused by an outdated shell-wrapper plan fixture and is recorded
  below.
- **Branch/worktree:** `codex/gpu-network-plan-review`, based on the final PR #83
  head in `/private/tmp/multi-tenant-ai-inference-platform-pr84`.
- **Objective:** the saved-plan review checked SG ingress/egress rules, but did not
  check whether the instance, subnet, VPC, route, gateway, and association were wired
  into one project topology.
- **Research:** reviewed HashiCorp's official Terraform plan JSON documentation.
  Known CIDR/DNS values can be checked under resource changes; generated IDs are
  unknown until apply, so configuration references are checked to bind those values.
- **Changes:** require the exact project VPC and subnet ranges and DNS/public-IP
  settings; require one default route; verify gateway, subnet, route table, route
  association, security group, and instance resource references. Added negative
  fixture cases for wrong VPC/subnet/route-table bindings and a changed subnet range.
  Added ticket84 and wired it into the documentation link checker.
- **Validation:** combined saved-plan and fake-wrapper suites passed **43 tests**;
  Ruff passed. Terraform provider tests were not repeated locally; CI covers the full
  test suite.
- **Evidence limits:** this is fixture/static evidence. A real AWS-provider plan is
  required to verify the exact JSON expression shape; the tests do not prove
  connectivity, public routing, SSM, or host behavior.
- **Cost/resources:** no AWS API call, Terraform plan/apply, GPU instance, model
  download, Docker build, clean-room run, or spend.
- **Next:** finish the ticket, goal, backlog, evidence, and docs-link updates; publish
  PR #84 on top of #83; then let required CI validate the new head.

## 2026-11-28 — Bind the saved GPU expiry target to project resources

- **Phase:** Phase 2 static-only Terraform safety preparation; no GPU or AWS mutation.
- **Starting state:** PR #82 final head `d5afac7` was clean and all six required CI
  jobs passed in run `46143890538`. The saved-plan validator checked the project
  schedule group and `TerminateInstances` action, but not the configured target role
  or resource references.
- **Branch/worktree:** `codex/gpu-expiry-binding-review`, based on PR #82 in
  `/private/tmp/multi-tenant-ai-inference-platform-pr83`.
- **Research:** read HashiCorp's official Terraform JSON output format. Since an EC2
  identifier and generated IAM role ARN can remain unknown until apply, the plan's
  `change.after` values may omit them; the parsed configuration retains expression
  references that can be compared by exact resource address.
- **Changes:** the saved-plan validator now requires the expiry schedule target to
  reference this GPU instance and the project's expiry role. It also requires the
  expiry IAM policy's role and resource references to bind to those same resources.
  Added fixture cases for incorrect target roles and instance references, ticket83,
  docs index entry, and documentation-link validation.
- **Failed approaches:** the first test command used `python`, unavailable on the
  workstation; `python3` was Python 3.14 without pytest. The first test run then
  exposed an incorrect expectation that the IAM policy's ARN reference also included
  the `.id` path; the code and fixture were corrected to the actual `.arn` reference.
- **CI failure and fix:** PR #83 run `46145456879` showed that the shared wrapper
  test fixture also needed Terraform's configuration expressions. The saved-plan
  validator correctly refused its older resource-changes-only fixture. Added the
  same role/instance/action bindings to that fake plan; the combined validator and
  wrapper suites then passed **39 tests**. A new PR CI run is still required.
- **Validation:** the focused validator suite passed **24 tests**;
  Ruff passed, the local docs-link checker validated 34 Markdown files, and
  `git diff --check` passed. The first local focused run did not include the wrapper
  suite, which is why CI caught the incomplete fixture update.
  Terraform fixture checks do not prove the live AWS provider's JSON shape. The next
  permitted remote plan should confirm it before any apply.
- **Security/evidence limits:** this checks resource references, not the runtime
  schedule's successful delivery. Terraform mock tests separately check the policy
  action and scope; a real scheduled termination remains unverified. No AWS query or
  mutation, Terraform plan, GPU operation, model download, Docker build/container,
  local clean-room run, or project spend occurred.
- **Next:** update the PR record, push the wrapper fixture fix to PR #83, and watch
  its new CI run. Do not merge without owner authorization.

## 2026-11-28 — Restack and validate PR #58 local tenant and operator preparation

- **Phase:** Phase 2 remains quota-blocked; Phase 3–6 code and instructions are being prepared without a GPU.
- **Branch / PR:** `codex/gpu-manual-reproduction-guide`, PR #58, rebased from former base `4795f12` onto PR #57 head `d5e4570`.
- **Rebase choice:** kept the updated upstream goal/status text where old PR #58 commits carried stale snapshots. PR #58-specific failures remain in ticket #58 and this journal; source and test changes remain in the branch diff.
- **First test attempt:** focused gateway tests failed during collection because the new worktree did not contain the ignored, locally generated `models/tiny-intent-classifier.onnx` CPU fixture. Ran `make install` in the new PR #58 worktree; it created the local Python environment and both local ONNX fixtures. No clean-room cleanup was run.
- **Validation:** `make verify` passed Ruff, **153 tests** (2 skipped), dependency audit, Compose/monitoring checks, and benchmark/evaluation/CUDA dry-run plans. One existing Starlette/httpx warning remains. The suite made zero GPU operations and zero model-network requests.
- **Historical troubleshooting retained:** earlier PR #58 workflows failed because the Trivy installer could not locate the requested versions and the smoke script hid a failing assertion. The package switched to a checksum-verified release archive and named, secret-safe smoke assertions. The initial Redis outage drill exposed HTTP 500 from a rollout-state read; the fix returns fail-closed 503 and persists rollout state before changing local weights. Earlier CI validated recovery and cross-gateway cancellation using local CPU Compose.
- **Cost and limits:** no AWS, GPU, model download, or cloud spend. No local clean-room run was performed; keep the single integrated clean-room run for after the stack stabilizes.
- **Next:** publish the rebased branch with an exact force-with-lease, run its required checks once, then continue restacking PRs #59–#71.

## 2026-11-28 — Rebase and validate Ansible host configuration

- **Phase:** Phase 3 static host-configuration preparation; no GPU host access.
- **Branch / PR:** `codex/gpu-ansible-host-configuration`, PR #57, rebased from PR #56 head `3292af9` onto updated PR #56 head `b9d41f6`.
- **Rebase:** three PR #57 commits replayed. Preserved the newer PR #55/56 goal and journal state, and retained the PR #57 implementation and review-fix history.
- **Failed command:** `make gpu-ansible-validate` initially failed because the isolated Ansible executable was not on `PATH` (`ansible-playbook: command not found`). No configuration ran.
- **Successful validation:** reran with `PATH=/tmp/gpu-ansible-venv/bin:$PATH`; playbook syntax passed. Ruff and `git diff --check` passed.
- **Cost and limits:** local static validation only; no AWS, host setup, GPU, package installation on EC2, or spend. A fresh PR CI run remains necessary after publication.
- **Next:** publish the rebased PR #57 branch with an exact force-with-lease, then continue restacking its descendants.

## 2026-11-28 — PR #56 release-manifest review fix passed CI

- **Phase:** Phase 9 static release tooling; Phase 2 remains quota-blocked.
- **Branch / PR:** `codex/gpu-release-host-controller`, PR #56, tested head
  `473db1cee7fa0aacb826d7a6e94fbf020c7c9c74`.
- **Validation:** GitHub Actions run `46105533251` passed all five required jobs,
  including the fresh-runner local CPU end-to-end sequence. Local Ruff and the focused
  release-controller suite passed **17 tests**. Governance validation records the
  original successful clean-room sequence and this updated-head run.
- **Result:** the `manifest-from-report` review finding is fixed; no host-state files
  are required to generate a metadata manifest. The CLI regression fails if a host
  controller is constructed during manifest generation.
- **AWS / GPU / cost:** none; no AWS operation, EC2 host, model artifact, GPU, or spend.
- **Next:** reply to and resolve the release-controller review finding; continue
  remaining non-billable work and do not merge without authorization.

## 2026-11-28 — Fix PR #56 manifest command initialization

- **Phase:** Phase 9 static model-release preparation; Phase 2 remains blocked by zero applied G/VT quota.
- **Branch / PR:** `codex/gpu-release-host-controller`, PR #56, rebased onto the updated PR #55 branch.
- **Review finding:** the metadata-only `manifest-from-report` command must not construct the host controller because its parser has no host state arguments and does not need Docker or EC2 access.
- **Fix:** host controller creation now occurs only for commands that use host state or host controls. A CLI regression test makes construction fail if the report-only command tries to initialize the controller.
- **Validation:** the focused release-controller suite passed 17 tests; Ruff and `git diff --check` passed. Previous CI for the pre-rebase head passed; a fresh run is required for this rebased stack.
- **Limitations and cost:** this proves local control flow only. No AWS, GPU, model download, host rollout, or spend occurred.
- **Next:** finish the current branch rebase, rerun focused tests, publish with an exact force-with-lease, and validate in CI.

## 2026-11-28 — Rebase authenticated release planning onto approval-integrity fix

- **Phase:** Phase 9 static model-release preparation; quota-gated GPU validation remains pending.
- **Branch / PR:** `codex/gpu-llm-release-api`, PR #55, rebased from predecessor `69f0b39` onto PR #54 head `cfcc1be`.
- **Troubleshooting:** the rebase exposed overlap in the plan store and tests. Kept the newer store guard that rejects inserted plans with an approver, and retained #55 manifest-digest checks. An initial focused test run found that #54 now requires champion and candidate manifests as keyword arguments; updated the invalid-insert and normal-save test paths to supply both.
- **Validation:** focused release-control and API suites passed **13 tests**; Ruff and `git diff --check` passed. One pre-existing Starlette/httpx deprecation warning remains.
- **Cost and limits:** local tests only; no AWS, GPU, model download, or spend. The required single integrated clean-room run remains planned after the static stack settles; no second clean-room run was started.
- **Next:** publish the rebased PR #55 branch with an exact force-with-lease, run its checks, then restack descendants and resolve conflicts without losing each package's evidence.

## 2026-11-27 — Quota status rechecked without mutation

- **Phase:** Phase 2 static-only EC2 preparation; no AWS mutation.
- **Current state:** AWS email supplied by the owner reports that the initial 4-vCPU request was denied. The owner reports manually sending an appeal through the existing case. The latest read-only Service Quotas history still reports `CASE_OPENED`; applied quota is `0.0` vCPUs. These sources have not yet reconciled.
- **Decision:** do not submit a duplicate request or start billable infrastructure. Continue non-billable code, deployment, and runbook preparation.
- **Cost:** no resources or GPU instance-hours used by this check.

## 2026-11-27 — Attempt the authorized quota-case update with AWS CLI

- **Phase:** Phase 2 — static-only EC2 preparation; GPU execution remains blocked.
- **Branch / PR:** `codex/quota-case-cli-followup`, preparing a focused PR #41 on top
  of PR #40.
- **Objective:** follow the owner's instruction to reopen the existing denied quota
  case through the CLI, while avoiding a duplicate quota request or support case.
- **AWS identity and case:** verified `ai-platform-pilot-key` caller account against
  the expected project account. The support case reference was obtained from the
  existing quota record and the AWS email; the identifier is intentionally omitted
  from the public repository.
- **Attempt:** inspected `aws support help`; it has `add-communication-to-case` but no
  `reopen-case` command. Used the available add-communication operation with the
  prepared appeal text and existing case reference. AWS returned
  `SubscriptionRequiredException` before accepting any communication.
- **Failed approach:** the SSO profile had no cached token, so an SSO device-auth
  login was briefly started. After the owner clarified to use CLI only, it was
  canceled before sign-in; no browser interaction or AWS change occurred.
- **Alternative checked:** `aws service-quotas create-support-case` only applies to
  quota requests with status `PENDING`. This request still reports `CASE_OPENED`, so
  that command would not reopen it and was not called.
- **Post-check:** a fresh read returned `CASE_OPENED` and desired quota `4.0`; applied
  quota remains `0.0`. No new request, support case, communication, resource, GPU hour,
  or spend was created.
- **Support path:** AWS's official guide documents reopening a resolved case through
  the Support Center. The owner's explicit CLI request has been attempted, but the
  API route is blocked by the account's Support plan. Keep the project moving on
  non-billable tasks; do not launch with zero applied quota.
- **Next:** submit this truthful blocker record in PR #41 and continue remote-state,
  cost, expiry, and automation work that does not require GPU runtime.

## 2026-11-27 — PR #40 status follow-up checks passed

- **Phase:** Phase 2 static-only preflight; no cloud resource creation or spend.
- **Command:** read-only AWS Service Quotas queries in `us-east-1` checked the existing
  request and applied G/VT quota using `ai-platform-pilot-key`.
- **Result:** request `[request reference redacted]` remains
  `CASE_OPENED`, requested value `4.0`; the applied `Running On-Demand G and VT
  instances` quota is `0.0` vCPUs.
- **Decision:** do not retry the request or launch infrastructure. This is status
  evidence only; quota approval would still not authorize Terraform apply.
- **Cost:** no AWS resources or spend; GPU instance-hours remain `0`.

## 2026-11-27 — PR #35 lease held during tokenizer preflight

- **Phase:** Phase 6 non-billable gateway correctness work. Phase 2 remains the active
  cloud phase; no AWS resource or GPU was used.
- **Branch / PR:** `codex/tokenizer-admission-preflight`, PR #35 stacked on PR #34.
  Code fix commit: `59cca44`; docs and rebase follow-up are local pending publication.
- **Starting state:** PR #35 was based on old PR #34 head `ae99959`; PR #34 had been
  rebased and updated to `b51aedd`. The PR #35 branch had diverged after both histories
  changed.
- **Objective:** resolve review finding that tokenization can take longer than the
  concurrency lease, allowing admission to expire before the exact token reservation.
- **Rebase/troubleshooting:** rebased PR #35 with
  `git rebase --onto origin/codex/redis-admission-leases ae99959940b217495ae5a2e231656965b2a4ce2f
  codex/tokenizer-admission-preflight`. Conflicts affected shared goal/status/journal
  docs and `test_vllm_streaming.py`. Kept the updated PR #34 documentation and combined
  unique PR #35 test functions with current stream regression tests. A targeted test run
  then found five `NameError` failures because the merged test file lacked its
  `HTTPException` import; restored the import and reran successfully. No conflict markers
  or partial rebase remain.
- **Change:** start a bounded lease watcher immediately after vLLM admission, retain it
  through `/tokenize` and exact reservation adjustment, then stop it on all success,
  rejection, error, and cancellation paths. Normal generation and streaming start their
  own watcher after preflight.
- **Validation:** targeted stream/lease suite passed **21 tests**. `make verify` passed
  Ruff, **87 tests**, pip-audit and Compose config (2 optional Redis tests skipped; one
  existing Starlette deprecation warning). Redis 7.4 integration passed **2 tests**.
  `git diff --check` passed. The integration container was stopped and is absent.
- **Review response:** resolved the stale second-clean-cycle finding based on the
  owner's explicit rule: one successful cycle is sufficient, and the two historical CPU
  cycles remain evidence.
- **Cloud/cost:** no AWS calls, GPU, or live vLLM; goal-specific spend remains `$0` and
  GPU hours remain `0`.
- **Follow-up:** pushed PR #35 head `5cd8dfb` with `--force-with-lease`, updated its
  description, resolved both review threads, and watched one CI run to success. Run
  `45937540562` passed all four required jobs.

## 2026-11-27 — PR #36 carried onto the tokenizer lease fix

- **Phase:** Phase 6 non-billable gateway tests. The active cloud phase remains Phase 2.
- **Branch / PR:** `codex/vllm-preflight-failure-cleanup`, PR #36 stacked on PR #35.
  Local source commit `ec5dcd1`; local documentation commit `a8d3278`.
- **Starting state:** PR #36 targeted the earlier #35 branch at `a8e63b8`; #35 had
  moved to `5cd8dfb` after the tokenizer lease fix.
- **Action:** ran `git rebase --onto origin/codex/tokenizer-admission-preflight
  a8e63b8 codex/vllm-preflight-failure-cleanup`. Two commits replayed. Shared goal,
  status, backlog, journal, evidence, and validation docs conflicted; retained the newer
  #35 state and preserved the #36 ticket, test additions, and validation entry.
- **Validation:** `make verify` passed Ruff, **90 tests**, pip-audit, and Compose
  configuration; 2 optional Redis tests were skipped, with one existing Starlette
  warning. `git diff --check` passed. No full clean-room run was started because the
  existing PR CI cycle is the relevant reproduction gate.
- **Limits:** cancellation and Redis outage use deterministic local doubles; tokenizer
  timeout uses `MockTransport`. No real Redis failure, live vLLM, AWS, or GPU was used.
- **Cloud / cost:** no AWS resource or spend; GPU hours remain `0`.
- **Next action:** publish this rebased PR #36 branch with `--force-with-lease`, update
  the PR evidence, then watch its CI once.

## 2026-11-27 — Redis lease review fixes and branch recovery

- **Phase:** Phase 6 non-billable gateway correctness prework. The active cloud
  implementation phase remains Phase 2; no cloud resource was created or changed.
- **Branch / PR:** `codex/redis-admission-leases`, PR #34 stacked on PR #33. Code fix
  commit: `4cffc60`, documentation head `b51aedd`. The rebased branch was pushed with
  lease protection; both review threads were resolved and all four required checks
  passed in run `45936485832`.
- **Starting state:** local branch was rebased onto PR #33 head `c5de757`, while the
  GitHub PR branch still pointed to `ae99959940b217495ae5a2e231656965b2a4ce2f`.
  Five validation and goal documents contained local updates that had not been committed.
- **Objective:** close two lease-lifecycle review findings, record actual test evidence,
  and make the reviewed branch reflect the rebased source.
- **Commands / troubleshooting:** inspected `git status`, branch history and PR state;
  the local and remote histories diverged after the first rebase. An initial rebase
  replayed PR #33 ancestors and produced conflicts; it was aborted. The corrected
  `git rebase --onto origin/codex/gateway-stream-accounting e87753c
  codex/redis-admission-leases` replayed only PR #34 commits. Documentation conflicts
  were resolved by retaining the newer PR #33 documentation and PR #34 ticket/code.
- **Changes:** bounded asynchronous lease renewal and request cancellation before
  expiry; reject renewal after expiry; prune stale reservation metadata on later
  admissions while retaining conservative token-ledger entries through their windows.
  Added regression tests for an unresponsive renewal and repeated crash cleanup.
- **Validation:** `make verify` passed Ruff, 75 tests, pip-audit and Compose config; two
  optional Redis integration tests were skipped in the no-Redis run. A disposable
  local Redis 7.4 container ran the relevant lease suite with 7 passing tests. The
  container was stopped after the test. The evidence and test limitations are in
  `VALIDATION.md` and `EVIDENCE_MANIFEST.md`.
- **Failed approaches:** the first rebase attempt replayed the wrong ancestor range and
  caused conflicts in files already changed by PR #33. It was aborted before any push;
  the `--onto` rebase used the old PR #34 base commit to replay only its own work.
- **Cloud / cost:** no AWS API, GPU, or live vLLM was used in this package. Goal-specific
  spend remains `$0`; GPU instance-hours remain `0`.
- **Completion:** the rebased PR #34 branch was published, both review threads resolved,
  and all four required checks passed as recorded above. Work then moved to PR #35.

## 2026-11-27 — Clean-room run count clarified

- **Scope:** verified the repository's clean-room requirements after the owner clarified
  that one successful run is sufficient.
- **Finding:** `AGENTS.md` and the pull request template required a second bootstrap/demo;
  the GPU goal's final acceptance text already described one reproduction. Historical
  CPU evidence records two successful runs, but no GPU clean-room run has started.
- **Decision:** one successful clean-room cycle satisfies this GPU goal and the shared
  implementation-PR gate. Repeat only after a failed cycle or a material correction that
  requires revalidation. Historical records remain unchanged.
- **Changes:** aligned `AGENTS.md`, the PR template, goal document, and implementation
  status with that decision.
- **Validation:** source review only; no runtime clean-room cycle was run. No AWS resource
  was created or changed.
- **Next step:** continue Phase 2 non-billable work; retain the single clean-room run for
  Phase 12 after the GPU automation and evidence process are ready.

Preserve earlier entries. Record actual actions and outcomes; never replace failed attempts with a clean narrative. Keep credentials, tokens, private data, raw Terraform state, and sensitive logs out of this file.

## 2026-11-26 — Goal registration and initial audit

- **Phase:** 1 — repository audit, research, and architecture.
- **Branch / PR:** `codex/single-l4-gpu-goal` / [#30](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/30), draft and open.
- **Starting repository:** clean `main`, `c8f02ed`; tracking `origin/main`.
- **Starting AWS state:** not yet queried in this project. No cloud mutation was performed.
- **Objective:** register the persistent project charter and inspect baseline implementation before GPU architecture work.
- **Commands and checks:** inspected `AGENTS.md`, README, repository file inventory, system map, vLLM adapter and gateway selection, tenant/catalog/auth/Redis admission code, Terraform EKS root and GPU module, Kubernetes vLLM manifest, Compose, Makefile, CI, status/backlog, and validation history; ran `gh auth status` and `gh pr list` (authenticated as Bepoadewale; no open PR listed); `make verify`; `docker compose config --quiet`; `make cloud-delivery-validate`; read-only AWS identity, tag inventory, instance inventory, instance-type offerings, quota, and Price List API lookup; official docs/model-card research.
- **Findings:** local production claim is CPU ONNX only; gateway has a vLLM HTTP adapter selected by `backend_url`; Redis quotas and server-side Ed25519 tenant identity exist; current GPU deployment manifests are Kubernetes/EKS contracts and explicitly outside execution; Terraform EKS root includes NAT/RDS/ElastiCache and must not be used for this project.
- **Issues to audit:** streaming token accounting counts chunks, streaming supplies a fixed TTFT, quota reservation estimates whitespace-delimited words; Redis release accepts `actual_tokens` but its Lua release only decrements active requests, while daily and minute token ledgers retain estimated reservations; mutable `latest` vLLM image and a different model in the old Kubernetes contract; no isolated EC2 deployment root identified in the source inventory.
- **Changes:** added goal, proposed architecture, status, risk, research, and execution records; linked the goal from README and docs index.
- **Tests / validation:** `make verify`: Ruff passed; 50 tests passed, one Starlette deprecation warning; `make audit` failed with 84 known vulnerability records across seven packages and exit 2 after retries, so full command failed before Compose validation. `docker compose config --quiet` passed when run separately. `make cloud-delivery-validate` and `make terraform-validate` passed. Historical results remain distinct from current results; see `VALIDATION.md`.
- **Cloud resources/cost:** none created or changed. Read-only project-tagged resource and EC2 instance queries returned no matches in `us-east-1`. G/VT On-Demand quota is 0 vCPUs. AWS Price List API lookup returned g6.xlarge Linux On-Demand `$0.8048/hour` in US East (N. Virginia), giving `$6.4384` for 8 hours and `$9.6576` for 12 hours before storage, IPv4, transfer, state, logging, and taxes. No spend estimate is yet complete or authorized for apply.
- **Decisions:** favor On-Demand as requested; no Spot plan. Do not request quota increase or apply Terraform during Phase 1. Treat quota increase as a pending AWS account change requiring explicit preparation and authorization review.
- **Pull request:** created draft PR #30 at commit `754564d`; documentation-only registration. CI status will be recorded after the existing PR checks complete. Per repository policy, no merge or clean-room readiness claim is made here.
- **Next action:** deepen Phase 1 audit and official source research; identify safe baseline audit remediation as a separate focused package; then open the docs-only goal-registration PR.
- **Next action:** finish source audit, run `make verify` as explicitly requested, record exact outcomes, then complete read-only AWS inventory and official documentation research.

## 2026-11-26 — Dependency audit repair and clean-room verification

- **Phase:** Phase 1 — repository audit, research, and architecture. This was a
  non-billable local implementation package to restore the baseline validation gate.
- **Branch / PR:** `codex/fix-baseline-dependency-audit`; [PR #31](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/31), draft and open. Commits `e1d9aa0` and `9710932`. The goal registration PR is #30; its required checks passed on the observed revision.
- **Starting repository:** started from a new branch based on `main` at
  `c8f02ed`, then committed the source fix and evidence. `gh auth status` confirmed
  the existing Bepoadewale GitHub session; no credential was printed or stored.
- **Starting local state:** an existing `.local/self-service/profiles.db` predated
  this work. It was moved to `/tmp/multi-tenant-ai-inference-platform-self-service-profiles.db`
  before project cleanup and restored to its original path after final cleanup.
- **Objective:** resolve the pre-existing pip-audit failure in local and container
  installs and establish fresh clean-room evidence before review.
- **Commands and checks:** `make install`; `make bootstrap-local`; `make smoke`;
  `make demo-flagship`; `make verify`; `make clean-local` (two successful clean-room
  cycles); `docker build -t inference-gateway:dependency-audit -f gateway/Dockerfile .`;
  `git diff --check`; GitHub PR checks are under one watcher using
  `gh pr checks 31 --watch --interval 120`.
- **Changes:** added root `constraints.txt` with safe minimum versions for seven
  affected transitive dependencies; applied it to Makefile install and the gateway
  Dockerfile. Updated README, `PROJECT_STATUS.md`, `docs/governance/VALIDATION.md`,
  and ticket #31. The constraints prevent resolutions below current audit fixes but
  are not a complete lock file.
- **Validation:** PR branch `make verify` passed Ruff, 50 tests (one existing
  Starlette/httpx deprecation warning), pip-audit (`No known vulnerabilities found`,
  editable project skipped), and Docker Compose configuration. Local image build
  passed on arm64. Fresh bootstrap, smoke, and cumulative CPU/local demo passed.
  Final cleanup left no project Compose containers, generated `.venv`, or generated
  `models/`; the standalone test image was removed.
- **Failed approaches and diagnosis:** after an initial demo sequence had populated
  Redis, rerunning the cumulative demo against that same state returned 429 in
  `demo-agent-tools`, because the synthetic tenant's minute allowance had already
  been consumed. The failed rerun was retained as troubleshooting history, not counted
  as a clean-room pass. A new project cleanup and bootstrap reset Redis, and the full
  demo then exited 0. Expected connection resets during controlled restarts were
  visible in logs; the relevant recovery assertions passed.
- **Evidence:** full results in `docs/governance/VALIDATION.md`; detailed acceptance
  checklist in `docs/tickets/ticket31.md`; reviewable source and validation changes in
  PR #31. No screenshot was generated. No AWS command was needed for this package.
- **Cloud resources/cost:** no cloud resource was created or changed; GPU instance
  hours remain 0; AWS spend from this package is $0. The pre-existing local profile DB
  was restored. No other local generated artifacts remain.
- **Decisions:** keep this fix isolated from the GPU goal PR. Do not mark PR #31
  review-ready until CI is terminal. The PR remains draft pending checks/review.
- **Blockers:** PR #31 CI result is pending. Separately, first G6 launch remains
  blocked by quota `L-DB2E81BA` at 0 vCPUs and by the unresolved full $25-bound cost,
  expiry, resource, and teardown plan.
- **Next action:** review gateway vLLM schema and token/accounting/cancellation paths,
  continue official compatibility and price research, and record the exact dependency
  PR CI outcome before updating the project goal state.

## 2026-11-26 — GPU stack compatibility research

- **Phase:** Phase 1 — official research; no infrastructure or local application
  runtime was started.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30, draft.
- **Starting state:** persistent goal updated to include PR #31, its local evidence,
  current quota blocker, and prior checks. PR #31's CI watcher was still active; no
  result was assumed.
- **Objective:** refine the candidate host/GPU runtime compatibility model from current
  primary sources, and correct the EC2 L4 memory description to match AWS's units.
- **Commands / research:** browsed the AWS EC2 accelerated-instance table and public
  NVIDIA driver guide, NVIDIA CUDA compatibility matrix, PyTorch local-install guide,
  and current vLLM stable and latest GPU guides.
- **Findings:** AWS lists `g6.xlarge` as 4 vCPUs/16 GiB system memory and 1 L4 with
  22 GiB GPU memory; `g6.2xlarge` is 8 vCPUs/32 GiB and the same 22 GiB GPU memory.
  AWS's Ubuntu 24.04 x86_64 CUDA example installs matching kernel headers and shows
  CUDA 13.0/driver 580.65.06. NVIDIA's broad minor-compatibility table lists driver
  family 580+ for CUDA 13 and 525+ for CUDA 12, subject to toolkit-specific requirements
  and feature limits. Current vLLM stable docs list L4 support, Linux/Python 3.11–3.14,
  default CUDA 12.9 wheel plus 12.8/13.0 choices, and warn of compiled-kernel binary
  compatibility. vLLM wheels bundle PyTorch, so serving should use the matching bundled
  build; a separate PyTorch learning workload should use an isolated environment.
  Fractional `g6f` L4 slices do not meet the one-full-L4 project constraint.
- **Changes:** expanded `RESEARCH_NOTES.md` with the sources, version implications,
  candidate-but-unpinned stack, and open verification gates; corrected memory values;
  updated the risk register for PR #31 and the exact-tag inventory boundary.
- **Validation:** research only. These documents do not establish actual runtime
  compatibility, driver availability for the eventual AMI/kernel, live capacity,
  inference, or GPU performance.
- **Cloud resources/cost:** none created or changed; no billable operation.
- **Next action:** complete source audit and price the full bounded stack; wait for
  PR #31 CI through its existing watcher. No quota request or apply is authorized.

## 2026-11-26 — PR #31 checks completed

- **Phase:** Phase 1; dependency repair is a local non-billable support package.
- **Branch / PR:** PR #31, `codex/fix-baseline-dependency-audit`, commits `e1d9aa0`
  and `9710932`.
- **Checks:** the single `gh pr checks 31 --watch --interval 120` process completed
  successfully. Both workflow runs passed Python, manifests, supply-chain, and
  `local-e2e`; observed run IDs were `45906309837` and `45906313982`.
- **Decision:** mark the change ready for human review now that the repository-required
  implementation clean-room evidence and GitHub checks have both passed. Do not merge
  without the normal approval/review requirements.
- **Cloud resources/cost:** none created or changed; no GPU time and no AWS spend.
- **Next action:** continue Phase 1; PR #30's latest docs-only checks remain on their
  existing watcher.

## 2026-11-26 — Goal registration PR checks completed

- **Phase:** Phase 1 registration documentation; runtime clean-room execution is not
  applicable to this documentation-only PR.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30; goal/research documentation
  current commit will be recorded with this journal update.
- **Checks:** the single `gh pr checks 30 --watch --interval 120` process completed
  successfully. Both workflow runs passed Python, manifests, supply-chain, and
  `local-e2e`; observed run IDs were `45906505681` and `45906511022`.
- **Decision:** PR #30 and PR #31 are both marked ready for review. No merge has been
  performed; the normal approval and PR-only workflow remain in force.
- **Cloud resources/cost:** none created or changed; no GPU time and no AWS spend.
- **Next action:** continue non-billable Phase 1 source audit, official references,
  capacity/price review, and exact bounded-cost design while the PRs await review.

## 2026-11-26 — State and expiry cost-control research

- **Phase:** Phase 1; planning only.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30; no AWS account mutation.
- **Sources consulted:** official HashiCorp S3 backend and state locking guides, AWS
  Session Manager security guidance, S3 pricing page, and EC2 service authorization
  reference.
- **Findings and decision candidates:** use Terraform's versioned, private, encrypted
  S3 backend with native `use_lockfile=true` and a dedicated pay-per-request DynamoDB
  lock table because the repository's `AGENTS.md` requires one per cloud root. HashiCorp
  marks DynamoDB locking deprecated, so test dual-lock behavior and retain the table
  only while that repository policy requires it. Session Manager itself has no
  EC2 connection fee; interface VPC endpoints add hourly/data charges, so the current
  minimum-cost candidate is one public IPv4 with no inbound service rules and outbound
  HTTPS, after recording its egress risk. Treat inbound model/image transfers as free
  only where the applicable AWS price rules say so; the final estimate must include
  S3 state requests/versions, IPv4, EBS, transfer, logs, taxes, and all other actual
  line items, without relying on free-tier eligibility.
- **Expiry candidate:** a boot-scheduled systemd shutdown timer plus EC2
  `instance_initiated_shutdown_behavior = "terminate"` avoids a permanent Lambda or
  broad terminate role. This design is only proposed. Its scheduling, host clock,
  cloud-init failure behavior, volume deletion, and actual instance termination must
  be tested before any GPU batch.
- **Changes:** refined proposed architecture and research notes; updated the risk
  register. No Terraform resource or IAM permission was created.
- **Cost boundary:** current `$9.7309` 12-hour subtotal remains partial (GPU, one
  public IPv4, 100 GiB gp3 only). It is not a complete estimate, cost authorization,
  or apply approval. Current G/VT quota remains zero.
- **Next action:** complete exact price and expiry checklist and static validation of
  the proposed EC2-only root before requesting any paid run or account change.

## 2026-11-26 — Phase backlog and proposed architecture expanded

- **Phase:** Phase 1 — architecture and non-billable preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal`, PR #30; commit `336c1b4` has been pushed
  and its required GitHub checks are running.
- **Starting state:** both PRs #30 and #31 are ready for human review; #31 has passing
  local and CI evidence. No AWS mutation has occurred.
- **Objective:** finish the architecture deliverables required for Phase 1 and make
  the implementation sequence reviewable before any infrastructure work.
- **Changes:** expanded the proposed architecture with the Linux/GPU software stack,
  identity and admission sequence, LLM request execution/KV cache, GPU telemetry, and
  rationale for a single EC2 host instead of EKS. Added the 10-package ordered
  `IMPLEMENTATION_BACKLOG.md` and linked it from the docs index. The backlog records
  dependencies, exit gates, cost boundaries, and the zero-quota blocker.
- **Research used:** official HashiCorp S3-native locking docs, AWS Session Manager and
  S3 pricing guidance, EC2 tag-scoped terminate authorization, EC2 L4 specs, NVIDIA
  CUDA compatibility, current vLLM stable GPU guide, and PyTorch installation docs.
  All architecture is labeled proposed; no diagram is a deployment record.
- **Validation:** `git diff --check` passed before commit. PR #30 CI is the validation
  gate for this documentation-only update. No local model or cloud runtime was started.
- **Cloud resources/cost:** none created or changed; instance-hours remain zero.
  Current partial estimate remains `$9.7309` for 12 hours of instance + IPv4 + sample
  100-GiB gp3 only; it is not a total estimate or authorization.
- **Open items:** remaining API/security source audit, official Docker/Toolkit/DCGM/
  monitoring/MLflow/Redis/evaluation research, complete cost model, exact expiry tests,
  quota gate, and eventual PR reviews.
- **Next action:** finish the remaining code audit and cost analysis before drafting
  any billable plan. Do not raise the GPU quota or apply infrastructure at this stage.

## 2026-11-26 — Container GPU and telemetry research

- **Phase:** Phase 1 research; no package installation or AWS changes.
- **Branch / PR:** `codex/single-l4-gpu-goal`; PR #30's documentation commit `336c1b4`
  is under its existing CI watcher.
- **Sources consulted:** official NVIDIA Container Toolkit install guide; Docker
  Compose GPU device reservation guide; NVIDIA DCGM Exporter release notes and release
  strategy; OpenTelemetry semantic convention writing and GenAI conventions pages.
- **Findings:** install the NVIDIA driver before Container Toolkit; current toolkit
  guide documents `1.20.2-1` and a systemd cgroup reload GPU-visibility issue.
  Compose requires `capabilities: [gpu]` and supports a one-device count but this
  grants device visibility, not GPU partitioning. DCGM Exporter 4.8.4 currently
  reports DCGM 4.6.1 components and distinguishes immutable full image tags from
  mutable `latest`; pin digest and validate actual fields. OpenTelemetry asks for
  explicit opt-in treatment for sensitive/verbose attributes; do not export prompt
  or completion content or credentials by default.
- **Changes:** recorded source/date and implementation implications in
  `RESEARCH_NOTES.md`. The GPU observability architecture remains proposed.
- **Validation:** documentation research only; no exporter, GPU container, telemetry,
  metrics, or alerts were run.
- **Cloud resources/cost:** none; instance-hours remain zero.
- **Next action:** continue remaining official references and source audit; then finish
  an exact total cost and expiry plan before considering any AWS change.

## 2026-11-27 — Phase 1 evidence and cost package completed

- **Phase:** Phase 1 complete as a repository audit/research/architecture gate; Phase 2
  starts with static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal`, PR #30. Its pushed head `336c1b4` has
  passed both required workflow runs; this additional documentation update is not yet
  committed or checked by CI. PR #31 is open and its required checks have passed.
- **Starting state:** documentation edits remained uncommitted after the #30 CI
  watcher ended. Zero AWS resources and zero GPU instance hours for this goal.
- **Objective:** close the source audit and Phase 1 research record, document current
  pricing inputs and evidence boundaries, and define the next static-only package.
- **Changes:** documented concrete API request/stream lifecycle risks, updated the
  official sources for monitoring, evaluation, model license, Terraform, Ansible,
  CUDA profiling, and current OpenTelemetry GenAI conventions; added a cost report and
  evidence manifest; recorded EventBridge Scheduler as the proposed independent
  expiry mechanism paired with guest shutdown. Marked Phase 1 complete and Phase 2
  static-only preparation active.
- **Cost model:** provisional 12-hour estimate is `$18.35`, including 12 hours at the
  2026-11-26 g6.xlarge catalog rate, one IPv4, 100 GiB gp3, temporary S3 state and
  S3/DynamoDB state lock, expiry invocation, a 10x data-egress placeholder, a 25% tax allowance, and a
  `$5` reserve. This is not a quote or authorization. Current G/VT quota is zero.
- **Validation:** official-source review and documentation inspection only; no cloud
  validation or local runtime started. `git diff --check` will be run before commit.
- **Cloud resources/cost:** none created/changed; spend `$0`; instance-hours `0`.
- **Known limitations:** the provisional estimate needs exact AMI, Price List, tax,
  account-level transfer, state-retention, and saved-plan confirmation. The expiry
  mechanism is proposed and not yet implemented or tested. The quota is unchanged.
- **Next action:** finish the static Terraform/expiry design in a focused PR; no AWS
  apply or quota request.

## 2026-11-27 — Repository state-lock policy and cost correction

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/single-l4-gpu-goal` / PR #30.
- **Starting state:** PR #30 head `80ca94e`; its two workflow runs were still active
  when the repository's state-lock requirement was reviewed.
- **Objective:** align the architecture and cost record with the repository rule that
  the cloud repository has its own DynamoDB lock table and roots use unique state-key
  namespaces, while keeping Terraform's current S3-native lock option documented.
- **Research and decision:** HashiCorp documents that S3 and DynamoDB backend locking
  can be configured together, but marks DynamoDB locking deprecated. The repository
  rule requires a repository-scoped DynamoDB table. A follow-up inspection of the
  actual `AGENTS.md` and existing bootstrap showed that the repository already defines
  this bucket and table. The GPU root will reuse them with a unique state key and
  test the pinned Terraform dual-lock path; it will not create a duplicate table.
  AWS Budgets direct-email alerts require recipient verification and can lag charges;
  they are not a runtime stop control.
- **Changes:** corrected the current rounded 12-hour envelope from `$18.34` to
  `$18.35`, added a small DynamoDB request allowance, documented email-alert
  verification, and updated the proposed state architecture, status, backlog, and
  evidence index. No Terraform resource was created.
- **Validation:** `git diff --check` passed. The existing PR #30 watcher reported
  Python, manifests, supply-chain, and local-e2e passing in both runs; `gh pr checks
  30` confirmed all displayed checks passed at `80ca94e`.
- **Cloud resources/cost:** none created or changed; AWS spend `$0`; GPU instance-hours
  `0`; quota remains `0` vCPUs.
- **Limitations:** estimate remains provisional. Exact price, tax, egress aggregation,
  state lifetime, resource plan, budget recipient verification, and expiry testing
  remain open before any apply.
- **Next action:** finish the static cost/design correction and prepare the isolated
  Phase 2 Terraform root in a separate pull request; keep it static-only.

## 2026-11-26 — Phase 2 single-L4 static root and AWS preview plans

- **Phase:** Phase 2 — isolated EC2 infrastructure, static-only.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended PR #32, based on PR #30 head
  `04cb564`.
- **Starting state:** PRs #30 and #31 remained open; PR #30's latest checks passed.
  This branch contained no Phase 2 Terraform root. Project AWS resources and GPU
  instance-hours were both zero.
- **Objective:** add a reviewable one-L4 root, independent expiry, scoped read-only
  preflight, exact-plan gates, and cleanup verification; produce AWS-backed previews
  without applying resources.
- **Research:** reviewed official Terraform S3 backend guidance, current AWS provider
  `5.100.0` schema, AWS quota/offerings, Canonical Ubuntu AMIs, AWS Systems Manager
  Agent setup, AWS budget notification pricing, and EventBridge Scheduler behavior.
- **Changes:** added a dedicated `gpu-ec2` Terraform root with one `g6.xlarge`, no
  inbound rules, outbound TCP 80/443, IMDSv2, encrypted 100 GiB gp3, scoped SSM and
  expiry roles, a guest `systemd` timer, and a one-time scheduled termination. Added
  account/quota/AZ/resource/bootstrap preflight, plan/apply/destroy scripts with
  checksum checks, a read-only resource-absence verifier, local-only preview plans,
  Make targets, and Phase 2 documentation. Reused the repository-level state bucket
  and DDB lock table under a distinct `gpu-ec2/` key after checking the actual
  `AGENTS.md` rule; created no duplicate table.
- **AWS read-only checks:** the expected account matched. Current On-Demand G/VT quota
  is `0.0` vCPUs. The `g6.xlarge` offering list currently includes `us-east-1a`, `1b`,
  `1c`, `1d`, and `1f`. Offerings do not reserve capacity.
- **Preview results:** the bootstrap local-state preview proposed `7 to add, 0 to
  change, 0 to destroy`; it used `operator@example.invalid` as a placeholder alert
  address. The GPU local-state preview proposed `14 to add, 0 to change, 0 to
  destroy`, exactly one `g6.xlarge`, AZ `us-east-1c`, and Canonical image
  `ami-0a951420c495183dc`. Together these show a preliminary 21-create scope. Plans
  are ignored under `.local/`, are not remote-backend plans, and must not be applied.
- **Validation:** final `make terraform-validate` passed the bootstrap, existing EKS,
  and new GPU roots with backend disabled. `make gpu-ec2-validate`, `bash -n
  scripts/gpu-ec2-*.sh`, and `git diff --check` passed. PR #30 checks passed at
  `04cb564`.
- **Failed attempts and fixes:** Terraform 5.100.0 rejected the optional
  `action_after_completion` argument; kept the pinned provider and rely on Terraform
  destroy to remove the non-recurring schedule. An HCL multi-line expiry expression
  needed parentheses. `terraform console` requested backend initialization and did
  not render the cloud-init file. The first `terraform show` command ran from the
  source root and could not load the plan copy's provider schema; rerunning `show`
  from `.local/gpu-ec2-preview` succeeded and listed all 14 create addresses. These
  failed commands changed no AWS resources.
- **Financial boundary:** preliminary estimate remains `$18.35`, below the `$25`
  ceiling but not an authorization. AWS Budgets notifications are free without
  actions, but email verification is required for alerts. No apply or quota request
  was made; AWS spend is `$0` and GPU hours are `0`.
- **Limitations:** previews omit remote locking and state bootstrap relationships,
  do not prove Scheduler or guest-timer behavior, and do not reserve capacity. The
  placeholder budget recipient is not usable. A final remote-state plan, exact price
  and tax confirmation, and expiry tests remain outstanding.
- **Next action:** finish static review, create and monitor the focused PR, then
  prepare the full cost/plan review. Request 4 vCPUs only after that is ready; do not
  apply while quota is zero.

## 2026-11-26T23:57Z — Final static checks and cloud-init template evidence

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended stacked PR #32 based on PR #30.
- **Starting state:** Terraform, scripts, and documentation were present but
  uncommitted. PRs #30 and #31 remained open. No Terraform mutation or quota request
  had been made.
- **Objective:** verify the latest cloud-init change, preserve the correct preview
  evidence, and run the complete static validation before opening the PR.
- **Commands and results:** `make gpu-ec2-validate` passed; `make terraform-validate`
  passed for bootstrap, the existing EKS root, and the GPU root; `bash -n
  scripts/gpu-ec2-*.sh` passed; `git diff --check` passed. A backend-free local copy
  rendered `cloud-init.yaml.tftpl`; Ruby YAML safe parsing succeeded using
  `YAML.safe_load(File.read(...))`. The prior `safe_load_file` method was unavailable
  in the installed Ruby and was replaced with the supported API.
- **Preview evidence:** the revised AWS-backed local-state GPU plan has SHA-256
  `a91226c5be150e1972e9351c843837c0004d54f19072684389a1c035facdef5d` and proposes
  14 creates. The bootstrap preview proposes 7 creates and has SHA-256
  `e1cd8a88e803b8cd15c1dd20fc9896aba03ffe40013d879cd6aff5928f69aaed`. The plans are
  local previews with the S3 backend removed; neither is suitable for apply.
- **Changes:** updated the validation record, ticket, and evidence manifest to
  distinguish successful static rendering/YAML parsing from unverified real-host
  cloud-init, SSM registration, and expiry behavior.
- **Cloud resources and cost:** no resources created or changed; AWS spend `$0`; GPU
  instance-hours `0`; G/VT quota remains `0` vCPUs; no quota request submitted.
- **Limitations:** no quota approval, remote-state plan, capacity guarantee, instance,
  GPU, or guest behavior has been verified. The first project bootstrap still needs
  private operator email input before its budget alert can be applied.
- **Next action:** complete the diff review and open PR #32 against the PR #30 branch;
  continue non-billable work while PR checks run. Keep quota and apply gates closed
  until exact plan, cost, and expiry controls are ready.

## 2026-11-27T00:00Z — Enforced account guard and refreshed preview

- **Phase:** Phase 2 — static-only infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, intended stacked PR #32 based on PR #30.
- **Objective:** ensure Terraform's account and AZ guards stop operations rather than
  merely warn, then produce a preview from the final source.
- **Issue found:** Terraform `check` blocks are diagnostic checks, not a sufficiently
  strong control for an account boundary or instance-launch condition.
- **Change made:** configured AWS provider `allowed_account_ids` in both the new GPU
  root and its prerequisite bootstrap root. Moved the G6 AZ-offering test into an
  `aws_instance` lifecycle precondition. The account identity remains a data source
  for the expiry-role trust policy.
- **Validation:** `make gpu-ec2-validate`, `make terraform-validate` (bootstrap,
  existing EKS root, GPU root), shell syntax checks, and `git diff --check` passed.
- **Read-only preview:** the source-updated AWS-backed local-state GPU plan proposed
  `14 to add, 0 to change, 0 to destroy`. It selected one `g6.xlarge` in `us-east-1c`
  and Canonical Ubuntu AMI `ami-0a951420c495183dc`. SHA-256 is recorded in
  `EVIDENCE_MANIFEST.md`; the plan is not remote-state-backed or apply-ready. No cloud
  resource was created or changed.
- **Cost and quota:** spend remains `$0`, GPU instance-hours `0`, G/VT quota `0` vCPUs;
  no quota request was submitted. The plan is not an authorization to spend.
- **Next action:** finish reviewing staged source and documentation, then create PR
  #32 against the PR #30 branch. Keep quota and apply gated on the exact remote plan,
  refreshed cost review, expiry proof, and the existing `$25` maximum.

## 2026-11-27T00:03Z — User-directed G/VT quota request

- **Phase:** Phase 2 — static infrastructure preparation; no paid resources.
- **Branch / PR:** `codex/gpu-ec2-foundation`, commit `8f3bb44`; PR #32 was being
  prepared against PR #30's branch.
- **Instruction:** the user asked to request quota immediately while non-billable
  engineering continued.
- **Pre-request verification:** ran the required
  `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity`; the account matched
  the expected project account. Read the `L-DB2E81BA` applied quota (0 vCPUs) and
  request history (no existing requests) before submitting. No credentials were
  recorded.
- **Action and result:** submitted an account-level request for 4 On-Demand G/VT vCPUs
  in `us-east-1`, enough for the planned single `g6.xlarge`. Request ID:
  `[request reference redacted]`. AWS accepted the request and reports
  `PENDING`; an independent `get-requested-service-quota-change` query confirmed the
  status immediately after submission.
- **Financial/security boundary:** this is a quota control-plane request, not an EC2
  launch. Applied quota remains 0, no infrastructure was created or changed, no GPU
  hours accrued, and recorded project spend remains `$0`. The `$25` ceiling and the
  exact-plan/apply approval gate remain in force.
- **Next action:** record this request in PR #32, create the focused stacked PR, and
  continue the remote plan, price, expiry, teardown, and non-billable work while AWS
  reviews the request.

## 2026-11-27T00:06Z — Phase 2 pull request opened

- **Phase:** Phase 2 — static-only infrastructure foundation.
- **Branch and commits:** `codex/gpu-ec2-foundation`; `8f3bb44` adds the root and
  safeguards; `80d0d47` records the quota request and evidence.
- **Pull request:** [#32 — guarded single-L4 EC2 foundation](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/32), opened as a draft against PR #30's `codex/single-l4-gpu-goal` branch.
- **CI state:** both repository CI workflow runs started. At the last read-only PR
  query, Python, supply-chain, and local-e2e checks were running; one manifests check
  had passed. The other manifests check was still running.
- **Quota:** the 4-vCPU request remains `PENDING`; applied quota remains zero. The
  request ID and pre-request verification are indexed above.
- **Cloud cost:** no Terraform apply or other infrastructure mutation; AWS spend
  remains `$0`, and GPU instance-hours remain `0`.
- **Next action:** allow the single PR-check watcher to reach terminal state, resolve
  any failures, and continue the remote-state/cost/expiry preparation while AWS
  processes the quota request.

## 2026-11-27 — Resolve PR #32 script review findings

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32, stacked on PR #30.
- **Starting state:** PR #32's review identified that the plan/apply parent processes
  did not inherit the profile default set by their child preflight, and that the
  teardown verifier enumerated Scheduler schedules even when their group was absent.
  AWS confirms the requested 4-vCPU quota change remains open (`CASE_OPENED`); applied
  quota is still zero. No GPU instance or infrastructure exists from this goal.
- **Changes:** plan/apply now export `AWS_PROFILE` before preflight, defaulting to
  `ai-platform-pilot-key` and preserving an explicit profile. The cleanup verifier
  now skips schedule enumeration when its group is already absent. Added subprocess
  tests with fake AWS/Terraform binaries to check profile propagation and the missing
  group path.
- **Validation:** first lint attempt found import ordering, an unused import, and a
  datetime style issue in the new test; Ruff auto-fixed these. `make verify` then
  passed Ruff, 52 tests, the dependency audit, and Compose configuration. All 52 tests
  passed with one existing Starlette deprecation warning. `bash -n` for the three
  changed scripts and `git diff --check` passed.
- **Cloud / cost:** only read the AWS caller identity and quota request history; did
  not request a duplicate, run Terraform, or create/change AWS resources. Spend and
  L4 instance-hours remain `$0` and `0` in this goal.
- **Evidence limits:** fake CLI subprocess tests prove local wrapper branching and
  environment propagation only. They do not prove actual AWS authentication,
  Scheduler behavior, infrastructure deployment, or clean teardown.
- **CI duplication observed:** publishing the same PR head created two workflow runs
  (`45928736210` and `45928742151`) because this branch's workflow still ran on both
  branch pushes and pull requests. Both have passed Python, manifest, and supply-chain
  checks; their local-e2e jobs were pending at the last check. The workflow trigger is
  now restricted to pushes to `main` plus all pull requests so future branch updates
  produce one PR workflow. These are automated fresh-runner jobs, not the project's
  final end-to-end AWS/GPU clean-room reproduction.
- **Research update:** AWS's one-time schedule documentation confirms an `at(...)`
  schedule continues to count against schedule quota after it fires, until deleted.
  The pinned AWS provider schema does not support automatic deletion after completion,
  so the runbook must require Terraform destroy to remove the schedule and must not
  claim that expiry removes it.
- **Next:** validate the workflow YAML and research note, then publish them to PR #32
  after the currently running checks reach terminal state. Observe the one subsequent
  PR-triggered workflow and update the evidence manifest.

### Follow-up outcome

- PR #32 head `528b52c` passed all four required jobs in the single PR-triggered
  workflow `45929546262`. Evidence is indexed in `EVIDENCE_MANIFEST.md`; the PR
  description has been updated. Human review remains open.
- During a read-only tag audit, direct inspection confirmed `versions.tf` configures
  provider-level `default_tags = local.required_tags`, so supported resources receive
  project/environment/owner/expiry tags even when a resource block only adds `Name`.
  AWS provider documentation confirms tags for VPCs, subnets, IAM roles, and Scheduler
  groups. No source change was needed.
- A `terraform providers schema -json` attempt from the configured S3-backend root
  stopped with “Backend initialization required.” Running `init -backend=false` and
  `-reconfigure` succeeded, but the schema command still rejected the configured
  remote-backend root. No AWS backend call, plan, or state access occurred. The
  provider-level default-tag configuration was verified from source instead.
- The AWS quota request currently reports `CASE_OPENED`; the applied quota remains
  zero. No AWS resource was created or changed, and goal-specific spend remains `$0`.
- **Next:** continue Phase 2 non-billable cost and remote-state preparation while
  preserving the exact-plan and apply authorization gates. Track the open review and
  quota request without submitting a duplicate or launching infrastructure.
- The status and backlog refresh was published as head `d3cee0f`; its one PR-triggered
  workflow `45930498661` passed Python, manifests, supply-chain, and local-e2e. The
  evidence manifest and PR description record that result. The AWS request is still
  `CASE_OPENED`; no infrastructure was launched.

## 2026-11-27 — Expand EC2 fail-closed tests and recheck account inventory

- **Phase:** Phase 2 — static-only EC2 infrastructure and non-billable validation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; code commit `7988b8f` is local
  and awaits publication with its documentation update.
- **Changes:** added fake-CLI tests that verify preflight stops on a wrong account or
  insufficient G/VT quota; apply refuses before AWS/Terraform if the operator has not
  set `GPU_EC2_CONFIRM=apply`; and a modified plan fails checksum review before cloud
  preflight. Together with earlier tests, six fail-closed cases cover the wrapper and
  cleanup paths.
- **Validation:** `make verify` passed Ruff, 56 tests, pip-audit, and Compose config.
  One existing Starlette deprecation warning remains. Bash syntax and `git diff
  --check` passed. The first lint issue was resolved earlier in this package; no new
  lint failures occurred.
- **AWS state reconciliation:** verified the caller matches the expected project
  account in `us-east-1`; the account number is omitted from this public journal.
  Exact project-tag Resource Groups and EC2 queries returned no resources
  or non-terminated GPU instance. S3 `HeadBucket` returned 404 for the expected state
  bucket; DynamoDB returned `ResourceNotFoundException` for the expected lock table;
  the exact project budget query returned no budget. This confirms the bootstrap
  guardrails are not present yet. No API mutation was made.
- **Quota and cost:** the 4-vCPU request is already open (`CASE_OPENED`); applied quota
  remains zero. No duplicate request, Terraform plan/apply, resource, GPU hour, or
  goal-specific spend was created.
- **Next:** publish code plus records to PR #32; let its single PR workflow validate
  the current head. Continue preparing the remote-state and full-cost gates without
  applying the bootstrap or GPU roots.

## 2026-11-27 — Verify destroy-plan authorization gates locally

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; teardown tests are committed at
  `ca3706b` and docs are being prepared before publication.
- **Changes:** added fake-CLI tests proving the destroy wrapper refuses missing
  explicit confirmation, altered destroy-plan bytes, and an unexpected AWS account
  before Terraform. A positive fake command test verifies the plan helper calls
  `terraform plan -destroy` and stores its output only in the test's temporary path.
- **Validation:** `make verify` passed Ruff, all 60 tests, dependency audit, and Compose
  configuration. Shell syntax checks passed for all six `gpu-ec2` helper scripts, as
  did `git diff --check`. One existing Starlette deprecation warning remains.
- **Cloud / cost:** tests replace `aws` and `terraform` in `PATH` with local stubs.
  They make no AWS API calls and cannot create or destroy resources. No GPU hours or
  goal-specific spend were added.
- **Next:** publish this test package and its evidence; observe the single PR-triggered
  CI workflow. Keep actual bootstrap and GPU changes gated by approval, quota, exact
  cost, saved plan, and expiry controls.

## 2026-11-27 — Verify baseline resource scope and cleanup output

- **Phase:** Phase 2 — static infrastructure preparation; no GPU infrastructure has
  been created by this goal.
- **Branch / PR:** `codex/gpu-ec2-foundation`, PR #32; verifier scope correction is at
  `11d2e6e`.
- **Discovery:** the verifier's generic success message said shared repository state
  and budget controls were “intentionally retained,” but live read-only checks showed
  the expected state bucket, lock table, and budget do not exist yet. The GPU verifier
  never queried them. Changed its message and test to state clearly that shared state,
  locks, and budget guardrails are outside its scope and are neither checked nor
  modified by this script.
- **AWS baseline check:** ran the read-only verifier against the expected account in
  `us-east-1`. It exited 0 and reported no non-terminated project instance, tagged
  volume/network resource, snapshot, expiry IAM role/profile, or Scheduler resource.
  This is an initial pre-provision baseline, not proof of post-destroy cleanup.
- **Partial command observation:** the first invocation returned only the first seven
  lines at the command tool's 10-second boundary and did not return its exit code. A
  process check found no verifier still running; the standalone NAT-gateway query
  returned empty successfully. Re-ran the full verifier with a longer bound and
  captured all checks and exit code `0`.
- **Validation:** after the wording change, `make lint` and `make test` passed (60
  tests, one existing Starlette deprecation warning); Bash syntax and `git diff
  --check` passed. The AWS verifier itself remains read-only.
- **State/cost:** exact project-tag inventory remains empty. Separate calls show the
  shared state bucket, DynamoDB lock table, and budget are absent, so the preflight
  correctly blocks until bootstrap resources are established. No cloud resource or
  cost was created.
- **Next:** publish the verifier correction, test, and truthful baseline record with
  the current PR package. Keep this baseline clearly distinct from future teardown
  evidence.

## 2026-11-27T00:20Z — Local vLLM streaming and cancellation package

- **Phase:** local prerequisite work for Phase 6; Phase 2 remains the active cloud
  phase. No AWS resource or GPU was used.
- **Branch / parent:** `codex/gateway-stream-accounting`, initially based on PR #32
  commit `24336cf`; it was later rebased onto PR #32 head `da2567e`.
- **Objective and changes:** close the audited vLLM streaming usage/TTFT gaps before
  live inference. The adapter requests/parses the final usage event; the gateway
  supports client `stream_options`, records measured versus estimated usage, measures
  first-content delay, and records terminal cancellation/error outcomes once.
- **Setup failures retained:** `.venv` and the ignored ONNX fixture were absent. The
  first Ruff command failed because its binary did not exist; the first test collection
  failed because the fixture was absent. Installed editable dependencies and generated
  the ignored fixture. A test initially expected bytes although this direct response
  iterator yielded strings; corrected the assertion. The first fake Redis pipeline also
  omitted a positional `hset` form and failed before its target assertion; updated the
  fake to model both forms.
- **Earlier validation snapshots:** the initial package reached 5 targeted/55 full
  tests; subsequent usage-option checks reached 7/57; the stream-failure case reached
  8/58. Each snapshot had one existing Starlette deprecation warning. These are retained
  as history; later validation is recorded below.
- **Evidence boundary:** vLLM used `httpx.MockTransport`; cancellation used the local
  in-memory limiter. No real vLLM server, Redis recovery, or GPU behavior was tested.
- **Quota/cost:** the 4-vCPU request remained pending; applied quota remained zero. No
  infrastructure mutation, GPU hours, or AWS spend occurred.

## 2026-11-27T00:25Z — PR #33 implementation committed

- **Original implementation commit:** `1186e30` (`fix: preserve vLLM stream usage and
  cancellation`), later replayed during rebase as `130bddd`.
- **PR:** #33 was opened against PR #32's `codex/gpu-ec2-foundation` branch. The PR
  branch was later rebased onto PR #32 head `da2567e` to preserve the stack.
- **Validation at that point:** Ruff passed; targeted tests reported 8 passed and the
  full suite reported 58 passed with one existing warning. Later review-fix validation
  is recorded below.

## 2026-11-27 — PR #32 latest checks and PR #33 review fixes

- **PR #32:** the single watcher reached terminal success for head `da2567e`; run
  `45933749318` passed Python, manifests, supply-chain, and local-e2e.
- **PR #33 findings:** in-band vLLM error events after HTTP 200 were silently ignored;
  string-yielding backends omitted final usage when clients requested it. Both issues
  were fixed. Error frames now fail the backend stream; estimated usage is emitted once
  when the backend has no measured usage.
- **Current validation:** targeted streaming suite **10 passed**; `make verify` passed
  Ruff, **60 tests**, pip-audit with no known vulnerabilities, and Docker Compose
  validation, with one existing Starlette/httpx warning.
- **Rebase and publication:** PR #33 was rebased on PR #32 head `da2567e`; source and
  tests are in `635f61d`. The force-with-lease push succeeded. Checks on the new PR head
  are still pending; one watcher will be used.
- **Cloud boundary:** no vLLM server, Redis, AWS mutation, or GPU was used. Goal spend
  remains `$0`; GPU hours remain `0`; quota and apply gates are unchanged.

## 2026-11-27 — NVIDIA, vLLM, and model compatibility candidate

- **Phase:** Phase 1 official research supporting Phase 3; no cloud or GPU execution.
- **Branch / PR:** `codex/gpu-software-compatibility`, prepared on the PR #32 foundation
  branch at `da2567e`; PR #37 is not yet open.
- **Starting state:** worktree clean; quota request `[request reference redacted]`
  still `CASE_OPENED`, with applied G/VT quota 0 vCPUs. PR #36's existing CI watcher
  session `5600` was live; run `45938690893` had manifests and supply-chain passed,
  Python passed, while local-e2e remained pending.
- **Objective:** replace moving dependency references with current official release
  evidence and identify a verifiable model artifact before preparing the one bounded
  GPU batch.
- **Research and commands:** checked NVIDIA's R580.196.11 release notes, driver/CUDA
  matrix, and Ubuntu installation guide; checked vLLM v0.34.0 release, L4 GPU
  requirements, and supported model table. Queried `docker buildx imagetools inspect
  vllm/vllm-openai:v0.34.0` and recorded the registry index and AMD64 digests.
  Queried Hugging Face's public model page/API using `python3` for revision, license,
  model config, tokenizer metadata, size, and LFS SHA-256. No image layers or model
  files were downloaded.
- **Minor failed command:** invoking the Python query with `python` failed because
  this host exposes `python3` only; the same read-only query then completed with
  `python3`. This changed the command only and did not affect environment state.
- **Finding:** R580.196.11 / CUDA 13.0 / vLLM 0.34.0 / Qwen2.5-1.5B is an official-doc
  candidate for Ubuntu 24.04 x86_64 and L4, but not proven on EC2. The model's
  `config.json` reports 32,768 positional embeddings while tokenizer metadata reports
  131,072 max length; use a conservative context until RoPE and runtime behavior are
  checked. The exact package repository versions and host kernel remain open.
- **Changes:** added the dated compatibility matrix and source links to
  `RESEARCH_NOTES.md`; added ticket37 with digests, model provenance, unresolved
  checks, and clear no-execution status; added the research package to the backlog.
- **Validation:** public metadata queries succeeded; no model weights, GPU image,
  container, or cloud resource was started. Diff review and documentation checks are
  pending.
- **AWS/cost:** no mutations; 0 GPU hours; no AWS resource or spend. No quota request
  was repeated.
- **Next:** validate documentation formatting, commit the focused research package,
  push its branch, open PR #37 against PR #32, and let its required checks reach a
  terminal state. Continue using the existing PR #36 watcher only.

## 2026-11-27 — Quota denial and support-path investigation

- **Phase:** Phase 2 remains static-only; GPU execution is blocked.
- **Starting state:** PR #38 head `5256060` is under its one active CI watcher. No GPU
  resources exist or were created. The existing quota request ID is recorded in the
  project ledger; do not create another request.
- **New evidence:** the owner provided an AWS email stating that the 4-vCPU On-Demand
  G/VT quota increase was denied and that the case may be reopened with a detailed use
  case. A read-only Service Quotas history query still reports `CASE_OPENED` for the
  same request; the applied quota remains `0.0`. Treat the email as the denial notice
  and the API status as inconsistent until reconciled.
- **Commands / checks:** queried Service Quotas request history and applied quota in
  `us-east-1`; checked the applied G/VT quota and `g6.xlarge` regional offering in
  `us-east-2` and `us-west-2`. All three regions report zero applied quota; G6 is
  offered in each, which does not prove AZ capacity. A read-only AWS Support
  `describe-cases` call failed with `SubscriptionRequiredException`; no support case
  or quota request was created or changed.
- **Research:** AWS states that a denied quota request should be taken to Support and
  that resolved cases can be reopened through the Support Center console. The account
  profile cannot use the Support API. Official references are in
  [`QUOTA_APPEAL_DRAFT.md`](QUOTA_APPEAL_DRAFT.md).
- **Alternatives considered:** checked two other US regions; their applied quotas are
  also zero, so switching regions alone does not solve the issue. No alternative GPU
  family is allowed by project constraints. A duplicate quota request is unsafe while
  the existing request still appears open.
- **Changes:** created a sanitized appeal draft with the single-instance use case,
  four-vCPU request, hard $25 ceiling, 8–12 hour target, private access, automatic
  expiry, and teardown safeguards. The draft has not been submitted.
- **Next action:** keep non-billable repo work moving. The owner must reopen the
  existing case from AWS Support Center if they choose to appeal; no GPU launch is
  possible until the quota is approved and the cost/apply gates pass.
- **Cost:** no AWS resources, GPU hours, or charges were created.

## 2026-11-27 — Refresh the pinned-AMI local-state preview

- **Phase:** Phase 2 — static-only EC2 infrastructure preparation; quota blocks apply.
- **Branch / PR:** `codex/refresh-gpu-ec2-preview`, preparing PR #42 on top of PR #41.
- **Starting cloud state:** verified the AWS account with the key profile. Latest
  read-only quota checks show applied On-Demand G/VT quota `0.0`; the existing
  request still says `CASE_OPENED`, despite the denial email. The attempted Support
  CLI communication was rejected before sending. No project resources exist.
- **Objective:** refresh the EC2 local-state plan after pinning the exact Ubuntu AMI
  and review its resource count and security properties without applying it.
- **Execution:** `scripts/gpu-ec2-preview-plan.sh` ran with `g6.xlarge`,
  `us-east-1c`, the reviewed Canonical Ubuntu 24.04 amd64 AMI, and an exact six-hour
  expiry. It verified caller account and AZ offering, copied the Terraform root,
  removed only the S3 backend block in that preview copy, and produced a local-state
  saved plan. Plan digest:
  `d33721981fdeaec4b513d3a738553c155423d50aa8bb7851c31ef0c5da70bd44`.
- **Plan review:** 14 creates, zero changes, zero destroys. Exactly one `g6.xlarge`;
  IMDSv2 required; root volume is 100 GiB, encrypted gp3, delete on termination;
  security group has no inbound rules and outbound TCP 80/443. A public IPv4 is
  associated so the host can use public internet egress without a NAT Gateway.
- **Plan limitations:** this local-state preview has no remote lock, does not run the
  quota preflight, cannot establish account capacity, and must not be applied. The
  raw plan remains under ignored `.local/` and was not added to Git. Terraform's
  `applyable=true` is metadata, not authorization or proof of safe applicability.
- **Troubleshooting:** an initial `terraform show -json` from the repository root
  could not load the provider schema. Running it from the initialized preview copy
  succeeded. A first filtered parser assumed object-shaped metadata and failed on
  Terraform's list-shaped JSON; correcting the parser produced the security summary.
- **Cost:** plan-only; no AWS resource, GPU hour, or spend was created. It does not
  recalculate the full project estimate.
- **Next:** submit the sanitized plan review in PR #42; continue work on shared remote
  state, current cost assumptions, expiry safeguards, and runtime preparation without
  paid GPU infrastructure.

## 2026-11-27 — Record manual appeal report and remote-lock test coverage

- **Phase:** Phase 2 — static EC2 preparation; GPU execution remains blocked.
- **Branch / PR:** `codex/test-dual-terraform-locks`, preparing PR #43 on top of PR #42.
- **Starting state:** PR #42's four required checks passed in run `45977824955`. The
  owner reports manually submitting the appeal through the existing AWS Support
  Center case. Read-only quota history remains `CASE_OPENED`, applied quota is `0.0`,
  and the connected email search has no newer reply.
- **Objective:** record the appeal status without resubmitting it and add regression
  coverage for Terraform state-lock configuration.
- **Changes:** documented the owner-reported appeal in the goal, status, research,
  appeal record, and ticket #41. Added fake-Terraform assertions that the plan and
  destroy-plan wrappers pass both S3 lockfile and DynamoDB lock arguments to `init`.
- **Validation:** focused script tests passed (14 tests), Ruff passed, and
  `git diff --check` passed. These tests prove argument wiring only; actual remote
  lock acquisition, contention, and release remain untested. The first `make verify`
  attempt could not start because this worktree had no `.venv`; using the existing
  project virtual environment then exposed absent generated CPU ONNX fixtures. After
  creating both expected local fixtures with `scripts/create_model.py`,
  `make VENV=<existing-project-virtualenv-path> verify` passed Ruff, 72 tests,
  pip-audit, and Docker Compose configuration. The model files are generated local
  fixtures and are not part of this change.
- **Cloud and cost:** read-only status only; no support message, AWS mutation, resource,
  GPU hour, or project spend was created during this work.
- **Next:** publish PR #43, then prepare a consolidated GPU execution runbook covering
  manual host setup, inference, metrics, experiments, evidence export, and teardown.
  Runtime commands remain unverified until an authorized GPU run occurs.

## 2026-11-27 — Prepare GPU batch runbook and reconcile read-only AWS state

- **Phase:** Phase 2 static preparation; planning Phase 3–10 GPU work in one batch.
- **Branch:** `codex/gpu-batch-readiness`, based on PR #43 head `4e62876`.
- **Objective:** pre-stage future GPU work and confirm the cloud is safe to wait for
  quota approval.
- **Research:** checked official NVIDIA Ubuntu driver/CUDA installation guides,
  NVIDIA Container Toolkit installation, PyTorch CUDA installation and verification,
  and vLLM GPU/Docker deployment. Recorded the headless driver path, the normal CUDA
  13/R580-or-newer vLLM driver requirement, and the need to recheck exact packages on
  the execution date.
- **AWS reads:** verified the key profile's expected account without copying its
  identifiers into evidence; applied G/VT quota remains `0.0`. Exact project-tag EC2
  and Resource Groups Tagging API queries returned no project resources. All calls
  were read-only.
- **Changes:** drafted `GPU_BATCH_RUNBOOK.md` with prerequisites, a ten-hour planning
  ceiling, manual host setup, manual vLLM first run, tenant/telemetry checks,
  benchmark/evaluation, stop conditions, evidence export, and teardown. Commands are
  labeled as planned and unexecuted.
- **Cost:** no infrastructure, GPU hour, or spend.
- **Next:** validate and publish PR #44; continue preparing scripts and datasets
  locally while quota and the Support Center response remain pending.

## 2026-11-27 — PR #44 published

- **Branch / PR / commit:** `codex/gpu-batch-readiness`, PR #44 against PR #43,
  initial head `868e11d`.
- **Checks:** CI is pending; no AWS changes or GPU hours.
- **Next:** finish recording this publication and wait for the existing PR #43 and
  #44 CI runs, then continue non-billable code readiness work.

## 2026-11-27 — PR #43 and #44 checks passed

- PR #43 head `4e62876`: run `45979618437` passed Python, manifests, supply-chain, and
  local end-to-end checks.
- PR #44 head `02247c8`: run `45980633787` passed the same four required checks.
- Both PRs remain open for human review. No AWS or GPU execution occurred.
- Continue static deployment integration in PR #45.

## 2026-11-27 — Build the opt-in single-L4 Compose runtime path

- **Phase:** static preparation for Phases 5, 6, and 11; no GPU execution.
- **Branch:** `codex/single-l4-compose-deployment`, based on PR #44 head `02247c8`.
- **Objective:** connect the existing gateway vLLM adapter to a standalone EC2 Compose
  profile while keeping the CPU ONNX path as the default.
- **Changes:** added an opt-in catalog target/model ID, single-GPU Compose profile,
  candidate image/model env file, and readiness checks for the selected backend and
  shared capacity state. The Compose file exposes only loopback gateway ports; vLLM
  and Redis are private to the Compose network. Added `make gpu-compose-config` to
  the standard verification target.
- **Validation:** `make VENV=<existing-project-virtualenv-path> verify` passed Ruff,
  76 tests (one existing Starlette deprecation warning), pip-audit with no known
  vulnerabilities, and both base/GPU Compose config checks. Nine focused tests also
  passed for catalog defaults/profile, unhealthy vLLM readiness, and the API health
  endpoint. `git diff --check` passed.
- **Cloud/cost:** no image pull, GPU allocation, AWS write, instance hour, or spend.
- **Limitations:** simulated Redis capacity remains a logical accounting mechanism.
  This profile has no DCGM exporter yet and has not run against actual GPU hardware.
- **Next:** finish full verification, publish PR #45, and continue GPU observability
  and benchmark preparation in separate packages.

## 2026-11-27 — Add safe capacity-demo CI diagnostics

- **Phase:** Phase 2 static deployment prep; no cloud or GPU execution.
- **Branch / PR / commit:** PR #45 branch `codex/single-l4-compose-deployment`,
  commit `2688d48`, pushed to PR #45.
- **Starting state:** PR #45's fixed smoke check passes. The cumulative local CPU
  `demo-capacity` demo failed in runs `45983777135` and `140460013629`; the PR #46
  workflow also failed in the same script. The scripts used bare `test` / `jq` checks,
  so CI did not identify which request or expected status failed.
- **Change:** the capacity demo now tracks its current stage and, on error, prints each
  captured HTTP status plus a restricted JSON summary of error, capacity decision, and
  usage fields. It does not print bearer tokens, prompts, generated text, or full
  response bodies.
- **Validation:** `bash -n scripts/demo-capacity.sh` passed. The script itself was
  not run locally because it calls `FLUSHDB` on the project Redis service. CI must
  establish the actual failure cause and verify that diagnostics are sufficient.
- **Cloud and cost:** none. This only changes local CPU demo diagnostics.
- **Next:** push to PR #45, run its existing CI once, inspect the new failure detail,
  and fix the underlying issue if confirmed. CI has not yet been checked for this
  head at the time of this entry; the observability branch must rebase onto this head.


## 2026-11-27 — Fix stale capacity snapshot assertion

- **Phase:** Phase 2 static deployment preparation; local E2E is CPU-only.
- **Branch / PR:** `codex/single-l4-compose-deployment`, PR #45.
- **Starting state:** CI run `45988603667` on head `65e5cba` passed smoke, then failed
  at the capacity demo's administrative snapshot check. The diagnostic reported that
  the preceding search quota request returned 429 as expected, search and payments
  requests returned 200, and the analytics CPU fallback returned 200.
- **Root cause:** the capacity API returns `mode: SIMULATED_HARDWARE_QUOTA_ACCOUNTING`
  and the pools list; the demo checked an obsolete `hardware: SIMULATED` property.
  This was a stale assertion, not a GPU failure.
- **Change:** updated the demo to compare the returned `mode` and pool slot count. The
  snapshot body/status are now stored in the temporary diagnostic directory, so a
  future failure can report the relevant fields.
- **Validation:** `bash -n scripts/demo-capacity.sh` and `git diff --check` passed. The
  demo was not run locally because it executes Redis `FLUSHDB`; a fresh GitHub Actions
  run is needed to verify the assertion and reveal any later queue-path failure.
- **Cloud and cost:** no AWS operation, GPU, model, or spend.
- **Next:** push this correction and watch its one PR #45 run. After it passes, rebase
  PR #46 and the benchmark preparation branch onto the updated PR #45 head.

## 2026-11-27 — Confirm PR #45 capacity fix in CI

- **Phase:** Phase 2 static deployment preparation; CI exercised the existing local
  CPU-only stack, not a GPU.
- **Branch / PR / commit:** `codex/single-l4-compose-deployment`, PR #45, `31348c3`.
- **Starting state:** the stale capacity mode assertion was fixed and pushed. CI run
  `45990929878` was watched once using `gh pr checks 45 --watch --interval 120`.
- **Result:** all four required checks passed: local E2E (5m11s), manifests, Python,
  and supply-chain. The capacity demo including its queue path passed in local E2E.
- **Evidence:** run `45990929878`; sanitized cause and result are recorded in
  `docs/tickets/ticket45.md`.
- **Cloud and cost:** no AWS resources, GPU runtime, model download, or spend.
- **Next:** rebase the observability branch onto `31348c3`, validate it and its CI,
  then rebase the benchmark branch onto the updated observability head.

## 2026-11-27 — Prepare static GPU observability profile

- **Phase:** Phase 7 preparation; static configuration only. Live GPU observability
  remains unvalidated until an authorized L4 execution.
- **Branch / parent:** `codex/gpu-observability-profile`, based on PR #45 head
  `bb9ad9c`; PR #46 has not yet been created.
- **Starting state:** PR #45 smoke fix was pushed. Workflow `45983777135` passed the
  smoke step but failed inside the pre-existing cumulative CPU `demo-capacity` script.
  Rerunning only the failed job (`140460013629`) failed at the same script. The log
  does not reveal which internal request/assertion failed. We did not run the script
  locally because it begins with Redis `FLUSHDB`, which would destroy local project
  state.
- **Objective:** prepare the single-GPU profile's metrics, logs/traces, alerting, and
  dashboards using current official component docs and release-pinned images, without
  starting services or incurring cloud cost.
- **Changes:** added DCGM, Node, and Redis exporters; Prometheus; Grafana; Alertmanager;
  OpenTelemetry Collector; Tempo 3; five lab warning rules; and a focused GPU/inference
  dashboard. Monitoring ports are loopback-only where published; exporters and model
  services remain internal. DCGM profiling fields and `SYS_ADMIN` are not enabled.
  The DCGM exporter and vLLM both see the same physical GPU; the reservation does not
  isolate devices. Monitoring data is ephemeral and must be exported before stopping.
- **Validation:** `make gpu-compose-config` passed without starting services.
  `make gpu-observability-validate` passed: Prometheus 3.16.0 validated the actual
  mounted scrape config and found five alert rules; Alertmanager 0.35.0 validated its
  actual mounted config; Tempo 3.1.1 verified its actual mounted config; OpenTelemetry
  Collector Contrib 0.166.0 validated the profile-specific privacy-filtering config;
  both dashboard JSON files parsed; Compose config parsed; Bash syntax and `git diff
  --check` passed. The dedicated GitHub Actions job and `make verify` target are now
  wired to rerun the same validators. System Python lacked PyYAML; the system Ruby YAML parser rejected
  valid flow endpoint lists in Compose/Prometheus, which were instead checked by their
  native parsers. Four config-validator images were downloaded into local Docker
  cache; no profile containers were started.
- **Research:** reviewed NVIDIA DCGM exporter installation, metrics fields and v4.9
  unit/name changes; vLLM current V1 metric names; Prometheus scrape configuration;
  Node Exporter setup; Tempo 3 migration; and official release manifests. The release
  digests are recorded in the PR ticket; they must be rechecked at run time.
- **Failures and troubleshooting:** first Tempo config verification exposed invalid
  compaction nesting; corrected to the schema accepted by Tempo 3.1.1. A generic YAML
  check also failed because the available Ruby parser is old and not Compose-aware.
  Initial PR #45 smoke check was corrected separately; later `demo-capacity` failure
  remains unresolved and is not attributed to GPU work.
- **Cloud and cost:** no AWS calls or resources, GPU hours, model downloads, vLLM/DCGM
  image pulls, or goal-specific AWS spend. The four local validator images occupy
  Docker cache; the profile has not run.
- **Evidence:** static files and validator outcomes are indexed in the evidence
  manifest; no screenshots or real metrics exist yet.
- **Next:** finish review of Compose security/limits, update this record, publish PR
  #46 stacked on PR #45, and diagnose the parent PR's opaque capacity-demo failure
  through non-destructive CI diagnostics.

## 2026-11-27 — Rebase observability preparation on passing deployment base

- **Phase:** Phase 7 static preparation.
- **Branch / PR:** `codex/gpu-observability-profile`, PR #46, rebased onto PR #45's
  documented passing head and the follow-up documentation commit.
- **Starting state:** PR #45 all-checks run `45990929878` passed on `31348c3`; a later
  docs-only commit `caa9b37` records the result. PR #46 was still based on the older
  PR #45 head `bb9ad9c`.
- **Action:** rebased PR #46 onto `caa9b37`. Conflicts in the persistent goal, journal,
  and PR #45 ticket were reconciled by preserving the newer PR #45 root cause/result
  and retaining the older observability work-session entry as historical context.
  Updated ticket46 to point to the actual capacity-demo fix and new CI gate.
- **Validation:** `make gpu-compose-config`, `make gpu-observability-validate`, and
  `git diff --check` passed after rebase. This validates static configs only; no
  monitoring service or GPU was started.
- **CI / cloud / cost:** new PR #46 checks are pending after the rebase. No AWS calls,
  GPU hours, model downloads, or spend.
- **Next:** publish the rebased PR #46 head and watch one check run; then rebase the
  benchmark preparation branch onto that resulting head.


## 2026-11-27 — Publish observability preparation PR

- **Phase:** Phase 7 static preparation; no live GPU evidence.
- **Branch / PR / commit:** `codex/gpu-observability-profile`, PR #46 against PR #45,
  initial head `3f26111`.
- **Starting state:** native monitoring-config validators and Compose parsing passed;
  documentation records static-only evidence and no AWS cost.
- **Action:** pushed the observability package and opened PR #46. The PR explains the
  configuration, validation, privacy controls, cost boundaries, and remaining runtime
  checks.
- **Validation:** PR workflow started after publication; final check result is pending
  and will be recorded after its single watcher reaches a terminal state.
- **Cloud and cost:** no AWS resource, GPU runtime, or model was used.
- **Next:** inspect the #46 CI result, resolve any reviewable validation issue, then
  continue non-billable deployment preparation while quota and appeal outcome remain
  unresolved.

## 2026-11-27 — Prepare direct vLLM benchmark matrix

- **Phase:** Phase 8 static preparation; no inference measurement or GPU execution.
- **Branch:** `codex/gpu-benchmark-preparation`, prepared on top of the current PR #46
  head before PR #45's current CI run completes. PR #47 is not yet open.
- **Starting state:** existing `benchmarks/load_test.py` is marked local-mock and
  launches all requests together even though it reports a concurrency field; it does
  not measure vLLM TTFT/TPOT or authenticate requests to the gateway.
- **Research:** reviewed the official vLLM 0.34.0 `bench serve` reference for the
  OpenAI chat backend, random token lengths, max concurrency, warmups, aggregate
  output, metadata labels, and TTFT/TPOT/ITL/end-to-end percentiles.
- **Changes:** added a benchmark-client Compose profile with no GPU reservation, a
  three-shape synthetic matrix, a runner that checks context bounds and one-L4
  metadata, aggregate-only output saved outside Git, and a `make gpu-benchmark-plan`
  dry-run included in `make verify`. Concurrency 16 is opt-in after lower-load memory
  checks. The direct test is documented as excluding gateway and tenant overhead.
- **Validation:** `python3.12 -m py_compile`, Ruff, `make gpu-benchmark-plan`,
  `make gpu-compose-config`, and `git diff --check` passed. Dry-run produced 11 cases
  and 33 commands; opt-in concurrency 16 produced 12 cases and 36 commands. No Docker
  profile service was started and no benchmark API request was sent.
- **Security and cost:** output is outside public Git; detailed request payload output
  is not enabled. No AWS or model resources, GPU hours, or spend were used.
- **Outstanding:** an authenticated gateway benchmark is still needed, and vLLM CLI
  flags/pins must be verified inside the exact image before the authorized batch. No
  actual performance/cost result exists.
- **Troubleshooting:** an attempt to parse `make gpu-benchmark-plan` stdout as raw JSON
  failed because Make echoes its command line; invoking the Python dry-run directly
  produced the intended JSON record. The Make target itself completed successfully.
- **Next:** finish the static review, then publish PR #47 after reconciling the
  PR #45/#46 stack.

## 2026-11-27 — Fix benchmark timeout container targeting

- **Phase:** Phase 8 static preparation; PR #47 candidate branch.
- **Branch:** `codex/gpu-benchmark-preparation`; PR #47 is not open yet.
- **Starting state:** PR #45's capacity demo fix is pushed and its CI watcher is active.
  Review of the stacked benchmark runner found a potential cleanup mismatch after the
  first benchmark repetition.
- **Finding:** Compose names each client container from workload, concurrency, and
  repetition. The timeout handler used the overall run index, so later timeouts could
  ask Docker to stop a different, nonexistent container and leave the actual client
  alive.
- **Change:** one helper now creates the container name for both `compose run --name`
  and timeout/interruption cleanup. Added a targeted regression test for repetition 3.
- **Validation:** first test attempt could not collect the test because the standalone
  pytest environment did not include the repository root on `sys.path`; the test now
  adds that root explicitly. The workstation's default Python 3.12 has no pytest, so
  `uvx --python 3.12 --from pytest pytest -q gateway/tests/test_gpu_benchmark_runner.py`
  ran the targeted test in a temporary tool environment: 1 passed. Ruff, Python 3.12
  bytecode compilation, and `git diff --check` passed. No Docker container or GPU
  benchmark was launched.
- **Cost/security:** local validation only; no AWS resources, GPU hours, or spend.
- **Next:** await PR #45's existing CI watcher, then reconcile the PR #46/#47 branch
  stack and run CI against the corrected cleanup code.

## 2026-11-27 — Rebase and revalidate benchmark preparation

- **Phase:** Phase 8 static preparation.
- **Branch / parent:** `codex/gpu-benchmark-preparation`, rebased to PR #46 head
  `6df97e7`, which includes PR #45's passing capacity-demo fix.
- **Action:** transplanted only the two benchmark-specific commits onto the updated
  observability branch. A first broad rebase attempt began replaying PR #46's commits
  and encountered documentation conflicts; it was aborted without changing the branch.
  The focused rebase using the original PR #46 base then applied the benchmark package
  cleanly apart from status documentation, which was reconciled to retain current PR
  #45/#46 facts and show the benchmark as a candidate, not an open PR.
- **Validation:** `make gpu-benchmark-plan` produced 11 cases and 33 commands within
  120 minutes; a targeted cleanup-name regression test passed (1 test); Ruff,
  `make gpu-compose-config`, and `git diff --check` passed. No Docker profile, model,
  AWS resource, or GPU request was started. The first JSON parsing attempt included
  Make's echoed command; parsing after that line succeeded, as noted in ticket47.
- **CI / cost:** PR #46 new-head run is in progress. No AWS spend or GPU hours.
- **Next:** push the updated branch and open PR #47 against PR #46, then watch its CI.

## 2026-11-27 — Correct Trivy severity input parsing

- **Phase:** Phase 11 static CI preparation; discovered while reviewing PR #46 checks.
- **Branch / PR:** `codex/gpu-benchmark-preparation`, PR #47.
- **Finding:** PR #46's workflow emitted `Unexpected input(s) 'CRITICAL'` from the
  Trivy action. The inline YAML map left the comma-separated severity value unquoted,
  so `CRITICAL` was parsed as a separate action input rather than part of `HIGH,CRITICAL`.
- **Change:** rewrote that action's `with` section as a normal mapping and quoted the
  combined severity string so both requested severities are passed as one value.
- **Validation:** pending the next PR #47 CI run; inspect the action log for the
  absence of the warning. No AWS or GPU activity.
- **Validation:** Ruby's YAML parser accepted `.github/workflows/ci.yml`; `git diff
  --check` passed. The PR #47 workflow must still confirm the Trivy action accepts the
  value without warnings.
- **Next:** push the fix and watch the resulting PR #47 run; no local clean-room rerun.

## 2026-11-27 — Confirm rebased observability and benchmark CI

- **Phase:** Phases 7/8/11, static validation only.
- **PR #46:** rebased head `6df97e7` passed all five required checks in run
  `45992409372`, including the dedicated GPU observability schema job. No monitoring
  stack or GPU was started.
- **PR #47:** head `33a1586` passed all five required checks in run `45993312156`:
  local E2E, manifests, Python, supply-chain, and GPU observability. The supply-chain
  log now passes `HIGH,CRITICAL` as a single Trivy severity input without the earlier
  malformed-input warning.
- **Evidence:** both runs are indexed in `EVIDENCE_MANIFEST.md`; ticket46/ticket47 and
  implementation status record the static-only boundary.
- **Cloud and cost:** no AWS resource, GPU hour, model download, inference benchmark,
  or goal-specific AWS spend.
- **Next:** continue static preparation for evaluation and incident exercises, then
  refresh shared status docs and PR descriptions. The single-L4 experiment still
  requires quota approval and the complete $25 cost/plan authorization gate.

## 2026-11-27 — Prepare a deterministic LLM evaluation suite

- **Phase:** Phase 9 static preparation; no model evaluation.
- **Branch:** `codex/gpu-evaluation-preparation`, based on the passing PR #47 stack.
- **Starting state:** the repository had governed ONNX model-release demos but no
  versioned evaluation suite for the planned Qwen/vLLM runtime.
- **Change:** added seven synthetic cases covering arithmetic/factual response,
  structured JSON, instruction following, subjective summarization, simple reasoning,
  technical explanation, and malformed JSON input. Added a stdlib Python evaluator,
  deterministic check helpers, a no-network dry-run, owner-only aggregate output
  outside the repository, and a required model-revision field for actual execution.
  Prompts and response text are not written to the report; a response digest and token
  counts are recorded when available. The subjective summary remains a human-review
  item and does not become an automatic pass.
- **Troubleshooting:** the first exact-number matcher rejected a correct answer ending
  with sentence punctuation. A focused test caught this; the expression now allows
  punctuation while not accepting a larger number or a decimal prefix. Ruff also
  identified one unused import, which was removed.
- **Validation:** `make gpu-evaluation-plan` reported seven cases and zero network
  requests. Four Python 3.12 tests passed; Ruff, bytecode compilation, JSON parsing,
  and `git diff --check` passed. No vLLM, model, Docker evaluation service, AWS
  resource, or GPU was used.
- **Security and cost:** optional API credentials are read only from the environment;
  reports are excluded from public Git by default. No AWS spend or GPU hours.
- **Next:** publish the evaluation-preparation PR and validate its CI. On the L4,
  confirm actual OpenAI response shape, usage fields, malformed-input status, and
  candidate report output before connecting evaluation to governed release decisions.

## 2026-11-27 — Tighten evaluation review and report safeguards

- **Phase:** Phase 9 static preparation; no request to the model.
- **Branch:** `codex/gpu-evaluation-preparation`, based on PR #47 head `9936e11`.
- **Finding and change:** an evaluation with all deterministic checks passing could
  still need a person to inspect the subjective summary. The CLI now returns exit
  code 2 for that state, so an automated release step cannot treat it as approved. A
  separate `--show-subjective-response` flag allows an operator to inspect the
  synthetic answer interactively; by default it is not printed or saved. Reports are
  created with owner-only mode from the initial file descriptor, not chmodded only
  after writing.
- **Troubleshooting:** five focused tests pass after the numeric punctuation fix. A
  shell-quoted f-string used only to summarize dry-run output failed to parse; the
  reporting command was changed to `str.format`, and the dry-run then confirmed seven
  cases and zero network requests. No evaluation behavior depended on that shell
  one-liner.
- **Validation:** targeted Python 3.12 tests: 5 passed; Ruff across repository Python
  source/test/benchmark/evaluation/script paths passed; bytecode compilation,
  `make gpu-evaluation-plan`, and `git diff --check` passed.
- **Cloud and cost:** no model, Docker evaluation service, AWS operation, GPU hour, or
  spend. PR #48 CI remains pending.

## 2026-11-27 — Open evaluation preparation PR

- **Phase:** Phase 9 static evaluation preparation.
- **Branch / PR / commit:** `codex/gpu-evaluation-preparation`, PR #48 against PR #47,
  initial head `b67d74e`.
- **Action:** opened PR #48 with the task suite, evaluator, tests, CI dry-run, README,
  ticket, and evidence/status links. The PR description states the exact local checks
  and the limitations before GPU execution.
- **Validation before publication:** `make gpu-evaluation-plan` reported seven cases
  and zero network requests; five Python 3.12 tests passed; Ruff across source,
  tests, benchmarks, evaluations, and scripts passed; bytecode, JSON/workflow parsing,
  and `git diff --check` passed.
- **Related CI:** PR #47's updated documentation head `9936e11` passed all five
  required jobs in run `45994609421`. PR #48's required checks are now pending.
- **Cloud and cost:** no LLM request, AWS resource, GPU hour, or goal-specific AWS
  spend.
- **Next:** watch PR #48's checks, fix any real failure, then continue preparing the
  CUDA lab and incident drill without claiming runtime evidence.

## 2026-11-27 — Confirm evaluation code CI and track environment-doc refresh

- **PR #48 code head:** `24b149c` passed all five required jobs in run `45996207684`,
  including Python and local E2E. CI did not contact a model or AWS.
- **Documentation follow-up:** added the exact local workstation tool inventory and
  link to `LOCAL_ENVIRONMENT_READINESS.md` in commit `5af5562`. The checks for this
  latest docs head are running in PR run `45997123263`; no result is claimed yet.
- **Cost/cloud:** no GPU or AWS operation, no model load, and no spend.

## 2026-11-27 — Record workstation tool readiness

- **Phase:** cross-phase non-billable preparation.
- **Branch:** `codex/gpu-evaluation-preparation`, PR #48.
- **Inventory:** macOS 25.6.0 arm64; AWS CLI 2.32.6; Terraform 1.14.0; Docker
  Compose v2.40.3; Python 3.12.12; GitHub CLI authenticated as Bepoadewale.
  `ansible-playbook`, `nvcc`, `nvidia-smi`, and `nvidia-container-cli` are not
  installed on this local workstation.
- **Interpretation:** local static checks, Terraform tooling, Compose rendering, and
  PR work are available. The local Mac is not the target Linux/L4 host. No CUDA or
  Ansible installation was attempted; Ansible follows manual host setup in this goal.
- **Cloud/cost:** did not inspect or print local AWS configuration and made no AWS
  request or mutation. No cost or GPU runtime.
- **Evidence:** exact tool state and its limits are recorded in
  `LOCAL_ENVIRONMENT_READINESS.md` and the evidence manifest.

## 2026-11-27 — Prepare CUDA and PyTorch performance experiments

- **Phase:** Phase 4 static preparation; no CUDA compilation or GPU execution.
- **Branch:** `codex/gpu-cuda-lab-preparation`, based on the PR #48 evaluation branch.
- **Starting state:** the local machine is macOS arm64 without `nvcc`, `nvidia-smi`, or
  an NVIDIA device. The repository had no CUDA performance lab.
- **Change:** added a bounded CUDA C++ vector-add example with L4/single-GPU guards,
  CPU correctness comparison, warmups, CUDA-event kernel timing, and separate transfer
  timings. Added a PyTorch matrix benchmark comparing CPU FP32 with L4 FP32/FP16 and
  BF16 only if supported, using synchronized CUDA-event measurements and explicit
  numerical tolerances. Added a plan-only Make target, static CI wiring, tests, and a
  learning README. Runtime measurements write aggregate JSON outside Git with owner-only
  permissions.
- **Validation:** plan reports sizes 256/512/1024, 3 warmups, 10 repetitions, and zero
  GPU operations. Three Python 3.12 tests passed; Ruff, bytecode compilation, and
  `git diff --check` passed. The `.cu` file was not compiled because the local
  workstation has no CUDA compiler.
- **Financial/security boundary:** no model, GPU, CUDA container, AWS resource, or spend.
  Runtime remains prohibited until the full $25 plan/expiry/teardown gates pass.
- **Next:** open PR #49 after updating docs, validate static CI, and later compile/run on
  the pinned Ubuntu/L4 environment before using any result in reports.

## 2026-11-27 — Confirm evaluation preparation PR checks

- **Branch / PR / head:** `codex/gpu-evaluation-preparation`, PR #48, `71637d7`.
- **Result:** all five required checks passed in run `45997259460`, including the
  local E2E workflow, Python tests and dry-run, Terraform manifests, supply-chain, and
  GPU observability schema validation.
- **Evidence limits:** CI did not contact a language model or AWS. The evaluation
  remains static; no quality score or release approval exists.
- **Cost:** no AWS resources, GPU hours, model download, or spend.

## 2026-11-27 — Open CUDA preparation PR

- **Phase:** Phase 4 static preparation; AWS/GPU execution remains blocked on quota
  and the approved cost plan.
- **Branch / PR / head:** `codex/gpu-cuda-lab-preparation`, PR #49, `ce8bbba`.
- **Starting state:** local macOS arm64; no NVIDIA device or `nvcc`. The CUDA sample
  could not be compiled locally.
- **Work:** opened PR #49 with the bounded CUDA/PyTorch lab, dry-run, tests, and
  learning documentation. Updated the goal, implementation status, backlog, ticket,
  and evidence records to reflect the opened PR.
- **CI:** run `45998860857`; at journal time Python, manifests, GPU observability,
  and supply-chain passed, while local E2E remained pending.
- **Validation limits:** CI/static checks do not establish CUDA compilation, L4
  compatibility, GPU timings, or real performance.
- **Cost/resources:** no AWS resource, GPU hour, model download, or spend.
- **Next:** finish CI observation, then prepare the manual Ubuntu/GPU setup checklist
  and consolidate required host artifacts before the authorized GPU batch.

## 2026-11-27 — Owner reports manual quota appeal submitted

- **Phase:** Phase 2 remains blocked; all work this session is non-billable.
- **Status source:** the owner reports manually submitting the appeal through the
  existing AWS Support Center case. No independent delivery receipt or new AWS
  decision has been recorded here. The prior AWS email says denied; the last recorded
  Service Quotas history still says `CASE_OPENED`, with applied quota zero.
- **Action:** updated current-state documentation to avoid asking the owner to submit
  the appeal again. No AWS case message, quota request, or infrastructure mutation was
  sent by the agent.
- **Cost/resources:** no AWS calls, GPU time, resources, or spend in this update.
- **Next:** continue preparation; check the appeal outcome and applied quota before
  any launch preflight, and do not launch with zero applied quota.

## 2026-11-27 — Prepare ordered GPU host install manifest

- **Phase:** Phase 3 static preparation; no GPU host or package install.
- **Branch:** `codex/gpu-host-install-manifest`, based on PR #49 documentation head
  `a7afcdf`.
- **Objective:** make the exact install order and the host/container split easy to
  review before the short paid execution window.
- **Work:** added `GPU_HOST_INSTALL_MANIFEST.md` covering Ubuntu, SSM, matched kernel
  headers, compute-only NVIDIA driver, Toolkit-only CUDA compiler, Docker, NVIDIA
  Container Toolkit, isolated PyTorch, pinned vLLM, Qwen artifact, gateway/Redis, and
  the local observability stack. Linked it from the documentation index and status.
- **Research boundary:** version candidates are copied from dated official-source
  research; Docker packages and standalone PyTorch still require an exact refreshed
  selection. The full matrix remains unverified on L4.
- **Validation:** documentation links, status consistency, and whitespace checks are
  to be completed before the PR is published.
- **Security/cost:** no AWS calls, infrastructure, model/image downloads, or spend.
- **Next:** finish local documentation checks, open the focused PR, and keep the GPU
  work behind quota, exact-plan, $25, runtime, expiry, and teardown gates.

- **Publication:** opened PR #50 at `1097acb`, stacked on PR #49. Required checks are
  pending. Local Markdown-link and whitespace checks passed before publication.

## 2026-11-27 — Confirm CUDA preparation PR checks

- **PR / head:** PR #49, docs follow-up head `a7afcdf`.
- **Result:** all five required jobs passed in run `45999972463`, including Python,
  manifests, supply-chain, local end-to-end, and GPU observability validation.
- **Evidence limit:** the workflow used a CPU-only runner; it did not compile CUDA,
  contact AWS, download a model, or demonstrate L4 behavior.
- **Cost:** no AWS resources, GPU hours, model or image downloads, or spend.

## 2026-11-27 — Resolve hash-locked PyTorch CUDA dependencies

- **Phase:** Phase 3 static preparation, branch `codex/gpu-host-install-manifest`.
- **Research:** queried the official PyTorch CUDA 13.0 wheel index and Docker's
  official Ubuntu 24.04 amd64 package index. Recorded the PyTorch wheel and metadata
  hashes plus candidate Docker Engine, containerd, Buildx, and Compose package
  versions/hashes in `RESEARCH_NOTES.md`.
- **Failed approaches:** the first `uv` resolution put PyPI before the PyTorch index
  and could not find `torch==2.14.0+cu130`. A direct-wheel resolution began fetching
  a 529-MiB Torch wheel; it was interrupted before installation. Cache state was not
  inspected or cleaned. The successful approach made the official PyTorch index the
  first index and used PyPI as fallback with `first-index` resolution.
- **Result:** `uv 0.9.15` resolved 29 pinned packages and SHA-256 hashes for CPython
  3.12 / x86_64 Linux into `requirements-torch.lock`. Resolver fetched a 1.2-MiB
  setuptools distribution for metadata; no package was installed in the local Python
  environment. No model or container image was downloaded.
- **Validation:** the lock includes the selected Torch wheel hash and CUDA dependency
  versions; final preflight still must refresh and review the lock.
- **Cost/resources:** no AWS calls, GPU use, or spend.
- **Next:** add the lock to the focused host-install PR, update installation steps,
  then validate the package and scripts only on an authorized Ubuntu/L4 host.

## 2026-11-27 — Document the single-L4 LLM release gap

- **Phase:** Phase 9 non-billable design; no model or GPU operation.
- **Branch:** `codex/gpu-sequential-release-design`, based on host-install PR #50.
- **Inspection:** compared `gateway/api/release.py`, the ONNX model catalog, the
  single-GPU Compose profile, and the sanitized LLM evaluation report.
- **Finding:** the existing API is tied to the ONNX stable/candidate pair and writes
  weighted Redis rollouts. The GPU profile has one vLLM endpoint and no MLflow service,
  while the evaluator does not publish its report. Reusing those ONNX canary weights
  would misrepresent two routes to the same model server as a real canary.
- **Change:** drafted a separate sequential LLM release design with a manifest,
  independent approval, stale-plan checks, vLLM restart, readiness/smoke checks, and
  verified rollback. The design explicitly records the service interruption and the
  local SQLite/artifact-store limits.
- **Validation:** source inspection only; all runtime release behavior remains
  unimplemented and unverified.
- **Cost/resources:** no AWS calls, model downloads, GPU hours, or spend.
- **Next:** publish the design as a focused PR, then implement the private MLflow and
  LLM release path with tests before the paid batch.

## 2026-11-27 — Recheck L4 runtime release and host manifest before approval

- **Phase:** Phase 2 remains blocked on quota; static preparation spans Phases 3, 5,
  and 9.
- **Branch / PR:** `codex/gpu-sequential-release-design`, PR #51 stacked on PR #50.
- **Starting state:** PR #50 head `fef4951` had passed all five required jobs in run
  `46012380712`. PR #51 head `b205929` passed all five required jobs, including the
  local end-to-end job, in run `46013204318`. No PR was merged.
- **Research:** rechecked NVIDIA Container Toolkit installation guidance, vLLM's
  current GPU installation page, the official vLLM v0.34.0 release notes and image
  publication, the Hugging Face Qwen2.5-1.5B model card, and the current OCI registry
  manifest. The vLLM documentation lists L4 support and compute capability 7.5+;
  v0.34.0 publishes CUDA 13.0, requires Hugging Face Hub 2.0+, and changes KV-cache
  sizing behavior. The image's linux/amd64 digest still matches the candidate pin.
- **Changes:** corrected the goal, status, evidence, ticket, install manifest, and
  release notes for the completed PR checks; documented the new vLLM image/runtime
  preflight; clarified that the 85% memory setting is only a conservative lab cap and
  has no measured capacity evidence. Added current release notes to the deployment
  guide. No vLLM configuration behavior changed.
- **Validation:** local links across seven edited Markdown files resolved; `git diff
  --check` passed. One local validation snippet used `python` and failed because only
  `python3` is available; rerunning with `python3` passed. The registry manifest query
  returned the same OCI index and AMD64 digest; it fetched registry metadata only.
- **Cloud and cost:** no AWS API call or mutation, package/image layer pull, model
  download, GPU execution, instance-hour, or project spend occurred. The owner reports
  that the appeal was manually sent; quota approval remains unconfirmed and no GPU
  launch is eligible.
- **Next:** publish the updated PR #51 status/research documentation, watch its new
  CI run once, then continue non-billable host automation and deployment-readiness
  review. Manual host configuration must precede any claim that Ansible is validated.

## 2026-11-27 — Restack GPU deployment PRs after gateway correctness work

- **Phase:** Non-billable integration work across Phases 5–11; Phase 2 remains blocked
  by zero applied On-Demand G/VT quota.
- **Starting state:** PRs #33–#36 held the stream accounting, request-scoped Redis
  admission leases, model-aware token reservations, and preflight cleanup fixes, but
  the GPU infrastructure chain beginning at PR #37 was based directly on PR #32 and
  omitted them. Earlier CI on PRs #33–#36 passed.
- **Changes:** changed PR #37's base to PR #36 and rebased each child branch #38–#51
  onto its immediately preceding PR. Preserved each PR as a separate review unit and
  kept its unique code, tests, tickets, and research. Shared status/journal conflicts
  were resolved by retaining the current parent records and carrying forward package-
  specific evidence entries. Updated branches #37–#50 were pushed with
  `--force-with-lease`; PR #51's final status update is being committed on the same
  branch before its updated head is pushed.
- **Validation:** GitHub PR metadata confirms the sequential base chain from #36
  through #51. PRs #33–#36 retain their passing checks. The old CI results for #37–#51
  apply to earlier branch heads only; each restacked head needs a fresh workflow run.
  No merge was performed and `main` was not modified.
- **Cloud and cost:** no AWS calls, resources, packages, image layers, model weights,
  GPU hours, or project spend were used.
- **Next:** publish the final #51 restack/status commit, then let the updated PR checks
  complete and fix any failures before describing the static stack as CI-ready.

## 2026-11-27 — Verify quota appeal status without mutation

- **Phase:** Phase 2; AWS mutation remains blocked.
- **Starting state:** the owner reported manually sending an appeal through the
  existing Support Center case. No approval had been confirmed.
- **Commands:** read-only `sts get-caller-identity`, `service-quotas get-service-quota`,
  and `list-requested-service-quota-change-history-by-quota` with profile
  `ai-platform-pilot-key`, region `us-east-1`.
- **Result:** identity matched the expected project account; applied On-Demand G/VT
  quota `L-DB2E81BA` is `0.0`; the existing 4-vCPU request still reports
  `CASE_OPENED`. The CLI does not confirm appeal delivery or approval.
- **Decision:** do not launch, submit another appeal, or create a new quota request.
- **Cost:** all queries were read-only; no resource, GPU hour, or project spend.
- **Next:** wait for AWS to update the existing request/case while continuing only
  non-billable repository work.

## 2026-11-27 — Refresh workstation and stacked PR readiness

- **Time:** 14:41 UTC.
- **Phase:** Phase 2 remains blocked on quota; static readiness work only.
- **Branch / PR:** `codex/gpu-sequential-release-design-restack`, PR #51, head
  `44c467a` at the start of this check.
- **Starting state:** PRs #32–#50 had fresh successful required checks on their
  current heads after the deployment stack was rebased to include PRs #33–#36.
  PR #51's workflow `46017455801` had four jobs pass and its local end-to-end job was
  still running. No PR was merged; `main` was untouched.
- **Workstation checks:** verified AWS CLI 2.32.6, Terraform 1.14.0, Docker Compose
  2.40.3, `uv` 0.9.15, GitHub CLI 2.101.0, and Python interpreters. `python3` resolves
  to 3.14.0; `python3.12` is separately installed at 3.12.12, and `python3.13` at
  3.13.9. Ansible, `nvcc`, `nvidia-smi`, and NVIDIA Container Toolkit CLI are absent
  from this Apple Silicon workstation. Python 3.12 is the correct explicit local
  interpreter for the repository's CPython 3.12 GPU lock; a local interpreter does
  not substitute for GPU-host validation.
- **Read-only AWS checks:** `sts get-caller-identity` with the designated key profile
  matched the expected account. `get-service-quota` returned applied G/VT quota `0.0`
  in `us-east-1`. EC2 lists `g6.xlarge` offerings in five us-east-1 Availability
  Zones; this is not capacity assurance. No AWS write, apply, GPU hour, or spend.
- **Documentation:** corrected the local readiness record and implementation status
  with the interpreter distinction and current quota/offering data. Updated the goal
  with current restacked CI status. No appeal was resubmitted; its owner-reported
  submission remains unconfirmed by AWS API status.
- **Validation:** `make gpu-ec2-validate`, `make gpu-compose-config`,
  `make gpu-benchmark-plan`, `make gpu-evaluation-plan`, and `make gpu-cuda-plan`
  passed. Dry-runs planned 33 benchmark commands with a 120-minute cap, seven
  evaluation cases with zero network requests, and CUDA operations with zero GPU
  calls. A read-only `make gpu-ec2-preflight` using the reviewed AMI and a bounded
  future expiry correctly stopped with `refusing: On-Demand G/VT quota is 0.0 vCPUs;
  4 are required`; it did not reach an apply step. `git diff --check` passed.
- **Next:** finish PR #51's one remaining CI check, update the
  evidence/status records with terminal results, and continue only non-billable work.

## 2026-11-27 — Restacked deployment CI and static readiness passed

- **Phase:** Phase 2 remains quota-blocked; no AWS mutation or GPU execution.
- **PR state:** current restacked heads PRs #32–#51 have all required checks passing.
  PR #51 workflow `46017455801` finished with all five jobs successful, including
  local end-to-end. PRs remain open and unmerged.
- **Static commands:** `make gpu-ec2-validate`, `make gpu-compose-config`,
  `make gpu-benchmark-plan`, `make gpu-evaluation-plan`, and `make gpu-cuda-plan`
  passed. Dry-runs planned 33 benchmark commands with a 120-minute cap, seven
  evaluation cases with zero network requests, and CUDA operations with zero GPU
  calls. A read-only `make gpu-ec2-preflight` correctly stopped with
  `On-Demand G/VT quota is 0.0 vCPUs; 4 are required`; it did not reach an apply step.
- **Documentation:** updated the persistent goal, status, backlog, evidence manifest,
  and workstation readiness record. The local Python default is 3.14.0; Python 3.12.12
  is installed explicitly and should be selected as `python3.12` for the repository's
  CPython 3.12 lock. The workstation has no Ansible or NVIDIA host tools, which is
  expected before access to a standard Ubuntu L4 instance.
- **AWS state:** the key profile still resolves to the expected account, applied quota
  is zero, and `g6.xlarge` appears in five availability zones. Offerings do not reserve
  capacity. The owner reports sending the existing-case appeal; AWS API status does
  not confirm a decision. No duplicate appeal or request was sent.
- **Cost/security:** no AWS write, instance, model/image download, GPU hour, or project
  spend. The `python3.14` default correction does not change the target CPython 3.12
  lock or host setup.
- **Next:** add the private MLflow and sanitized evaluation-report path in a focused
  non-billable PR; keep it off public host ports and preserve the existing ONNX release
  flow.

## 2026-11-27 — Add private MLflow evaluation evidence path

- **Phase:** Phase 9 static/local implementation; AWS quota remains zero.
- **Branch:** `codex/gpu-mlflow-evaluation-records`, based on the restacked PR #51
  head `855a52d`.
- **Starting state:** the ONNX release process is local, while the GPU Compose profile
  had no MLflow service and the LLM evaluation runner did not publish its report.
  MLflow is already an application dependency in the repository's Python image. The
  parent PR #51 documentation head `855a52d` passed all five checks in run
  `46018929290`.
- **Research:** official MLflow docs separate run metadata (backend store) from run
  files (artifact store), and describe SQLite plus proxied artifact uploads through
  `--serve-artifacts` and `--artifacts-destination`. This fits a short single-host lab;
  production durability and access controls are out of scope.
- **Changes:** added a private MLflow service with a named volume, SQLite metadata,
  local artifact destination, and loopback-only host port. Added a one-shot evaluator
  Compose profile that waits for vLLM and MLflow health. The evaluator publishes only
  suite/model provenance, aggregate metrics, policy tags, and sanitized JSON; prompts
  and completions are not sent. Added a fake-client test, ticket #52, research notes,
  runbook steps, deployment guide, and documentation index link. Existing CPU ONNX
  release services were not changed.
- **Validation:** six focused Python 3.12 tests passed; Ruff passed; bytecode compile
  passed; `make gpu-compose-config` passed; `git diff --check` passed. Earlier in this
  session, Terraform validation, benchmark/evaluation/CUDA dry-runs passed and the
  read-only AWS preflight safely rejected quota `0.0`. No containers were started.
- **Cost/security:** no image build or pull, model download, AWS write, GPU hour, or
  project spend. MLflow's UI/API binds to `127.0.0.1:15011` only; the Compose network
  has no public AWS inbound path. The named volume must be exported before authorized
  host teardown.
- **Limitations:** no live MLflow server, artifact upload, model registry release,
  L4 evaluation, release approval, or rollback was executed. SQLite and one-host
  artifacts are temporary lab storage.
- **Next:** publish as PR #52 stacked on PR #51, wait for required CI, then continue
  static work on immutable sequential LLM release-plan controls.

## 2026-11-27 — PR #52 CI passed and evaluation instructions clarified

- **Branch / PR / head:** `codex/gpu-mlflow-evaluation-records`, PR #52,
  `55f4d59`, based on PR #51.
- **CI:** all five required jobs passed in run `46020258170`: Python, manifests,
  supply-chain, GPU observability, and local end-to-end. The workflow did not start
  the L4 Compose profile or contact AWS.
- **Documentation follow-up:** clarified the exact one-shot Compose evaluation command,
  the MLflow UI's loopback/Session Manager access, and the need to export evidence
  before teardown. Updated the cost report to count model cache, Redis, and MLflow data
  against the existing encrypted 100-GiB disk; no separate AWS volume/service is added.
- **Validation boundary:** the passing run covers source at `55f4d59`; these follow-up
  Markdown edits still need to be published and receive their own check run. No code
  changed after the tested head.
- **Next:** publish the documentation follow-up, wait for its CI, then continue
  non-billable preparation for exact container dependency pins and sequential release
  plan controls. Applied GPU quota remains zero.

## 2026-11-27 — Prepare pinned gateway container build inputs

- **Phase:** Non-billable repeatability work; Phase 2 remains blocked by quota.
- **Branch:** `codex/gpu-container-build-locks`, based on PR #52 head `1f02955`.
- **Starting state:** the shared gateway image used `python:3.12-slim` and installed
  version ranges without artifact hashes. The GPU vLLM image and host packages were
  pinned separately, but gateway, evaluator, and MLflow dependencies could drift.
- **Research:** queried the Docker Official Python OCI index metadata. The
  `python:3.12-slim-bookworm` index digest is
  `sha256:44cf1793efa7c7a476bb0f2cff81443f4a072c90c1cb127e2924933daa3e8c64` and
  advertises Linux amd64/arm64, with image annotation Python 3.12.16. Registry
  metadata only was read; no layers were downloaded. Official PyPI metadata shows
  MLflow 3.18.0 as a published release with provenance.
- **Changes:** generated a universal SHA-256 lock for 124 packages from
  `requirements-container.txt`; pinned the Dockerfile base image by OCI index digest;
  switched pip install to `--require-hashes`; added a Python lock coverage validator,
  Make target, and CI calls. This applies to the existing CPU app and GPU gateway
  because they share one Dockerfile; the separately pinned vLLM image and CUDA
  learning lock are unchanged.
- **Validation:** `make container-dependencies-validate` passed and reported 124
  pinned packages with hashes; Python 3.12 bytecode compile and Ruff passed; Markdown
  link scan across 21 documents found no missing local links; `git diff --check`
  passed. `pip-audit -s osv -r requirements-container.lock` reported no known
  vulnerabilities. Docker Engine 29.0.1 and Buildx v0.29.1 are available and the
  daemon responds; the registry metadata inspect completed. The first YAML syntax
  check passed Ruby 2.6's unsupported `aliases:` keyword and failed; rerunning
  `YAML.load_file` without that newer keyword parsed the workflow successfully. CI
  repeats the lock audit and Linux image build.
- **Cost/security:** no AWS call/write, image layer download/build, model download,
  GPU hour, or project spend. The Docker metadata query supports both local arm64 and
  EC2 amd64; CI will test the actual Linux amd64 installation.
- **Limitations:** the package lock is static until the Docker build and dependency
  audit pass; it does not prove GPU-host behavior. The workstation's default Python
  remains 3.14.0; GPU and project tooling use explicit Python 3.12.
- **Next:** watch PR #53 run `46023306230` for the Linux image build, lock audit, and
  CPU end-to-end checks. Review failures before deciding on any follow-up edits.

## 2026-11-27 — Publish shared container reproducibility PR

- **Phase:** Non-billable repeatability work; Phase 2 remains blocked by quota.
- **Branch / PR:** `codex/gpu-container-build-locks`, [PR #53](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/53), stacked on PR #52.
- **Commit:** `e623b7512a750c776412c2287547981763aba592`.
- **Starting infrastructure state:** no goal-owned AWS resources; the existing G/VT quota remains zero. No cloud mutation occurred.
- **Changes:** published a Python base-image digest, universal hash lock, lock verifier, and CI checks. Updated the goal, status, backlog, ticket, and evidence records to identify the opened PR.
- **Validation:** local lock coverage and GPU Compose configuration passed; the precise lock passed `pip-audit -s osv`; PR #52 remained green. PR #53 CI run `46023306230` has five jobs in progress (Python, GPU observability, supply chain, local E2E, and manifests).
- **Cost/security:** no GPU, AWS resources, layers built locally, or cloud spend. GitHub Actions uses repository CI only; no AWS credentials or cloud actions are configured by this PR.
- **Next:** allow one watcher to monitor run `46023306230`; diagnose any failed job, then continue the next non-billable readiness package.

## 2026-11-27 — Verify container CI and reconcile MLflow install notes

- **Phase:** Non-billable repeatability work; Phase 2 remains blocked by quota.
- **Branch / PR:** `codex/gpu-container-build-locks`, PR #53.
- **Validation:** GitHub run `46023306230` completed successfully for head `e623b7512a750c776412c2287547981763aba592`. All five jobs passed. The supply-chain job built the gateway Docker image on Linux amd64, ran Trivy, and generated an SBOM. The Python job passed the hash-lock audit, lint, tests, GPU static plans, and dependency audit. The local E2E job passed `make smoke`, `make demo-flagship`, `make verify`, and `make clean-local` on the disposable CI runner.
- **Review finding:** the host installation manifest still described MLflow as absent from the GPU Compose profile, although PR #52 added a private MLflow service. Corrected the manifest to explain that it is disposable, uses the encrypted root disk, and requires evidence export before teardown.
- **Cost/security:** no AWS mutation, GPU execution, or cloud spend. GitHub CI work ran on ephemeral hosted runners.
- **Next:** validate and publish the documentation correction, then continue local implementation work on sequential LLM model release controls.

## 2026-11-27 — Restore local Python 3.12 validation environment

- **Phase:** Non-billable GPU readiness; Phase 2 remains blocked by quota.
- **Branch / PR:** `codex/gpu-container-build-locks`, PR #53 documentation follow-up.
- **Starting state:** the `.venv` directory was absent. The first `make verify` failed immediately because `.venv/bin/python` did not exist; no tests ran in that attempt.
- **Recovery:** ran the repository's `make install` using Python 3.12.12. It created `.venv`, installed the declared development dependencies, and regenerated the ignored local ONNX fixtures. No tracked model source or cloud resource changed.
- **Validation:** the subsequent `make verify` passed Ruff, 116 tests (2 skipped), dependency audit with no known vulnerabilities, and base/GPU Compose configuration. GPU observability syntax and dashboard validation passed. Benchmark, evaluation, and CUDA plans ran in dry-run mode with zero GPU operations and zero network requests. `git diff --check` passed.
- **Warning:** test startup emitted the repository's existing Starlette/httpx deprecation warning; no test failed.
- **Cost/security:** all work was local; no cloud service, GPU, or AWS resource was used.
- **Next:** publish the verified documentation correction, then implement and review sequential LLM release controls without assuming that runtime GPU behavior has been proven.

## 2026-11-27 — Prepare immutable LLM release records

- **Phase:** Phase 9 static implementation; Phase 2 remains blocked by quota.
- **Branch:** `codex/gpu-sequential-llm-release`, based on the green PR #53 documentation head.
- **Starting state:** PR #53 latest documentation head `2153942` passed all five required checks in GitHub run `46025160292`. The existing release API still applies only to the ONNX weighted canary; it cannot deploy the single vLLM target.
- **Research/design:** preserve the existing ONNX API. Bind the LLM's full model commit, artifact digest, runtime image digest/configuration, evaluation suite and report digests, source commit, and current champion into a sequential release plan. Approval state must be separate from the immutable plan digest and must come from a different actor.
- **Changes:** added local release manifest, plan, stale-input validation, and SQLite independent-approval primitives; added focused tests and updated the release design, evaluator instructions, backlog, status, index, and ticket #54. No deployment endpoint or Docker control was added.
- **Troubleshooting:** the first focused test run found two champion fixtures whose report revision did not match; corrected their fixture metadata. Ruff reported import ordering; auto-fix and rerun passed. A later test-edit initially placed the multi-GPU assertion in the wrong test scope; corrected it before acceptance. Seven focused tests now pass.
- **Security boundary:** the approval store accepts an actor string and is not itself an identity provider. It must not authorize deployment until an API obtains requester/approver identity from the existing verified role tokens and checks the actual MLflow run and model artifact.
- **Cost:** local-only code and tests; no AWS call, model download, GPU, or spend.
- **Next:** finish ticket/status records, run the complete local validation suite, then open PR #54 stacked on PR #53. Follow with authenticated approval and a safe host-side sequential deployment/rollback package.
- **Validation completion:** full `make verify` passed Ruff, 123 tests (2 skipped), and the dependency audit; GPU Compose and observability validation passed, and benchmark/evaluation/CUDA targets remained dry runs with zero model requests or GPU operations. The single-L4 CPU/GPU Compose configuration parsed successfully. No local model-serving containers were started.

## 2026-11-28 — Protect release approval state and report snapshot integrity

- **Phase:** Phase 9 static model-release preparation; PR #54.
- **Branch / starting head:** `codex/gpu-sequential-llm-release`, remote head
  `69f0b39`; its upstream evaluation/CUDA stack still needs updated heads.
- **Starting state:** review found that `save()` accepted caller-edited approval fields
  because status and approver are excluded from the immutable plan digest, and that
  manifest creation validated one report read but hashed a second read of the same path.
- **Changes:** `save()` now only accepts new plans in `PENDING_APPROVAL` with no
  approver. Manifest creation reads the report once, parses the snapshot, and computes
  its SHA-256 from those same bytes. Tests cover self-approved/mutated inserts and a
  simulated concurrent report overwrite after the snapshot read.
- **Validation:** Ruff passed; the focused release-control suite passed 8 tests;
  `git diff --check` passed. No model, MLflow service, AWS resource, or GPU was used.
- **Evidence limits:** tests prove local state and byte-snapshot checks only. They do not
  establish authenticated identity, live artifact trust, deployment, or rollback.
- **Next:** publish after restacking on the current predecessor, run PR CI, then reply
  to and resolve the two review threads with the passing evidence.

## 2026-11-27 — Prepare authenticated LLM release API

- **Phase:** Phase 9 static release integration; Phase 2 remains blocked by zero
  applied On-Demand G/VT quota.
- **Branch / PR:** `codex/gpu-llm-release-api`; PR #55 is not yet published. Base is
  PR #54 head `69f0b39`. No PR has been merged and no change was made to `main`.
- **Starting state:** PR #54's five required checks passed in run `46028053505`. The
  local Python 3.12 virtual environment exists. No project-owned AWS resource is
  known to exist, and no GPU instance has been used.
- **Objective and research:** connect the existing role checks and private MLflow
  evaluation service to immutable sequential LLM release records. Preserve the
  ONNX release route. Keep vLLM restart/deployment outside the gateway because it
  requires a separately scoped host controller.
- **Changes:** added API routes to create/read plans and independently approve them;
  validate a finished MLflow run, sanitized report, underlying model ID/revision,
  serving alias, source commit, declared artifact digest, pinned image, runtime
  configuration, suite digest, and deterministic gate; store champion/candidate
  manifests with the plan; enable SQLite write-ahead logging and migration of the
  manifest table. The GPU Compose profile mounts the same named SQLite volume into
  both gateway replicas and passes the exact serving configuration and provenance to
  the evaluator. The base gateway defaults to writable ephemeral `/tmp` storage; the
  GPU profile overrides it with persistent-for-the-host shared storage. The model ID
  is now recorded separately from the served API alias. Documentation, status, risk,
  evidence, and ticket #55 were updated.
- **Troubleshooting history:** system `ruff` was not on PATH; reran using
  `.venv/bin/ruff`. The first focused test command used only `PYTHONPATH=gateway/src`
  and failed to import the root `evaluations` namespace; Makefile and pytest paths
  now include `.`. The first model-ID mismatch test failed earlier at the missing
  model-revision comparison; the fake run fixture was corrected to reach the target
  assertion. Ruff found a duplicate `model` key in a report fixture; removed it.
  Review also identified that the original default `.local` SQLite path could not be
  created by the non-root container user; changed the default to `/tmp` and retained
  `/gpu-release` as the GPU Compose override.
- **Validation:** focused release/API/evaluation tests passed (18); full `make verify`
  passed Ruff and 128 tests (2 skipped), dependency audit with no known vulnerabilities,
  base/GPU Compose parsing, Prometheus and Alertmanager validation, dashboard parsing,
  and benchmark/evaluation/CUDA dry runs. `git diff --check` passed. The test run has
  one existing Starlette/httpx deprecation warning. Cloud and GPU actions remained
  disabled; dry runs made zero model requests and GPU operations.
- **Security and limits:** actor IDs are derived from existing role dependencies;
  self-approval is rejected by the store. MLflow report content remains sanitized.
  The API does not have Docker access. Champion manifest and model-file digest are
  still caller supplied; no independent running-state/file-byte verification exists.
  SQLite is shared by two containers only on one EC2 host, not a distributed database.
  No signed-token HTTP call to a live MLflow instance or real model artifact was tested.
- **Cost:** no AWS API mutation, model/image download, GPU hour, or project cloud
  spend. The $25 cap and zero-quota stop remain unchanged.
- **Next:** finish review, commit and publish PR #55 stacked on PR #54, wait on one
  CI watcher, resolve failures, then continue non-billable preparation on a narrowly
  scoped host-side release controller.

## 2026-11-27 — Publish PR #55 and reconcile its live state

- **Phase:** Phase 9 static LLM release integration; Phase 2 remains quota-blocked.
- **Branch / PR:** `codex/gpu-llm-release-api`, [PR #55](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/55), stacked on PR #54. Commit `f16c5194c9a7c674078e21cfb7a665c65ef33076`.
- **Starting state:** GitHub CLI authenticated as Bepoadewale. PR #54 was confirmed
  open at `69f0b392e98167cfb08f0c6fca62335655d6e41d`; no remote PR #55 branch
  existed. The worktree was clean after the code/docs commit.
- **Actions:** pushed the new branch and opened PR #55 with a detailed description of
  design, validation, failures, alternatives, security, cost, and known limitations.
  Reconciled the goal, status, backlog, ticket, and evidence manifest to show that
  PR #55 exists.
- **Validation:** commit `f16c519` contains full local verification: Ruff, 128 tests
  (2 skipped), clean dependency audit, Compose and observability parsing, GPU benchmark,
  evaluation, and CUDA dry-run checks, 13-file local Markdown-link check, and
  `git diff --check`. GitHub CI is pending; it has not been watched yet.
- **Cost/security:** no AWS mutation, GPU resource or hour, model/image download, or
  cloud spend. No credentials were copied into the repository.
- **Next:** start a single watcher for PR #55 required checks, then record the terminal
  outcome and address any failed check before selecting the next package.

## 2026-11-27 — Verify PR #55 CI

- **Phase:** Phase 9 static LLM release integration; Phase 2 remains quota-blocked.
- **Branch / PR:** `codex/gpu-llm-release-api`, PR #55, head `b94fc2781bc3ef9235507e459498703c6a41cea8`.
- **Validation:** one `gh pr checks 55 --watch --interval 120` watcher observed all five
  required checks pass in run `46033196309`: Python, manifests, GPU observability,
  supply-chain, and local end-to-end (4m55s). The PR remains open and unmerged.
- **Cost/security:** hosted CI used local CPU and static validation only; no AWS
  credentials or GPU operations are configured. No AWS resources, GPU hours, or spend.
- **Next:** record this CI result in the PR and status documents, then continue the
  non-billable host-side release-controller work as a separate PR package. Human review
  and merge remain pending; no merge is authorized by this task.

## 2026-11-27 — PR #56 updated-head checks and Ansible host preparation

- **Time / phase:** 17:42 UTC; Phase 2 remains static and quota-blocked; preparing
  Phase 3 automation without GPU execution.
- **Branch / PR:** `codex/gpu-ansible-host-configuration`, stacked on PR #56 head
  `852c873`. PR #56 passed all five checks including its one clean-room cycle in run
  `46040861818` and is ready for review. PR #57 is being prepared as a focused draft.
- **Research:** queried PyPI's JSON metadata and official NVIDIA/Docker repository
  package indexes and key files through read-only CLI requests. Recorded Ansible
  2.21.6, dated OS package versions, signing-key hashes, and remaining signature and
  compatibility checks. No APT package, model, or container image was installed or
  downloaded.
- **Changes:** added a hash-locked Ansible controller, local host playbook, Ubuntu
  24.04/amd64/one-L4 guards, signed NVIDIA/Docker repository configuration, pinned
  headless driver/CUDA/Docker/Container Toolkit packages, isolated hash-locked
  PyTorch install, reboot checkpoint, Docker runtime setup, and a small synchronized
  GPU matrix check. Added CI syntax validation, runbook instructions, research,
  ticket #57, evidence/status records, and documentation index links.
- **Commands/results:** universal Ansible lock compiled and installed with hashes in
  `/tmp/gpu-ansible-venv`; playbook syntax, task list, and a temporary local `lspci`
  assertion passed. `make install` prepared the project `.venv`; `make verify` then
  passed Ruff, 144 tests (2 skipped), audit, Compose/monitoring checks, and
  benchmark/evaluation/CUDA dry-run plans. `make gpu-ansible-validate`, relative
  Markdown-link validation, and `git diff --check` passed. Initial commands found
  macOS PEP 668 protection on system pip, a missing `.venv` in the new worktree, and
  a wrong working directory for the first Ansible invocation; each was corrected
  with an isolated venv, `make install`, or the documented working directory. No
  local clean-room command was run.
- **Cloud / cost:** no AWS request or mutation, host configuration, image/model pull,
  GPU operation, or spend. A new read-only check with the specified key profile
  confirmed the expected account and applied us-east-1 G/VT quota of `0.0` vCPUs;
  no account identifier was printed. The owner's existing appeal has no confirmed
  result in the API. The USD $25 ceiling and separate exact-plan authorization gates
  remain unchanged.
- **Next:** review the complete diff, publish PR #57 as a draft stacked on PR #56,
  then watch its single CI run. No merge or paid operation is authorized.

- 2026-11-27: Final Ansible review found that a minimal Ubuntu AMI may not contain
  `lspci`, and Ansible normally skips read-only `command` tasks in check mode. Added
  a conditional `pciutils` install before the L4 guard and explicitly enabled only
  read-only inventory/verification commands in check mode. The updated syntax check
  passed. These execution-safety changes are a material follow-up to PR #57 head
  `cd8b9a9`; its first CI run `46044432387` had passed five jobs while the local
  end-to-end job was pending. A new required CI run is needed for the updated code.

## 2026-11-28 — Fix Ansible check-mode and reboot verification gates

- **Phase:** Phase 3 static Ansible preparation; real host configuration still waits
  for quota and the approved GPU batch.
- **Branch / PR:** `codex/gpu-ansible-host-configuration`, PR #57.
- **Starting state:** review found two failures in the host role. In check mode, the
  play installed `pciutils` only as a preview but forced `lspci` to run anyway; on a
  base image without `lspci`, the preview failed. After a driver change or pending
  reboot, the GPU discovery command was correctly skipped but its assertion still
  ran against an empty result and hid the required reboot message.
- **Changes:** defer PCI inventory and its assertion when check mode cannot install
  missing `pciutils`, and print a clear message that this hardware check runs during
  normal configuration. Gate the post-reboot GPU assertion on the same condition as
  the NVIDIA command and CUDA/PyTorch verification tasks.
- **Validation:** the hash-locked Ansible 2.21.6 environment installed into the
  project `.venv`; `make gpu-ansible-validate` passed using that environment and
  `git diff --check` passed. PR checks remain to be run for the updated source. No
  host playbook or GPU task ran.
- **AWS / GPU / cost:** none; no AWS call, resource, package installation on EC2,
  GPU access, or spend.
- **Next:** include the exact changed-head syntax-check result in the ticket, publish
  the fixes, and use one PR CI run to validate the updated package.

## 2026-11-28 — Revalidate rebased PR #60 gateway benchmark

- **Phase:** Phase 8 benchmark preparation; GPU execution remains pending L4 quota and
  the bounded spend gates.
- **Branch / PR:** PR #60 (`codex/authenticated-gateway-benchmark`), rebased onto the
  current PR #58 guide head `59925fd`; implementation head at validation was `840f8c0`.
- **Starting state:** PR #60's earlier passing run applied to its former head
  `2e2d177`. New automated-review fixes had been added for truncated HTTP responses
  and P50 comparisons that included failed requests.
- **Commands / results:** focused gateway benchmark tests passed (8); focused Ruff
  passed; `make gpu-gateway-benchmark-plan` printed its bounded no-network plan;
  `git diff --check` passed.
- **Changes:** updated ticket, status, and goal records to mark the earlier CI result
  as historical and require fresh checks for the rebased code. No implementation
  changes in this validation session.
- **Cost / security:** no AWS call, resource, model download, live inference, GPU,
  credential, or spend. No local clean-room run was launched.
- **Next:** publish the documentation update on PR #60, watch its single fresh CI run,
  then rebase PR #61 and continue with the remaining pre-GPU stack.

## 2026-11-28 — Restack PR #61 interview guide

- **Phase:** Pre-GPU documentation and implementation preparation; applied GPU quota
  remains zero.
- **Branch / PR:** PR #61 (`codex/gpu-interview-preparation`) rebased onto PR #60
  head `9a8bd28` after PR #60 itself was restacked onto PR #58 head `59925fd`.
- **Starting state:** PR #61 had one documentation commit based on the old PR #60
  head `1012414`. Its earlier six-job CI run was valid only for that prior stack.
- **Changes:** retained the interview guide, added current rebase and acceptance
  history, and preserved PR #60's newer goal, status, and journal records rather than
  replacing them with stale snapshots. Refreshed the backlog and evidence manifest.
- **Validation:** confirmed the guide has 106 numbered questions across 18 topics;
  checking changed-file relative links and whitespace before publication. Fresh PR CI
  is required. No clean-room run is applicable to a documentation-only rebase.
- **Cost / security:** no AWS call, infrastructure, GPU, model download, live request,
  credentials, or spend.
- **Next:** finish structural/link checks, publish the rebased PR #61, watch one CI
  run, and proceed to PR #62.

## 2026-11-28 — Restack PR #62 benchmark and incident handbooks

- **Phase:** Phases 8 and 10 documentation preparation; GPU measurements and fault
  drills remain dependent on approved L4 capacity and the $25 spending controls.
- **Branch / PR:** PR #62 (`codex/gpu-operations-evidence-handbooks`) restacked onto
  PR #61 head `bfd3449` after PR #61 moved onto PR #60 head `9a8bd28`.
- **Starting state:** PR #62 contained one documentation commit based on PR #61's
  former head `fda6433`; inherited goal, status, backlog, journal, and #61 ticket
  updates were stale and conflicted during rebase.
- **Changes:** retained the new benchmark report and incident response handbook,
  preserved updated parent records, and refreshed the goal, backlog, evidence, status,
  and #62 ticket for this stack.
- **Validation:** the documents contain blank result slots and no invented GPU data.
  A current check passed for 75 relative Markdown links across nine changed Markdown
  files and `git diff --check`. PR #62's earlier 119-link check and CI run apply to
  the previous base; fresh CI is required.
- **Cost / security:** no AWS call, GPU, model request, credentials, or spend.
- **Next:** rerun the relative-link check, publish PR #62, and watch its fresh CI.

## 2026-11-28 — Restack PR #63 final project report draft

- **Phase:** Educational report preparation; GPU execution remains quota and budget
  gated.
- **Branch / PR:** PR #63 (`codex/gpu-final-project-report-draft`) restacked onto PR
  #62 head `90e4aca`.
- **Starting state:** PR #63 contained a documentation commit based on the former PR
  #62 head `bb7ff2f`. It adds a report draft and references prior #62 CI.
- **Changes:** retained the report and ticket, preserved current parent goal/status,
  backlog, and journal content, and updated the evidence record so old CI is clearly
  labeled as historical.
- **Validation:** on the updated files, 83 relative Markdown links resolve across
  nine files, all 28 numbered report chapters are present, and `git diff --check`
  passes. Old CI does not verify this head. The report remains a draft and must be
  updated with real measurements, screenshots, and incident evidence after approved
  GPU runs.
- **Cost / security:** no AWS operation, GPU, model download, live request, or spend.
- **Next:** validate the report links and chapter structure, publish PR #63, and
  watch the current-head CI before continuing.

## 2026-11-28 — Restack and repair PR #64 host-operation bootstrap

- **Phase:** Phase 11 non-billable host command readiness; Phase 2 remains blocked by
  zero applied L4 quota.
- **Branch / PR:** PR #64 (`codex/gpu-host-operator-automation`) restacked onto PR #63
  head `d25413f`.
- **Review finding:** the `configure` wrapper used the same `nvidia-smi` guard as
  inference. A standard Ubuntu instance has no working `nvidia-smi` before Ansible
  installs the NVIDIA driver, so this would prevent the first configuration pass.
- **Fix:** configure now validates only IMDSv2 account, instance ID, region, and
  instance type before Ansible; deployment and GPU workload operations still require
  exactly one visible L4. Added a regression test and clarified the manual guide and
  batch runbook.
- **Validation:** 20 focused host-operator tests pass; Ruff, Bash syntax, Make target
  previews, `make gpu-ansible-validate`, `make gpu-ec2-validate`, Compose validation,
  observability validation, and `git diff --check` pass. Full `make verify` first
  failed during test collection because generated ONNX fixtures were absent in this
  worktree. Created the two local ignored fixtures with `scripts/create_model.py`;
  rerun passed Ruff, 181 tests (2 skipped), dependency audit with no known
  vulnerabilities, Compose and monitoring validation, and all GPU benchmark,
  evaluation, and CUDA dry-run plans. One existing Starlette/httpx deprecation
  warning remains.
- **Parent CI:** PRs #59–#63 passed all six checks on current heads; PR #64 head
  `06f1a11` passed all six jobs in run `46114151883`. PR #65 needs fresh CI on the
  updated stack.
- **AWS / GPU / cost:** none; no AWS call, instance, model, GPU, live request, or spend.
  No separate local clean-room run was performed.
- **Next:** publish the updated PR #64 source and review docs, watch its single fresh
  CI run, and then continue with PR #65.

## 2026-11-28 — Restack and harden PR #65 Triton evidence output

- **Phase:** Phase 4 non-billable GPU performance preparation; all L4 measurements
  and profiling remain pending.
- **Branch / PR:** PR #65 (`codex/gpu-profiling-preparation`) rebased locally onto
  PR #64 head `06f1a11`.
- **Rebase history:** older PR #65 snapshots repeatedly conflicted with the latest
  goal/status/evidence records. Kept the newer parent records; package-specific detail
  remains in ticket #65 and this journal. Source and tests were carried forward.
- **Review finding:** Triton wrote every default run to one fixed JSON path using
  truncating file creation, which could overwrite prior evidence.
- **Fix:** the default path now includes a UTC microsecond timestamp. Explicit output
  paths use exclusive creation and fail safely when the file exists. Added a test that
  proves prior result contents remain unchanged; updated the manual guide.
- **Validation:** 12 focused Triton tests, Ruff, Python CLI dry-run, shell syntax, and
  whitespace checks pass. Full `make verify` passed Ruff, 193 tests (2 skipped), the
  dependency audit with no known vulnerabilities, Compose/monitoring validation, and
  all benchmark, evaluation, CUDA, and Triton dry-run plans. The first collection
  attempt lacked ignored ONNX fixtures in this worktree; created them locally and
  reran successfully. One existing Starlette/httpx deprecation warning remains.
- **Parent state:** PRs #59–#64 passed their six-job runs, including PR #64 run
  `46114151883`. PR #65 requires fresh CI after its updated base is published.
- **Cost/security:** no AWS, GPU, model download, live request, or spend. No manual
  clean-room run or project cleanup was performed.
- **Next:** wait for PR #64's current-head CI, publish PR #65 with a fresh run, and
  retain draft state until the required integrated clean-room review gate is met.

- **Documentation recheck:** 114 relative Markdown links resolve across 13 changed
  Markdown files; no unresolved rebase markers remain; `git diff --check` passes.
- **Parent CI update:** PR #64 head `06f1a11` passed all six required jobs in run
  `46114151883`, including the local CPU E2E job.


## 2026-11-28 — Record the one integrated local clean-room cycle

- **Phase:** non-GPU readiness / validation gate for the single-L4 project.
- **Evidence:** PR #65 source head `49076a5bf2c24a8122b787f2c119480d705be2a8`,
  GitHub Actions run `46114955314`, fresh Ubuntu 24.04 runner and Python 3.12.
  The `local-e2e` job and all six required workflow jobs passed.
- **Commands:** `make install`, `make bootstrap-local`, `make smoke`,
  `make demo-flagship`, `make verify`, `make clean-local`, executed in that order.
  The verification reported 193 passed, 2 skipped, one warning; the dependency audit
  reported no known vulnerabilities. The final cleanup log confirmed that only
  project Compose resources, local images, volumes, and generated artifacts were
  removed.
- **Decision:** record this as the single integrated local CPU clean-room acceptance
  run for this GPU goal. It confirms the existing local CPU path and project cleanup;
  it does not establish AWS or GPU behavior. Routine PR CI continues to exercise its
  local-e2e job, but no second manual project clean-room run was started.
- **Documentation:** exact commands, result, and limitations are now recorded in
  `docs/governance/VALIDATION.md`, ticket #65, and the evidence manifest. Fresh CI is
  required for this documentation follow-up before rechecking PR #65's P1 review gate.
- **AWS/GPU/cost:** no AWS resource, GPU, model artifact download, or project spend.


## 2026-11-28 — Restack PR #66 on the recorded clean-room evidence

- **Phase:** evidence/research reconciliation; no GPU or AWS operation.
- **PR #65:** source head `49076a5` passed six checks in `46114955314`. The
  designated local CPU clean-room cycle is now in `docs/governance/VALIDATION.md`.
  Documentation follow-up head `24ea5e8` was published and needs its own current CI.
- **PR #66:** rebased locally onto PR #65 head `24ea5e8`; current local head is
  `039619e`. Historical #66 checks do not validate the new base; it is not yet
  published. Rebase conflicts were resolved in favor of the newer parent facts and
  PR #66-specific ticket details were preserved.
- **Next:** publish #66, update its PR description, and check current CI; then restack
  PRs #67–#71 sequentially on their new immediate parents.
- **Cost/security:** no AWS query or mutation, model download, GPU operation, or spend.


## 2026-11-28 — Restack PR #67 on the clean-room evidence branch

- **Phase:** current-state documentation; no AWS/GPU execution.
- **Parent state:** PR #65 source `49076a5` has the designated local clean-room run
  recorded in governance, and PR #65 follow-up head `24ea5e8` requires fresh CI. PR
  #66 current head `2c5766e` is based on that follow-up and also requires fresh CI.
- **PR #67:** rebased on current #66 head `2c5766e`; new local head `5f1b911` is not
  yet published. Conflict resolution retained the newer parent goal/status and preserved
  the package-specific PR #67 ticket and evidence.
- **Next:** publish #67, start its normal required checks, and continue restacking #68–#71.
- **Cost/security:** no AWS query/mutation, model download, GPU operation, manual
  clean-room run, or spend.


## 2026-11-28 — Restack PR #68 after clean-room record update

- **Phase:** automation readiness documentation; no AWS/GPU execution.
- **Parents:** PR #65 governance record is published at `24ea5e8` after source head
  `49076a5` passed its designated local CPU clean-room CI in `46114955314`. PR #66
  head `2c5766e` and PR #67 head `7b9fb9f` are now published on the updated stack.
- **PR #68:** rebased on current #67 head `7b9fb9f`; local rebased head is `224b035`.
  It is not yet published or CI-validated. Ticket #68 distinguishes manual AWS
  workflow gating from paid operations and live host execution.
- **Next:** publish #68 and run current required CI, then restack #69–#71 sequentially.
- **Cost/security:** no AWS query or mutation, model download, GPU use, manual
  clean-room run, or spend.


## 2026-11-28 — Restack PR #69 on current automation-readiness parent

- **Phase:** cost estimate documentation; no new AWS Price List or infrastructure
  operation was performed in this restack.
- **PR #69:** prior head `81c09df` passed all six jobs in `46115952390`. The branch
  is now locally rebased on PR #68 head `6afa0ef`, with local head `bc0ea0e`; new CI
  is needed after publication.
- **Cost:** the corrected `$18.5193` 12-hour estimate and its limitations remain in
  the cost report. It is planning arithmetic only, not an invoice or spending approval.
- **Readiness:** the designated local CPU clean-room run is recorded at PR #65 source
  `49076a5`, run `46114955314`. Real GPU and cloud acceptance remain outstanding.
- **Next:** publish #69, update its PR body, verify its current CI, then restack #70 and
  #71 sequentially.
- **Cost/security:** no AWS mutation, GPU action, model download, manual clean-room
  run, or spend.


## 2026-11-28 — Restack PR #70 after cost refresh

- **Phase:** pinned software architecture documentation; no L4 compatibility is claimed.
- **PR #69:** prior head `81c09df` passed all six checks in run `46115952390`; current
  head `f21d61a` is published and needs fresh CI.
- **PR #70:** previous head `e5af488` passed all six checks in run `46116077981`.
  Rebased onto current #69 head `f21d61a`; local head `56bd866` is not published and
  needs its own checks.
- **Readiness:** the designated local CPU clean-room run is documented at source
  `49076a5`, run `46114955314`. Pinned candidate versions still need real L4
  verification; no model/runtime success is inferred from metadata.
- **Next:** publish #70, start current required CI, then rebase #71 on the new head.
- **Cost/security:** no AWS action, model download, GPU work, manual clean-room run,
  or spend.


## 2026-11-28 — Restack PR #71 on current architecture parent

- **Phase:** release-backlog documentation; no live host release or GPU behavior.
- **Parent:** PR #70 prior head `e5af488` passed run `46116077981`; current head
  `5f70852` is published on PR #69 head `f21d61a` and needs fresh CI.
- **PR #71:** locally rebased on #70 head `5f70852`; current local head `7e2824d` is
  not yet published. Prior #71 head `ee8d1ef` passed six checks in `46116269039`, but
  does not validate this rebase.
- **Clean-room record:** the single designated local CPU run remains PR #65 source
  `49076a5`, run `46114955314`, documented in governance. It does not prove AWS/GPU
  operation. No further manual local clean-room run occurred.
- **Next:** publish #71 and check current CI, then review the full non-GPU checklist.
- **Cost/security:** no AWS query/mutation, model download, GPU action, or spend.

## 2026-11-28 — Complete the restack checks and reconcile readiness handoff

- **Phase:** non-billable source/documentation preparation; no cloud or GPU operation.
- **PR #65:** added the one designated local CPU clean-room run to
  `docs/governance/VALIDATION.md`, answered and resolved the P1 review thread, and
  marked the PR ready for owner review. Follow-up head `24ea5e8` passed all six jobs
  in run `46117285643`.
- **Restacked PRs:** current heads #66 `2c5766e`, #67 `7b9fb9f`, #68 `6afa0ef`, #69
  `f21d61a`, #70 `5f70852`, and #71 `2aece0f` all passed their six required jobs in
  runs `46117369933`, `46117439007`, `46117499822`, `46117561667`, `46117637674`,
  and `46117785097`.
- **Readiness decision:** maintain the owner's target to complete feasible code,
  configuration, docs, local/static validation, and CI before quota approval. Quota
  approval still leaves immediate live account/quota/capacity/pricing/plan/cost/expiry
  and apply authorization gates, followed by actual L4-only work. The $25 ceiling
  remains binding; no apply is authorized by quota approval alone.
- **Backlog audit:** corrected the local Redis outage/recovery item to complete using
  the already-recorded run `46068015904`; clarified that incident drills and
  automation source are prepared while real L4 failures, host execution, expiry, and
  teardown verification remain open.
- **Review gates:** replied to and resolved the clean-room evidence findings on PRs
  #46 and #55 using the same recorded descendant-stack run; both are now ready for
  owner review. A read-only inventory found 41 open PRs and none in draft. PR #71
  head `2edf036` passed all six required checks in run `46118688165` before this
  handoff update.
- **Clean-room:** this was no additional run. The designated run remains CI run
  `46114955314`, CPU/local only, as recorded in `docs/governance/VALIDATION.md`.
- **AWS/cost/security:** no AWS call or mutation, model download, GPU hour, or spend.
- **Next:** continue resolving remaining non-GPU review/readiness gaps without merging
  PRs; reassess exact live preflight only after the quota appeal receives a decision.

## 2026-11-28 — Finish the final readiness handoff checks

- **Phase:** pre-quota non-billable documentation and review readiness.
- **PR #71:** updated the final status to show PR #46 and #55 ready after their
  evidence threads were resolved. Current PR #71 head `63df036` passed all six
  required jobs in run `46119306265`.
- **Review inventory:** the read-only open-PR inventory found 41 open PRs, no drafts,
  and no unresolved inline review threads. All PRs remain unmerged for owner review.
- **Validation boundary:** the single designated CPU clean-room run remains
  `46114955314`; routine PR local-E2E jobs are normal CI checks, not another requested
  manual project clean-room cycle. No GPU result is claimed.
- **AWS/cost:** no AWS operation, model download, GPU hour, or spend occurred. Applied
  L4 quota and the owner's existing appeal outcome remain external blockers.
- **Next:** continue any remaining source/review work that can be done without AWS;
  after quota decision, perform only the live safety preflight and authorized L4 batch.

## 2026-11-28 — Refresh the quota and project-resource preflight

- **Phase:** Phase 2 read-only account/quota gate; no mutation.
- **Identity:** `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity`
  matched the expected account. The account number is not repeated in this journal.
- **Quota:** `us-east-1` applied On-Demand G/VT quota is `0.0` vCPUs. The existing
  four-vCPU request remains `CASE_OPENED`; no new request or case was created.
- **Resources:** the exact `project=multi-tenant-ai-inference-platform` and
  `environment=gpu-ec2` tag inventory returned zero resources; the similarly scoped
  EC2 instance query returned no rows.
- **Result:** the owner-reported appeal has no approval reflected in Service Quotas.
  No launch is eligible. No AWS resource, GPU instance-hour, model download, or spend.
- **Next:** wait for the existing case outcome while continuing only non-billable
  source and review work; rerun current account/quota/price checks before any plan or
  apply after a decision.

## 2026-11-28 — Expand the educational report before GPU execution

- **Phase:** non-billable documentation readiness across project phases; L4 execution remains blocked by the quota gate.
- **Branch:** `codex/gpu-report-learning`, stacked on PR #71.
- **Pull request:** PR #72 is open for owner review. Its six CI jobs passed in run `46123579368` at head `c01fbca`, including routine PR local end-to-end CI. This is not another project-designated clean-room run.
- **Starting state:** PR #71 branch was clean at `a35c6a4`; report had all 28 chapter headings but about 2,700 words, and several foundations deferred to other docs.
- **Objective and changes:** expanded the report explanations of model/token/transformer concepts, GPU software layers, request and quota flow, vLLM KV cache, logical multi-tenancy, telemetry, and service objectives; added a concise chapter glossary; created ticket72 and linked it in `docs/README.md`.
- **Validation:** `git diff --check` passed; report is about 4,500 words. No software tests, AWS commands, GPU commands, model downloads, or instance-hour were used.
- **Evidence limits:** this records documentation only. The report remains marked PRE-GPU DRAFT. No runtime behavior, benchmark, screenshot, cost, or incident was invented.
- **Cost and resources:** no AWS mutation or spending; no project resources exist per the latest scoped read-only inventory.
- **Outstanding:** publish focused PR and review its CI; future L4-dependent chapters still need real evidence after quota approval, current cost checks, exact-plan review, and authorized batch execution.

## 2026-11-28 — Reconcile applied quota and current AWS launch gates

- **Phase:** Phase 2; read-only AWS refresh and guarded preflight. No cloud mutation.
- **Branch/PR:** `codex/gpu-applied-quota-reconcile`, PR #73 stacked on PR #72.
- **Starting state:** PR #72 was open at `ef1f5e3`; all six checks passed in run `46124118809`. Its worktree was clean. The prior project record said applied G/VT quota was zero.
- **Identity/quota:** `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity` matched the expected account. `get-service-quota` now returns `4.0` applied G/VT vCPUs; request history still reports `CASE_OPENED`. No approval notice was confirmed, and no duplicate request was made.
- **Capacity/price:** `describe-instance-type-offerings` lists `g6.xlarge` in us-east-1a, 1b, 1c, 1d, and 1f. This is not a capacity reservation. AWS Price List API returned `$0.8048/hour` for Linux shared On-Demand `g6.xlarge`, matching the current estimate.
- **Resource inventory:** exact project-tag resource count and project EC2 instance count were both zero. Exact expected state bucket and DynamoDB lock table were not found; the expected project Budget was absent. A read-only billing-alternate-contact query returned `ResourceNotFoundException`; a private primary-contact query produced no usable email. No address was recorded.
- **Guarded preflight:** `make gpu-ec2-preflight`, with the expected account, pinned Canonical AMI, offered `us-east-1c`, and a future expiry, accepted account, AMI, quota, and AZ checks, then stopped at `HeadBucket: 404 Not Found` because the project backend bucket does not exist. It did not reach plan or apply.
- **Failure/solution:** the stale zero-quota status was contradicted by current `get-service-quota`. Current docs now distinguish the applied quota value from the still-open request record and from launch authorization. Bootstrap remains gated by an invalid placeholder Budget email and the owner-authorization/exact-plan process.
- **Cost/evidence:** `$18.5193` remains a planning estimate under the `$25` cap. No AWS resource, model download, GPU hour, Terraform plan/apply, or spend occurred. No account ID, email, or credential is in the public record.
- **Next:** finish the status reconciliation PR; obtain a privately supplied, verified Budget notification address; review the exact bootstrap plan and required cloud-pilot authorization before any bootstrap apply. Then create and review the locked GPU plan before the single bounded GPU batch.

## 2026-11-28 — Build guarded backend bootstrap wrappers

- **Phase:** Phase 2 non-billable Terraform readiness; no cloud operation.
- **Branch/PR:** `codex/gpu-bootstrap-guardrails`, PR #74 based on PR #73 head
  `b50c5a9`; initial commit `1c495d1` was pushed and PR #74 opened for owner review.
- **Starting state:** the bootstrap root had seven resources and a static preview
  script, but no private saved-plan/apply/migration workflow. No matching AWS backend
  resources were recorded in the latest live inventory.
- **Objective and changes:** added private plan/apply/migrate wrappers, exact seven-
  resource plan validation, account and absence checks, digest-bound apply, Make
  targets, operator instructions, tests, and ticket74. The local state is retained
  after migration; no automatic cleanup is provided.
- **Troubleshooting:** the first focused test invocation called system `pytest`, which
  is absent. Installed the repository's documented Python 3.12 environment with
  `make install`; the existing model fixture generation completed. The first
  bootstrap preview Make target stopped immediately because the expected account
  variable was not supplied; it performed no AWS call. No preview was retried because
  the static Terraform validation is the relevant gate for this package.
- **Compatibility review:** comparison with the [HashiCorp S3 backend guide](https://developer.hashicorp.com/terraform/language/backend/s3)
  showed native S3 lockfiles require Terraform 1.10 or later. Tightened the bootstrap
  minimum from 1.8 to `>=1.10,<2.0`; bootstrap `terraform validate` passed after that
  correction. PR CI is being rerun on the corrected head.
- **Validation:** six fake-tool bootstrap tests passed. `bash -n` passed for all four
  new shell scripts. `make terraform-validate` passed for the bootstrap, existing EKS,
  and GPU roots. `make verify` passed: Ruff; 199 passed, 2 skipped; dependency audit
  found no known vulnerabilities; Compose and observability validation passed; GPU
  benchmark/evaluation/CUDA targets were dry runs. Initial `make verify` found an
  unsorted import; Ruff fixed it and verification was rerun successfully. `git diff
  --check` passed. No real AWS/Terraform plan, apply, or migration ran.
- **Security/financial boundary:** the email is represented only by a synthetic test
  address; no real recipient is stored. Fake AWS/Terraform binaries are used in tests.
  No AWS resource, model download, GPU hour, or project spend occurred.
- **Outstanding:** review the PR diff and verify final-head GitHub CI. The owner must
  provide a private valid Budget email and authorize a concrete saved plan before a future
  bootstrap apply. A separate owner-approved teardown plan is needed for versioned
  remote state resources.
- **Next:** confirm the corrected PR #74 CI result. Keep AWS read-only and do not
  repeat the designated project clean-room cycle.

## 2026-11-28 — Draft the AI infrastructure learning handbook

- **Phase:** non-billable documentation preparation across Phases 3–11; GPU execution
  remains blocked by launch authorization and unresolved budget-recipient setup.
- **Branch:** `codex/gpu-infrastructure-handbook`, stacked on PR #74 head `944b457`.
- **Starting state:** the repository had a 4,500-word pre-GPU report, 6,000-word
  manual reproduction guide, benchmark and incident reports, and interview guide, but
  did not have the separately requested AI infrastructure handbook.
- **Objective and changes:** drafted a 4,283-word handbook covering GPU/CUDA layers,
  parallel execution, transformer inference and KV cache, vLLM, performance metrics,
  tenant admission, model evaluation/release, observability, reliability, security,
  FinOps, troubleshooting, and distributed GPU concepts that are explicitly outside
  this single-L4 lab. Linked it from the main README and docs index, added ticket75 and an evidence-manifest
  entry, and restored the manifest entries to the table under their header. Corrected the
  manual guide to report the latest recorded 4.0-vCPU quota without treating it as
  confirmed appeal approval or paid-launch authorization. A live GitHub inventory
  found 45 open PRs (#30–#75 except #54); updated the backlog with successful #74
  CI and pending #75 status. The text distinguishes
  general explanations, proposed configuration, local evidence, and unexecuted L4
  requirements.
- **Validation:** a local standard-library link/heading checker found no broken
  relative targets across eight touched documentation/index files; `git diff
  --check` passed. No runtime code or software tests changed in this documentation
  package. PR #74 final head `944b457` passed all six required jobs in run
  `46128237140`; PR #75 head `a7c6ccd` passed all six required checks in run `46129784597`, including routine PR local end-to-end CI. This was not another designated project clean-room run.
- **Failure and correction:** the standard shell variable name `path` is special in
  zsh and overwrote the command search path in one temporary inventory command; the
  command failed before repository inspection. Re-ran with `file_path`; no files or
  system settings were changed.
- **Evidence boundary:** explanations are educational text, not GPU output. The
  handbook does not claim an L4 boot, GPU computation, real vLLM inference, live
  observability, benchmark, or incident result.
- **Cloud/cost/security:** no AWS calls or mutation, model/image download, GPU hour,
  or spend. No credentials or account-specific identifiers were added.
- **Next:** review the handbook for clarity, run documentation/CI checks, and publish
  the focused package as a PR stacked on #74. Continue only non-billable work until
  the private Budget recipient and exact-plan authorization gates are satisfied.

## 2026-11-28 — Add automated checks for project documentation links

- **Phase:** non-billable CI and documentation readiness.
- **Branch:** `codex/gpu-documentation-link-checks`, stacked on PR #75 head `a7c6ccd`.
- **Starting state:** PR #75 head `a7c6ccd` passed all six required checks in run
  `46129784597`. The handbook and updated guides had been checked locally, but no
  reusable repository check covered relative Markdown links and heading fragments.
- **Objective and changes:** add a Python standard-library checker, tests, a Make
  target in `make verify`, a GitHub Actions manifest check, and ticket76. Scope is
  limited to project goal/readme/GPU docs and active tickets; remote links are not
  fetched.
- **Validation:** three focused tests and Ruff passed. `make gpu-docs-validate` checked
  all 27 selected documents. `make verify` passed Ruff, 202 tests (2 skipped), dependency
  audit, Compose/observability validation, GPU dry-run plans, and the link checker.
  `make terraform-validate` passed all three roots; `git diff --check` passed. PR CI
  was pending at this intermediate point. No manual clean-room cycle or cloud/GPU action
  is part of this package.
- **Security/cost:** reads only checked-in Markdown, uses no network, and records no
  credentials or private values. No AWS resource, GPU hour, model/image download, or
  project spend occurred.
- **Final local verification:** `make verify` passed Ruff, 202 tests (2 skipped),
  dependency audit, Compose configuration, monitoring config validation, GPU
  benchmark/evaluation/CUDA dry-runs, and project documentation link checks. The
  monitoring validator pulled four digest-pinned images after the user's Docker
  cleanup; after validation, all resulting images were pruned. `make
  terraform-validate` passed for bootstrap, EKS, and GPU EC2 roots. `git diff --check`
  passed. No container was started by the validator and no cloud action occurred.
- **Pull request:** opened PR #76 stacked on #75. Final head `dba21f1` passed all six
  required CI jobs in run `46132280041`. No merge was performed.

## 2026-11-28 — Add mocked Terraform expiry safety tests

- **Phase:** Phase 2 non-billable infrastructure readiness.
- **Branch:** `codex/gpu-expiry-safeguard-tests`, based on PR #76 head `dba21f1`.
- **Starting state:** PR #76 is open; final head `dba21f1` passed all six required jobs
  in run `46132280041`. The Terraform root configures a Scheduler expiry plus a guest
  `systemd` timer, but the expiry wiring had no executable Terraform test.
- **Objective and changes:** add a Terraform `terraform test` file using the mocked
  AWS provider; test one-time UTC scheduling, exact target instance, scoped trust and
  terminate permission, guest timer rendering, root volume/IMDS settings, and invalid
  expiry input. Include the test in `make gpu-ec2-validate`, which is called by
  `make terraform-validate` and CI. Update the risk register and ticket 77 to separate
  mock configuration evidence from real runtime evidence.
- **Research:** official HashiCorp Terraform test documentation says mocking is
  supported from Terraform 1.7.0, while the repository GPU root requires Terraform
  1.10.0 or later. References are linked in ticket77:
  <https://developer.hashicorp.com/terraform/language/tests/mocking> and
  <https://developer.hashicorp.com/terraform/language/tests>.
- **Commands and outcomes:** Terraform 1.14.0 initialized the GPU root with
  `-backend=false`. The first mocked run failed because an automatically generated
  mock IAM role ARN did not satisfy AWS provider ARN validation; supplied a valid fake
  role ARN. The test then passed. After adding invalid-deadline cases and tighter
  assertions, `terraform fmt -recursive` and `terraform test -no-color` passed all
  three cases. Tests use mocked data and resources, not AWS API calls. The first
  `make verify` attempt failed before test collection because the new worktree had
  neither a `.venv` nor the ignored local ONNX fixtures. Reused the already installed
  Python 3.12 environment and generated both tiny fixtures with the documented model
  script; this was setup recovery, not another clean-room run. Then `make verify`
  passed Ruff, 202 tests (2 skipped), the dependency audit, Compose and observability
  validation, GPU dry-run plans, and Markdown link validation. `make terraform-validate`
  passed bootstrap, EKS, and GPU roots; GPU formatting, validation, and all three
  Terraform tests passed. `git diff --check` passed. The observability validator pulled
  four digest-pinned images; all local images were pruned afterward, leaving no local
  containers or images. Docker volumes and build cache were not removed.
- **Security/cost:** no cloud credentials were used, no network requests are part of
  the test, and there was no AWS resource, GPU-hour, or project spend.
- **Limitations:** static mocked configuration does not demonstrate Scheduler
  delivery, cloud-init success on the selected AMI, timer behavior after reboot, or
  EC2 termination. Those real checks remain required before paid inference work.
- **Pull request:** opened PR #77 stacked on #76 at implementation head `75f91e3`;
  all six required CI jobs passed in run `46133957636`. No merge was performed.

## 2026-11-28 — Add mocked GPU network-boundary tests

- **Phase:** Phase 2 non-billable infrastructure readiness.
- **Branch:** `codex/gpu-network-guardrail-tests`, based on PR #77 final head
  `387b91c`, which passed all six required CI jobs in run `46134599825`.
- **Objective:** add executable configuration checks for the custom security group
  and ensure the single L4 instance references only that group and its selected
  subnet.
- **Research:** current AWS EC2/VPC documentation states that security groups begin
  without inbound rules and are stateful, so response traffic for outbound requests
  is allowed without adding inbound rules. Sources are linked in ticket78.
- **Changes:** new Terraform mock test requires no ingress; exactly TCP 80 and 443
  egress to the documented IPv4 destination, with no IPv6, prefix-list, security-group,
  or self-referencing rule; one security-group attachment; and the selected subnet and
  `g6.xlarge` type. The docs state that allowed outbound ports still reach any public
  IPv4 destination and live rules remain unverified.
- **Troubleshooting:** the first test run failed because the mock generated an invalid
  Scheduler role ARN; added valid fake instance and IAM ARNs. The first egress check
  compared a provider set to a list and failed despite the printed CIDR matching; used
  a count plus membership check instead. The AWS mock also does not merge provider
  default tags into resource tags, so removed a tag assertion outside this network
  test's scope. All four Terraform tests then passed.
- **Security/cost:** mocked AWS provider only. No credentials, API calls, resource,
  GPU hour, or project spend. No live AWS validation is claimed.
- **Pull request:** opened PR #78 stacked on #77 at implementation head `5c3bd12`;
  all six required CI jobs passed in run `46135887060`. No merge was performed.

- **Validation update:** generated the standard ignored CPU ONNX fixtures in this
  worktree, then `make verify` passed Ruff, 202 tests (2 skipped), dependency audit,
  Compose/observability checks, GPU dry-run plans, and the documentation link check.
  `make terraform-validate` passed all three roots, including all four GPU mock tests;
  `git diff --check` passed. The observability validator downloaded four digest-pinned
  Docker images and all image tags were pruned afterward. The local Docker container
  and image listings are empty. This was not the designated clean-room cycle. No AWS
  resource, GPU hour, or project spend occurred.

## 2026-11-28 — Make GPU resource tags explicit and testable

- **Phase:** Phase 2 static infrastructure readiness; no AWS resource was changed.
- **Branch:** `codex/gpu-project-tag-guardrails`, based on PR #78 head `6aeb638`.
- **Objective:** make ownership, expiry, data classification, and cost scope explicit
  on taggable infrastructure, and check those values without AWS credentials.
- **Changes:** introduced one complete shared tag map and assigned it directly to each
  taggable resource in the GPU Terraform root, including the network, instance, root
  volume, IAM role/profile, and Scheduler schedule group. Added a Terraform mock test
  covering 11 resource tag maps and their required values. Added ticket79 to the
  documentation link checker and updated the goal, status, risk, backlog, environment
  README, and evidence manifest.
- **Troubleshooting:** first validation correctly rejected `tags` on
  `aws_scheduler_schedule`; the pinned AWS provider 5.100.0 schema has no such argument.
  Removed it and documented that the schedule group is tagged while the individual
  schedule remains managed by the dedicated root under its exact project name. The
  first test compared a typed provider object with a `map(string)`; Terraform reported
  the types differ. The test now compares normalized JSON values. Formatting, GPU-root
  validation, and all five mocked tests pass.
- **Documentation check:** `make gpu-docs-validate` passed for 30 files; `git diff
  --check` passed.
- **Security/cost:** test uses only AWS provider mocks. No AWS credentials/API calls,
  resources, GPU time, model download, or project spend. No live tag propagation or
  cleanup claim is made.
- **PR state:** branch is prepared on top of PR #78; PR #79 is not yet published.

## 2026-11-28 — PR #78 documentation-head end-to-end retry

- **Phase:** routine PR validation for Phase 2 static network guardrails.
- **Branch / PR:** PR #78, head `6aeb638`, stacked on #77.
- **Observed failure:** GitHub Actions run `46136477854` failed in `make demo-flagship`
  when the sandboxed-agent task POST returned HTTP 500. The response body and service
  traceback were not retained, so the root cause is unknown. The previous code head
  `5c3bd12` passed the full workflow; `6aeb638` changed documentation only.
- **Recovery evidence:** reran only the failed job for the same workflow. The sandboxed
  agent flow and all six required jobs passed in run `46136477854`. This shows the
  failure was not reproduced by the retry; it does not identify the cause.
- **Cost/scope:** GitHub-hosted CI only; no local Docker run, AWS call, GPU, or project
  spend occurred.

## 2026-11-28 — Publish explicit GPU resource tag guardrails

- **Branch / PR:** `codex/gpu-project-tag-guardrails`, PR #79, stacked on PR #78.
- **Publication:** pushed implementation commit `2e92165` and opened PR #79. GitHub
  Actions run `46137645356` passed all six required jobs, including local end-to-end.
- **Follow-up:** updated the goal, backlog, ticket, evidence manifest, and status to
  record the published PR and its passing implementation-head checks. The source code
  is unchanged; the follow-up documentation commit requires its own CI run.
- **Limits:** CI and mocked Terraform verify configuration only. No AWS resources, GPU
  execution, or spend occurred.

## 2026-11-28 — Add negative tests for GPU-root input bounds

- **Phase:** Phase 2 static infrastructure preparation; no AWS operation.
- **Branch:** `codex/gpu-input-constraint-tests`, based on PR #79 documentation head
  `efe7eed`.
- **Objective:** prove that Terraform planning rejects accelerator families, regions,
  project identifiers, disk sizes, and AMI inputs outside the authorized initial lab.
- **Changes:** added seven mocked `plan` cases for `g6.2xlarge`, `g5.xlarge`, root
  volume sizes below 100 or above 120 GiB, non-`us-east-1` region, unrelated project,
  and malformed AMI. The full GPU-root Terraform test suite now has 12 cases. Added
  ticket80 to the docs link checker, docs index, status, backlog, and evidence list.
- **Troubleshooting:** the first region case also supplied `us-west-2a`; the zone
  validation correctly failed first, causing the test to fail because it expected only
  the region validation. Kept a valid `us-east-1a` zone and changed only the region.
  The isolated region test and all other cases pass.
- **Validation:** Terraform 1.14.0 format check, validation, and all 12 mock tests pass.
  `make gpu-docs-validate` passed on 31 Markdown files, and `git diff --check` passed.
  No Docker, AWS, GPU, or spend.
- **PR state:** no PR opened yet.

## 2026-11-28 — Publish GPU Terraform input-boundary tests

- **Branch / PR:** `codex/gpu-input-constraint-tests`, PR #80, stacked on PR #79.
- **Publication:** pushed implementation and current-state records; PR #80 head
  `cf25f6d` passed all six required jobs in GitHub Actions run `46139054282`, including
  Terraform validation and local CPU end-to-end.
- **Follow-up:** the goal, status, ticket80, backlog, and evidence manifest now record
  this result. The source tests do not access AWS or assert live capacity; this
  documentation follow-up needs its own CI result.
- **Cost/scope:** GitHub-hosted CI only. No local Docker images, AWS resources, GPU
  execution, or project spend.

## 2026-11-28 — PR #79 final documentation checks passed

- **Branch / PR:** PR #79 final documentation head `efe7eed`, stacked on #78.
- **Result:** all six required GitHub Actions jobs passed in run `46138350722`,
  including local end-to-end. The goal, status, backlog, ticket79, and evidence record
  now identify this final head and its CI result.
- **Limit:** this is CI/local evidence only; no AWS, GPU, or spend occurred.

## 2026-11-28 — Prepare exact saved-plan review guard (PR #81)

- **Phase:** Phase 2 static infrastructure preparation; no AWS operation.
- **Starting state:** PR #80 was open on #79 at head `6145e25`. A live check showed
  all six required jobs passed in run `46139713692`. PR #81 did not yet exist.
- **Branch/worktree:** `codex/gpu-saved-plan-review`, based on PR #80 head `6145e25`
  in `/private/tmp/multi-tenant-ai-inference-platform-pr81`.
- **Objective:** ensure the saved plan's digest is paired with a structural review of
  its resource scope before the operator applies it, while keeping Terraform's raw
  JSON output and user data out of terminal output.
- **Changes:** added `scripts/gpu_ec2_plan_summary.py`; the plan wrapper now validates
  the plan JSON before printing its digest, and apply validates the same
  checksum-matched plan again before `terraform apply`. It checks exactly 14 expected
  managed resources with create-only actions; reviewed AMI/AZ/expiry; one `g6.xlarge`;
  encrypted bounded gp3 disk; IMDSv2 and one-hop metadata; SSM managed policy; all
  taggable resource maps; no ingress and only TCP 80/443 IPv4 egress; and exact
  one-time UTC expiry. Added fixture and fake-CLI regression tests, ticket81, docs
  index, docs-link validation, status, risk, backlog, evidence, and goal updates.
- **Errors and troubleshooting:** first wrapper integration failed because the fake
  Terraform command expected `show` at argv position zero, but the actual wrapper
  supplies `-chdir` before `show`; the fake command was changed to detect `show -json`
  anywhere in the args. A test then failed because a broadened tag check used a
  different but accurate error string; the expected assertion was corrected. One
  temporary edit put a privacy assertion in a test without a subprocess result, which
  produced `NameError`; it was moved to the relevant test. These failures and fixes
  are retained here rather than hidden.
- **Validation:** the initial implementation run passed 31 focused tests. Schema
  review then added two malformed-plan cases; the final focused run passed 33 tests.
  `make gpu-ec2-validate` passed format and configuration checks plus all 12 mocked
  Terraform tests. Ruff passed for all three changed Python files. `bash -n` passed
  for plan/apply wrappers, `make gpu-docs-validate` checked 32 Markdown files, and
  `git diff --check` passed. The tests use fixture JSON and fake AWS/Terraform
  executables.
- **Evidence limits:** tests prove the validator rejects specified fixture changes,
  that the sanitized summary omits sentinel user data, and that an unsafe instance
  type never reaches fake Terraform apply. They do not confirm live AWS provider JSON,
  remote state, quota/capacity, a real apply, or GPU behavior.
- **Resources/cost:** no Docker builds or containers, AWS calls, Terraform mutation, model/image
  downloads, GPU time, or project spend. PR #80 final CI was checked read-only; no
  duplicate watcher or status process was launched.
- **Next:** inspect the final diff, commit and publish PR #81 stacked on #80, then use
  one GitHub Actions watcher for its checks. Keep all cloud access read-only until the
  Budget recipient, exact plans, cost/expiry safeguards, and separate apply approval
  are resolved.

## 2026-11-28 — Publish saved-plan review guard

- **PR:** [#81 — validate saved GPU Terraform plans](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/81), stacked on PR #80.
- **Implementation head:** `8ff6f5fa5c648409d7ce50502b4879fe7102d896`.
- **CI:** all six required jobs passed in run `46141493735`, including the routine
  GitHub-hosted local CPU end-to-end workflow. No extra manual local clean-room run
  was started.
- **Follow-up:** updated this goal, status, backlog, evidence manifest, ticket, and
  journal to record the PR and implementation-head result. The documentation follow-up
  needs a new final-head CI run.
- **Limits and cost:** PR checks and fixture tests do not verify the actual AWS plan
  JSON or authorize infrastructure changes. No AWS call, Terraform mutation, GPU
  instance, model download, local Docker build/container, or project spend occurred.

## 2026-11-28 — Validate the scheduled expiry action (PR #82 preparation)

- **Phase:** Phase 2 static infrastructure preparation; no AWS operation.
- **Starting state:** PR #81 final head `3cb8139` passed all six required jobs in run
  `46142107889`, including the routine local CPU end-to-end workflow. PR #81 remains
  open and unmerged.
- **Branch/worktree:** `codex/gpu-plan-expiry-target-review`, based on PR #81 head
  `3cb8139` in `/private/tmp/multi-tenant-ai-inference-platform-pr82`.
- **Objective:** make the saved-plan summary verify not only when the expiry schedule
  runs, but also which action it invokes and which project schedule group owns it.
- **Changes:** require the exact project schedule name/group and EventBridge Scheduler
  AWS SDK target `ec2:TerminateInstances`; retain the one-time UTC expression, enabled
  state, and disabled flexible window. The sanitized summary now states that the
  expiry action invokes EC2 termination. Added negative fixture cases for a different
  target action and an unrelated schedule group. Added ticket82, docs index and link
  checker entry.
- **Troubleshooting:** the first edit of the validation condition omitted a boolean
  `or`; source inspection caught it before tests ran, and it was corrected.
- **Validation:** 35 focused plan-validator and fake-wrapper tests passed; Ruff passed
  for the changed Python files; `git diff --check` passed. These tests use fixture JSON
  and do not contact AWS.
- **Evidence limits:** a fixture validates expected plan fields, while the earlier
  Terraform mock test covers the configured schedule and role. Neither proves the
  live AWS provider emits these exact fields, the Scheduler fires, or an EC2 host
  terminates. Those remain real-L4 lifecycle checks.
- **Resources/cost:** no AWS calls, Terraform mutation, local Docker build/container,
  model download, GPU runtime, or project spend.
- **Next:** finish documentation/link checks, commit and publish PR #82 on top of #81,
  and watch its required CI. Keep AWS read-only until the private Budget recipient,
  exact plans, cost/expiry safeguards, and separate apply approval are resolved.

## 2026-11-28 — Publish expiry-target validation

- **PR:** [#82 — verify GPU expiry schedule target](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/82), stacked on PR #81.
- **Implementation head:** `3c50b00bb99d9badd63df0a18792f5b8a6d9dcf0`.
- **CI:** all six required jobs passed in run `46143239396`, including the routine
  GitHub-hosted local CPU end-to-end workflow. No separate manual clean-room run was
  started.
- **Follow-up:** the goal, status, backlog, ticket82, and evidence manifest now record
  the PR and implementation checks. This documentation follow-up requires its own
  final-head CI run.
- **Limits and cost:** this is static validation only; no actual Terraform plan JSON,
  EventBridge invocation, EC2 termination, AWS resource, GPU, model download, local
  Docker build/container, or project spend occurred.

## 2026-11-28 13:15 UTC — Tighten PR #84 instance public-address review

- **Phase and scope:** Phase 2 static infrastructure preparation; no cloud mutation.
- **Starting state:** PR #84 documentation head `c50b591` had passed all six required
  checks in run `46148089116`; the PR remained open. The validator checked the subnet's
  public-IP-on-launch setting but did not check the EC2 instance's own public-address
  plan value.
- **Objective and changes:** require `associate_public_ip_address=true` in the instance
  plan, add an unsafe-plan regression case, and align the fake Terraform-wrapper plan
  fixture. Update ticket84 and the persistent goal/status/evidence records.
- **Troubleshooting:** the first focused run failed one wrapper test because its
  independent fake plan fixture omitted the new field. Added the field to that
  fixture; no product defect or AWS operation was involved.
- **Validation:** final focused test run passed 44 tests; Ruff passed; the GPU docs
  link checker validated 35 files; `git diff --check` passed. The first test run's
  failure was retained in this entry.
- **Evidence limits:** these are local static and fixture tests; they do not establish
  real AWS plan JSON shape, route behavior, Systems Manager connectivity, or GPU
  execution. No CI has run on this follow-up yet.
- **Resources and cost:** no AWS API call, Terraform plan/apply, local Docker build or
  container, model download, GPU runtime, or project spend.
- **Next:** review the diff, publish the PR #84 follow-up, and watch one final-head CI
  run. Then resume the broader open-PR and non-billable readiness review.

## 2026-11-28 13:20 UTC — Reconcile the reported GPU quota approval

- **Phase and scope:** Phase 2 read-only quota verification; no AWS mutation.
- **Trigger:** the owner reported that AWS had approved the On-Demand G-series quota
  appeal and asked whether GPU work should begin before remaining non-GPU work.
- **Commands:** used `AWS_PROFILE=ai-platform-pilot-key` with `aws sts
  get-caller-identity` and `aws service-quotas list-service-quotas --service-code
  ec2 --region us-east-1`; the latter selected the quota named “Running On-Demand G
  and VT instances.”
- **Result:** expected account identity matched and applied quota `L-DB2E81BA` is
  `4.0` vCPUs. This is enough on paper for one `g6.xlarge`. Service Quotas request
  history elsewhere still reads `CASE_OPENED`; preserve that stale status alongside
  the owner report and applied value. The quota does not reserve AZ capacity.
- **Decision:** finish the non-GPU safety gates before any paid GPU run. The private
  Budget notification recipient, remote-state bootstrap, exact locked GPU plan,
  refreshed full-cost/expiry/teardown review, and separate apply authorization remain.
  Prepare GPU-dependent operations as one bounded batch after those gates.
- **Evidence limits and cost:** the CLI proves only the account context and applied
  quota value. It does not prove live capacity, a remote-state plan, an instance, or
  GPU access. Queries were read-only; no AWS resources or spend.

## 2026-11-28 13:26 UTC — Verify PR #84 follow-up CI and update readiness state

- **Phase and scope:** Phase 2 static plan validation and non-billable readiness.
- **PR/CI:** PR #84 commit `8349510` passed all six required jobs in GitHub Actions
  run `46148953601`, including local E2E. The run also validates the updated plan
  fixtures and instance-level public-IP assertion.
- **Documentation:** updated the goal, implementation status, cost report, ticket84,
  and evidence manifest to record the CLI-confirmed 4.0-vCPU applied quota and the
  owner's report of approval. The case-history API's `CASE_OPENED` value is retained
  as stale/inconsistent history, not treated as proof that the applied quota is zero.
- **Readiness decision:** quota capacity is now sufficient on paper for a single
  `g6.xlarge`, but finish non-GPU safety gates before GPU execution: obtain a private
  Budget notification recipient, create/review the remote-state backend plan, refresh
  exact costs/capacity/expiry/teardown, and require separate apply authorization.
- **Validation and cost:** six PR checks passed on code head `8349510`; documentation
  links, Ruff, the focused 44 tests, and diff checks passed before that run. The new
  documentation update then passed all six required checks on head `355deba` in run
  `46149649470`. No Terraform plan/apply, AWS mutation, GPU time, or spend occurred.

## 2026-11-28 13:42 UTC — Reconcile the open PR review and mergeability queue

- **Phase and scope:** PR-only workflow review; no branch or AWS mutation.
- **GitHub snapshot:** 54 PRs are open (#30–#84 except #54); none has an approving
  review decision. The live GraphQL mergeability result shows PR #39 and PR #50 as
  conflicting, while the other 52 are clean/mergeable. PR #84 head `2bad950` passed
  all six required checks in run `46150315317`.
- **Impact:** passing checks do not replace human review. The two conflicts and lack
  of approvals mean the open PR stack is not ready to close; do not claim all PR/CI
  review is complete. Resolve each branch against its intended base and revalidate
  affected descendants before any merge.
- **Decision:** keep the AWS account read-only. Continue the non-GPU review and safety
  gates; do not let quota approval alone trigger GPU launch.
- **Evidence limits and cost:** mergeability and review-decision data are a point-in-
  time GitHub snapshot. No AWS mutation, Terraform operation, GPU hour, or spend.
