# Ticket 67 — reconcile live PR and backlog status

## Objective

Make the durable implementation backlog distinguish current GitHub state from older
per-package notes. Record PR #66's final check result and keep the pre-quota readiness
target clear.

## Current state

- PR #66 final head `094576e522ad188df240c4b822a31eda41280694` passed all six required
  jobs in run `46093702808`, including the workflow local end-to-end cycle.
- One read-only CLI snapshot on 2026-11-28 found 37 open PRs, #30–#66. Every PR was
  non-draft and all displayed check runs were completed successfully. The snapshot
  does not show review approval, merge permission, or merged code.
- The guarded GPU plan wrapper runs the strict preflight before Terraform initializes
  the remote backend. The preflight requires four On-Demand G/VT vCPUs; the latest
  applied quota is zero. The remote-state plan is therefore not available through the
  guarded command until quota changes. Do not bypass that safety check.
- A separate workflow run `46093697237` appeared on the branch push for the
  manually-dispatched AWS OIDC workflow. GitHub reported zero jobs and no logs. The
  workflow file requires a manual dispatch and explicit inputs; no AWS step ran. The
  reason for the empty push event is unknown and does not affect the required PR CI.
- The untracked root `uv.lock` belongs to the user and remains untouched.

## Research and design

- Use the PR list snapshot only as an observation at its capture time. Human review
  and merge authority remain separate facts.
- Keep detailed package notes for historical context, but direct readers to live GitHub
  for current PR heads, checks, reviews, and merge state.
- Keep Terraform preflight guards intact. Quota approval can enable a reviewed plan;
  it does not authorize an apply or GPU spend.
- Treat the zero-job workflow run as an unexplained failed run, not as a cloud failure
  or successful OIDC validation.

## Implementation tasks

- [x] Capture one CLI snapshot of all open PRs and their check states.
- [x] Record the final PR #66 check result and current PR count in the goal and status.
- [x] Label older package status notes as historical snapshots.
- [x] Record that the remote plan is stopped by the zero-quota guard and that the
  manually-dispatched AWS workflow did not run any job.
- [x] Add the ticket to the documentation index, evidence manifest, and journal.
- [ ] Obtain human review; do not merge without owner authorization.

## Validation

Read-only command:

```bash
gh pr list --state open --limit 100 \
  --json number,isDraft,statusCheckRollup
```

The query found 37 open, non-draft PRs with completed successful displayed checks.
Local documentation checks and `git diff --check` are recorded in the execution
journal. No separate clean-room run was started; the PR workflow already performed
one local E2E cycle on PR #66's final head.

## Security and financial considerations

No AWS command, credential, resource mutation, GPU operation, model download, or spend
was used for this ticket. The plan guard was reviewed but not bypassed. The $25 cap,
quota gate, exact-plan review, expiry safeguards, and explicit apply authorization
remain in force.

## Evidence and outstanding work

See the execution journal and evidence manifest for the GitHub snapshot, passing PR
workflow, and failed zero-job workflow distinction. AWS quota remains zero and the
existing request remains `CASE_OPENED`; no L4 acceptance criterion has been met.
