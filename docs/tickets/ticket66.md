# Ticket 66 — reconcile readiness and evidence facts

## Objective

Make the current source-of-truth documents agree with verified model metadata,
AWS quota status, GitHub checks, and public evidence redaction. Clarify the readiness
target: complete all feasible non-GPU work and launch controls before the authorized
L4 batch, so the remaining engineering is predominantly real GPU execution and
validation.

## Current state

- PR #65 remains open. Source head `49076a5` passed all six required jobs in run
  `46114955314`, including the designated local CPU clean-room cycle. Its evidence
  record is in the refreshed PR #65 stack; current head `37b3b30` needs fresh CI.
  PR #66 is being restacked onto that current head and needs CI after publication.
- PR #50 remains open; its historical checks passed on the recorded head in run
  `46016503614`.
- The latest read-only AWS CLI check on 2026-11-28 confirms 4.0 applied On-Demand
  G/VT vCPUs in `us-east-1` and history status `CASE_CLOSED`. This allows one
  `g6.xlarge` by quota but does not reserve Availability Zone capacity or authorize
  provisioning. The project state bucket, lock table, and Budget are absent; the
  recipient is not verified. No AWS mutation was made.
- The immutable Qwen metadata and weight digest were already recorded in the research
  matrix, but two older paragraphs still described them as unpinned. No weight file
  has been downloaded.
- One untracked root `uv.lock` belongs to the user and is not part of this ticket.

## Research and design

- Use the existing immutable Hub revision and artifact digest in the earlier research
  matrix; state clearly that metadata inspection is not weight download or runtime
  verification.
- Preserve historical journal events, including earlier quota request statuses, while
  removing unnecessary AWS request identifiers from public documentation.
- Separate AWS's denial email, owner-reported appeal, current API status, and applied
  quota. Do not infer appeal acceptance from `CASE_OPENED`.
- State that quota approval leaves live plan, cost, apply authorization, execution,
  and teardown safeguards in force.

## Implementation tasks

- [x] Correct stale Qwen revision and quota language in research notes and audit.
- [x] Update the current state in the cost report and PR #50 ticket from live CLI
  verification.
- [x] Remove the AWS account number and request reference from public documentation.
- [x] Record the pre-quota readiness target in the persistent goal and status.
- [x] Correct model metadata and quota facts while keeping historical events intact.
- [x] Record commands and evidence in the journal and manifest.
- [x] Update the documentation index, cost report, audit, research notes, and ticket #50.
- [x] Rebase PR #66 onto updated PR #65 head `24ea5e8`.
- [ ] Push rebased PR #66 and pass its current required CI.
- [ ] Obtain human review; do not merge without owner authorization.

## Validation

Read-only commands used:

```bash
gh pr view 50 --json number,state,isDraft,headRefOid,statusCheckRollup
gh pr view 65 --json number,state,isDraft,headRefName,headRefOid,statusCheckRollup
AWS_PROFILE=ai-platform-pilot-key aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-DB2E81BA --region us-east-1
AWS_PROFILE=ai-platform-pilot-key aws service-quotas \
  list-requested-service-quota-change-history-by-quota \
  --service-code ec2 --quota-code L-DB2E81BA --region us-east-1
```

Historical quota queries in the earlier PR #66 run returned zero applied quota and
`CASE_OPENED`. A new read-only check on 2026-11-28 confirms 4.0 applied vCPUs and
`CASE_CLOSED`. PR #50 and #65 had successful required checks on recorded historical
heads. On implementation commit `637eb7d`, all six PR #66 checks passed in run
`46092847166`, including the workflow's local E2E cycle. `git diff --check` passed. A
local scan excluding the virtual environment checked 111 Markdown files and 200
relative file targets; none was missing. The current rebased PR #66 head needs fresh
CI. No separate manual clean-room cycle is planned.

## Security and financial considerations

Only read-only GitHub and AWS queries were used. No credentials, account numbers,
AWS request identifiers, private artifacts, or model weights are intentionally added.
No AWS mutation, GPU operation, model download, or spend occurred. The $25 ceiling,
quota gate, exact-plan review, expiry safeguards, and explicit apply authorization
remain in force. The $25 ceiling is a hard project limit, not an automatic apply
approval.

## Evidence and outstanding work

The execution journal records the checks made on 2026-11-28; the evidence manifest
records their limits. The current rebased PR head must pass CI before review. The one selected local CPU clean-room acceptance record is in `docs/governance/VALIDATION.md` (source head `49076a5`, run `46114955314`); it does not establish GPU or AWS behavior. The GPU-dependent
acceptance criteria remain incomplete until performed on a real L4. The quota appeal
outcome remains an external dependency.
