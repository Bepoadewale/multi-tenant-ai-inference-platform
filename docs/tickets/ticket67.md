# Ticket 67 — reconcile live PR and backlog status

## Objective

Make the durable implementation backlog distinguish current GitHub state from older
per-package notes. Record PR #66's final check result and keep the pre-quota readiness
target clear.

## Current state

- PR #66 prior head `094576e` passed all six required jobs in run `46093702808`. Its current rebased head `12cc2eb` is on the updated PR #65 stack; fresh CI run `46115502844` is in progress.
- One read-only CLI snapshot on 2026-11-28 found 37 open PRs, #30–#66. Every PR was
  non-draft and all displayed check runs were completed successfully. The snapshot
  does not show review approval, merge permission, or merged code.
- The guarded GPU plan wrapper runs the strict preflight before Terraform initializes
  the remote backend. The preflight requires four On-Demand G/VT vCPUs; the latest
  applied quota is zero. The remote-state plan is therefore not available through the
  guarded command until quota changes. Do not bypass that safety check.
- The exact-name AWS inventory recorded on 2026-11-26 found the planned shared S3
  state bucket, DynamoDB lock table, and budget absent. The bootstrap preview has
  seven creates and an invalid placeholder email. After quota changes, the remote plan
  still requires separately authorized bootstrap resources and a verified budget
  recipient. Do not treat quota approval as authorization to create them.
- A separate workflow run `46093697237` appeared on the branch push for the
  manually-dispatched AWS OIDC workflow. GitHub reported zero jobs and no logs. The
  workflow file requires a manual dispatch and explicit inputs; no AWS step ran. The
  reason for the empty push event is unknown and does not affect the required PR CI.
- The untracked root `uv.lock` belongs to the user and remains untouched.
- PR #67 current rebased head has not yet been published; its historical CI runs apply only to the original pre-restack commits and do not validate this new base.

## Research and design

- Use the PR list snapshot only as an observation at its capture time. Human review
  and merge authority remain separate facts.
- Keep detailed package notes for historical context, but direct readers to live GitHub
  for current PR heads, checks, reviews, and merge state.
- Keep Terraform preflight guards intact. Quota approval can enable a reviewed plan;
  it does not authorize an apply or GPU spend.
- The shared state/budget bootstrap remains an AWS mutation with its own review and
  authorization gate. Keep this distinct from the quota gate.
- Treat the zero-job workflow run as an unexplained failed run, not as a cloud failure
  or successful OIDC validation.

## Implementation tasks

- [x] Capture one CLI snapshot of all open PRs and their check states.
- [x] Record the final PR #66 check result and current PR count in the goal and status.
- [x] Label older package status notes as historical snapshots.
- [x] Remove stale “current head” claims from the goal's older PR references.
- [x] Record that the remote plan is stopped by the zero-quota guard and that the
  manually-dispatched AWS workflow did not run any job.
- [x] Record the absent shared-state/budget prerequisites and separate bootstrap
  authorization gate.
- [x] Preserve the historical pre-restack CI evidence and label it as such.
- [x] Add the ticket to the documentation index, evidence manifest, and journal.
- [ ] Publish the rebased PR #67 and pass its current required CI.
- [ ] Obtain human review; do not merge without owner authorization.

## Validation

Read-only command:

```bash
gh pr list --state open --limit 100 \
  --json number,isDraft,statusCheckRollup
```

The historical query found 37 open PRs with completed successful displayed checks at
01:40Z, before PR #67 opened. It is only a point-in-time snapshot; the current draft
state, PR count, and check results must be taken from GitHub after restacking. Local documentation checks and `git diff --check` are
recorded in the execution journal. PR #66's final head and PR #67's initial commit
each passed the workflow local E2E once; no separate manual clean-room run was started.

## Security and financial considerations

No AWS command, credential, resource mutation, GPU operation, model download, or spend
was used for this ticket. The plan guard was reviewed but not bypassed. The bootstrap
preview is not apply-ready and no placeholder budget alert will be used. The $25 cap,
quota gate, exact-plan review, expiry safeguards, and explicit apply authorization
remain in force.

## Evidence and outstanding work

See the execution journal and evidence manifest for the GitHub snapshot, passing PR
workflow, and failed zero-job workflow distinction. AWS quota remains zero and the
existing request remains `CASE_OPENED`; no L4 acceptance criterion has been met.
