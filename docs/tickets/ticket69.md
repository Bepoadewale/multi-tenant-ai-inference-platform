# Ticket 69 — refresh the single-L4 cost inputs

## Objective

Refresh the AWS catalog rates that drive the bounded single-L4 planning estimate,
record the exact units, and keep the $25 spending ceiling and authorization boundary
clear.

## Current state

- The read-only AWS Price List API returned `$0.8048/Hrs` for `g6.xlarge` On-Demand
  `BoxUsage`, `$0.005/Hrs` for an in-use public IPv4 address, and `$0.08/GB-Mo` for
  gp3 in `us-east-1` on 2026-11-28.
- The `g6.xlarge` record is effective 2026-11-01, uses Linux, shared tenancy, and no
  preinstalled software. The API also returned unused-capacity-reservation terms;
  only the `BoxUsage` term is used in the run-rate estimate.
- The first arithmetic check found the old 100-GiB gp3 line was understated by about
  ten times. The API uses GB-Mo; 100 GiB is about 107.3742 decimal GB, making 12-hour
  storage about `$0.1432` rather than `$0.0133`.
- The corrected 12-hour planning envelope is `$18.51932705` (about `$18.52`), including
  existing egress, state, tax, and contingency assumptions. It leaves `$6.48067295`
  under the $25 ceiling. This is an estimate, not a quote, invoice, hard cap, or
  spending authorization.
- Additional read-only Price List queries verified S3 Standard first-tier storage at
  `$0.023/GB-Mo`, S3 write/list requests at `$0.005/1,000`, S3 GET requests at
  `$0.0004/1,000`, DynamoDB on-demand writes/reads at `$0.625/$0.125` per million
  request units, and EventBridge Scheduler's first 14 million invocations at no
  charge. Existing positive request/expiry reserves remain in the estimate.
- The latest read-only check confirms 4.0 applied On-Demand G/VT vCPUs and
  `CASE_CLOSED`. This is enough by quota for one `g6.xlarge`, but not capacity or
  spending approval. No GPU or AWS resources have been created by this project.

## Work completed

- [x] Query AWS Price List API for `g6.xlarge` Linux shared On-Demand pricing in
  `US East (N. Virginia)` and record the effective date and selected usage term.
- [x] Query public IPv4 in-use pricing and gp3 storage pricing for the same region.
- [x] Record the pricing units and refresh `COST_REPORT.md` and `RESEARCH_NOTES.md`.
- [x] Recheck the arithmetic and correct the prior gp3 unit-conversion error across
  current status and evidence records.
- [x] Reconcile the inputs with the `$25` ceiling and existing bounded-runtime estimate.
- [x] Update the persistent goal, status, backlog, journal, evidence manifest, and docs
  index.
- [x] Run local documentation, arithmetic, and diff checks.
- [ ] Pass required PR checks and leave the PR open for human review.

## Validation and evidence

Read-only AWS Price List API queries returned the compute, public IPv4, gp3, S3,
DynamoDB, and Scheduler inputs recorded above. A local decimal calculation corrected
the EBS unit conversion by converting 100 GiB to 107.3742 GB before applying the
GB-Mo rate. The full-precision estimate is `$18.51932705`, leaving `$6.48067295`
below the $25 ceiling under the stated assumptions. These rates and the estimate must
be refreshed against the exact plan before any billable operation. The ticket stores
no account identity, credential, or private value.

The original PR #69 checks do not validate the current rebased head. PR #66 refreshed
run `46164644804` passed all six jobs; PR #67 run `46164896175` and PR #68 run
`46165126075` were still running at this snapshot. PR #69 needs its own fresh CI after
publication. On the current rebase, 64 relative links across five changed Markdown
files resolve and `git diff --check` passes.

## Security and financial considerations

No AWS mutation, Terraform operation, GPU launch, model download, or spend was
performed. The rates are regional catalog data. The final plan must still verify
account-wide transfer use, state retention and requests, taxes, the budget recipient,
actual runtime safeguards, and every billable resource. Quota approval alone is not
apply authorization.

## Outstanding work

Human PR review remains open. The final remote-state plan, validated budget recipient,
explicit bounded apply authorization, and all real L4 execution remain outstanding.
- PR #69 is rebased onto current PR #68 head `ff88165`; its refreshed head needs to be
  published and receive fresh CI. Historical PR #69 checks do not validate this base.
