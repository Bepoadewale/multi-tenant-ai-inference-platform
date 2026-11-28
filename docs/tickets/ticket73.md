# Ticket 73 — Reconcile current AWS quota and launch readiness

**Pull request:** [#73](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/73), stacked on PR #72.

## Objective

Refresh the current AWS capacity and project-resource facts after the previously
recorded quota denial, then correct current-state documentation without changing any
AWS resource.

## Findings

- The key profile's caller identity matched the expected project account. The account
  number is omitted from public documentation.
- Service Quotas now returns applied On-Demand G/VT quota `4.0` vCPUs, enough on paper
  for the one selected `g6.xlarge`. The existing request history still says
  `CASE_OPENED` in this snapshot. A later read-only check recorded in PR #71 returned
  `CASE_CLOSED`; the owner also confirmed approval. Do not create a duplicate request.
- EC2 lists `g6.xlarge` in us-east-1a, 1b, 1c, 1d, and 1f. This does not reserve live
  capacity.
- The current AWS Price List API query returns `$0.8048/hour`, consistent with the
  estimate in `COST_REPORT.md`.
- Exact project-tag inventory and project EC2 query returned zero resources. The
  expected state bucket, lock table, and project budget were not found.
- The account has no billing alternate contact. A private primary-contact query did
  not provide a usable address to this profile. No email address was printed or added
  to the repository; the Bootstrap example remains `example.invalid`.
- The guarded `make gpu-ec2-preflight` accepted identity, AMI, applied quota, and the
  selected offered AZ, then stopped at `HeadBucket: 404 Not Found` because the remote
  Terraform backend has not been created.

## Changes

- Reconciled current quota wording in the goal, implementation status, cost report,
  risk register, backlog, operator handbook, benchmark/report status, and Terraform
  README. Older journal and validation entries remain unchanged as historical evidence.
- Recorded the read-only results and preflight stop condition in the execution journal
  and evidence manifest.
- PR #72's six checks passed at `ef1f5e3` in run `46124118809`; that was before the
  latest rebase and is historical only.

## Validation and evidence limits

- `git diff --check` — passed after the documentation reconciliation.
- `make gpu-ec2-preflight` — intentionally stopped before plan/apply at the missing
  state bucket; no mutation occurred.
- No Terraform plan/apply, model download, instance launch, GPU hour, or AWS spend.
- Five AZ offerings do not prove current capacity. An applied quota value does not
  authorize spending.
- This PR does not address historical dated quota snapshots in the execution journal
  or validation records.

## Financial and security notes

The $25 ceiling and `$18.5193` 12-hour planning estimate are unchanged. AWS Budgets is
an alert, not a hard spending limit. The bootstrap root cannot be used with its
placeholder email address; a verified recipient must be supplied privately before
that alert can be created. No credentials or private contact data are committed.

## Outstanding work

- Obtain a private, verified email recipient for the project Budget alert, or establish
  an authorized alternative while preserving the cost-monitoring requirement.
- Review the owner-required cloud-pilot authorization and exact bootstrap plan before
  any bootstrap mutation.
- Create the backend only after the bounded bootstrap plan is reviewed; then generate
  the locked GPU-root plan and independently verify the full resource and cost scope.
- Recheck quota, AZ offering, live capacity, price, $25 total, expiry, and teardown
  immediately before any approved GPU batch.
