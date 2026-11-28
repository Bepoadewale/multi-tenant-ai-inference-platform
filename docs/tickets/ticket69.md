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

The three API lookups were read-only and used the configured AWS CLI profile. A local
decimal calculation caught the existing EBS arithmetic error; the line now converts
100 GiB to 107.3742 GB before applying the GB-Mo rate. `git diff --check` passed, a
repository scan found no missing relative Markdown targets in 114 files and 205
links, and the full-precision estimate calculation passed: `$18.5172`, with `$6.4828`
headroom. No account identity, credential, or private value is stored in this ticket.
Required GitHub Actions remain pending. Pricing must be refreshed again before any
billable plan.

## Security and financial considerations

No AWS mutation, Terraform operation, GPU launch, model download, or spend was
performed. The rates are regional catalog data. The final plan must still verify
account-wide transfer use, state retention and requests, taxes, the budget recipient,
actual runtime safeguards, and every billable resource. Quota approval alone is not
apply authorization.

## Outstanding work

Human PR review remains open. The final remote-state plan, validated budget recipient,
explicit bounded apply authorization, and all real L4 execution remain outstanding.
