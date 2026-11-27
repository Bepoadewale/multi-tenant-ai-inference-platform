# Ticket 39 — Record the denied GPU quota request

## Objective

Record the account owner's AWS quota-denial notice, reconcile it with the current
read-only Service Quotas view, check whether nearby US regions remove the blocker,
and prepare a detailed appeal message for the existing case.

## Current state

**Status update (2026-11-28):** this ticket preserves the denial and zero-quota
evidence captured on 2026-11-27. The owner later reported that AWS approved the
appeal, and a read-only CLI check confirms an applied 4.0-vCPU quota in `us-east-1`.
The request-history API still says `CASE_OPENED`. This quota does not reserve live
capacity or authorize a launch; use the current [goal](../goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md)
and [status](../gpu-lab/IMPLEMENTATION_STATUS.md) for remaining gates.

The applied On-Demand G and VT quota is zero in `us-east-1`, `us-east-2`, and
`us-west-2`. The owner supplied an AWS email saying the existing 4-vCPU
`us-east-1` request was denied, then explicitly authorized reopening the same case.
Service Quotas still reports `CASE_OPENED`. The AWS CLI communication attempt failed
with `SubscriptionRequiredException` before sending a message. No duplicate quota
request, new support case, or GPU infrastructure was created.

## Research and implementation

- AWS's Service Quotas guide says denied requests should be escalated to Support.
- AWS Support documentation explains how to reopen a resolved case in the Support
  Center console.
- AWS Support `describe-cases` and `add-communication-to-case` both returned
  `SubscriptionRequiredException`. The installed CLI has no `support reopen-case`
  operation; its help says Support API calls require a Business, Enterprise On-Ramp,
  or Enterprise Support plan.
- Service Quotas has a `create-support-case` CLI operation, but it only applies to
  requests in `PENDING` status. This request reports `CASE_OPENED`, so that command
  is not a reopen route and was not called.
- After the owner authorized reopening the existing case, we verified the AWS
  caller identity and attempted to add the prepared appeal through the CLI. AWS
  rejected the operation before sending; no case state changed.
- AWS's Support guide documents reopening a resolved case through Support Center.
- `docs/gpu-lab/QUOTA_APPEAL_DRAFT.md` gives AWS the requested details: one
  `g6.xlarge`, exactly four vCPUs, one L4, short cumulative runtime, hard $25 ceiling,
  private Session Manager access, expiry, and teardown verification.

## Acceptance criteria

- [x] Record the AWS denial email as owner-provided evidence without copying private
  mail metadata into the repository.
- [x] Query quota history and applied quota without creating resources.
- [x] Check two nearby US regions before concluding that a region switch helps.
- [x] Prepare a detailed, sanitized appeal message.
- [x] Follow the owner's authorization and try the existing-case CLI communication
  operation after verifying the AWS identity.
- [x] Record that Support API listing and communication are blocked by the account's
  Support plan; no message was sent.
- [ ] Reopen the existing case through Support Center using the AWS email link or
  another authorized console operator, then verify the decision and applied quota.

## Validation and commands

- Service Quotas history in `us-east-1` returned `CASE_OPENED`, desired value `4.0`,
  quota name `Running On-Demand G and VT instances`.
- Read-only applied quota queries returned `0.0` in `us-east-1`, `us-east-2`, and
  `us-west-2`.
- Read-only instance offering queries list `g6.xlarge` in the three checked regions.
- AWS Support `describe-cases` returned `SubscriptionRequiredException`.
- `aws support add-communication-to-case` with the existing case ID and prepared
  message returned `SubscriptionRequiredException` after AWS identity verification.
- `aws support help` lists `add-communication-to-case` but no `reopen-case`, and
  states that Support API operations require an eligible paid Support plan.
- `aws service-quotas help` lists `create-support-case`; its help says the operation
  only creates a Support case when the quota request status is `PENDING`. This
  request status is `CASE_OPENED`, so the operation was not called.
- `git diff --check` passed.
- No Terraform plan/apply, AWS resource mutation, or GPU launch was performed.

## Failed approaches and troubleshooting

- A first history query used the wrong response key (`RequestedQuota`) and returned
  `null`; inspecting the response keys showed `RequestedQuotas`, and the corrected
  query returned the existing request. No new request was sent.
- `get-requested-service-quota-change` returned `null` for the request ID. The
  history-list operation is the current evidence source for the request record.
- The Support API is unavailable under this account subscription. The attempted CLI
  write failed before sending. The documented Support Center workflow remains the
  supported way to reopen this resolved case.

## Security and financial considerations

No account number, credentials, support-case ID, or mail headers are stored in this
ticket. The appeal attempt created no communication, cloud resource, or spend. The
draft retains the hard $25 spending ceiling and does not treat an AWS Budget alert as
a hard cap.

## Evidence and limitations

The email itself was supplied by the owner; the repository stores only its sanitized
historical status. The Service Quotas API and email disagreed about the request status
at the time. Regional offerings do not prove capacity. No capacity reservation,
infrastructure, or GPU execution is demonstrated by this ticket.

## Outstanding work

- The owner authorized reopening the existing case, but the available CLI write was
  blocked by the Support plan. Reopen through the Support Center link in the AWS
  email, or use an eligible account Support plan that permits Support API access.
- Continue non-billable engineering while quota is unresolved.
