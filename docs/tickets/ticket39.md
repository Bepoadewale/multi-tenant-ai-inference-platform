# Ticket 39 — Record the denied GPU quota request

## Objective

Record the account owner's AWS quota-denial notice, reconcile it with the current
read-only Service Quotas view, check whether nearby US regions remove the blocker,
and prepare (but do not send) a detailed appeal draft.

## Current state

**Status update (2026-11-28):** this ticket preserves the denial and zero-quota
evidence captured on 2026-11-27. The owner later reported that AWS approved the
appeal, and a read-only CLI check confirms an applied 4.0-vCPU quota in `us-east-1`.
The request-history API still says `CASE_OPENED`. This quota does not reserve live
capacity or authorize a launch; use the current [goal](../goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md)
and [status](../gpu-lab/IMPLEMENTATION_STATUS.md) for remaining gates.

The applied On-Demand G and VT quota is zero in `us-east-1`, `us-east-2`, and
`us-west-2`. The owner supplied an AWS email saying the existing 4-vCPU
`us-east-1` request was denied. A fresh Service Quotas history query still reports
`CASE_OPENED` for that request. No duplicate request was submitted and no GPU
infrastructure was created.

## Research and implementation

- AWS's Service Quotas guide says denied requests should be escalated to Support.
- AWS Support documentation explains how to reopen a resolved case in the Support
  Center console.
- The AWS Support `describe-cases` API call returned
  `SubscriptionRequiredException` for the authenticated profile. The draft therefore
  identifies the console as the available case-reopen route.
- `docs/gpu-lab/QUOTA_APPEAL_DRAFT.md` gives AWS the requested details: one
  `g6.xlarge`, exactly four vCPUs, one L4, short cumulative runtime, hard $25 ceiling,
  private Session Manager access, expiry, and teardown verification.

## Acceptance criteria

- [x] Record the AWS denial email as owner-provided evidence without copying private
  mail metadata into the repository.
- [x] Query quota history and applied quota without creating resources.
- [x] Check two nearby US regions before concluding that a region switch helps.
- [x] Prepare a detailed, sanitized appeal draft without sending it.
- [x] Record the support API access error and console limitation.
- [ ] Reconcile the final request state in AWS Support Center.
- [ ] If the owner chooses to appeal, reopen the existing case and later verify the
  resulting AWS decision and quota value.

## Validation and commands

- Service Quotas history in `us-east-1` returned `CASE_OPENED`, desired value `4.0`,
  quota name `Running On-Demand G and VT instances`.
- Read-only applied quota queries returned `0.0` in `us-east-1`, `us-east-2`, and
  `us-west-2`.
- Read-only instance offering queries list `g6.xlarge` in the three checked regions.
- AWS Support `describe-cases` returned `SubscriptionRequiredException`.
- `git diff --check` passed.
- No Terraform plan/apply, AWS resource mutation, or GPU launch was performed.

## Failed approaches and troubleshooting

- A first history query used the wrong response key (`RequestedQuota`) and returned
  `null`; inspecting the response keys showed `RequestedQuotas`, and the corrected
  query returned the existing request. No new request was sent.
- `get-requested-service-quota-change` returned `null` for the request ID. The
  history-list operation is the current evidence source for the request record.
- The Support API call is not available under this account support subscription.
  Reopening must use Support Center unless the account's support entitlement changes.

## Security and financial considerations

No account number, credentials, support-case identifiers, or mail headers are stored
in this ticket. No cloud resources or spending were created. The draft retains the
hard $25 spending ceiling and does not assert that an AWS Budget alert is a hard cap.

## Evidence and limitations

The email itself was supplied by the owner; the repository stores only its sanitized
historical status. The Service Quotas API and email disagreed about the request status
at the time. Regional offerings do not prove capacity. No capacity reservation,
infrastructure, or GPU execution is demonstrated by this ticket.

## Outstanding work

- The owner can reconcile/reopen the existing case through AWS Support Center using
  the draft, if they choose to appeal.
- Continue non-billable engineering while quota is unresolved.
