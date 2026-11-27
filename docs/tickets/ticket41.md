# Ticket 41 — Attempt the authorized quota-case update through AWS CLI

## Objective

Follow the owner's instruction to reopen the existing 4-vCPU G/VT quota case through
the AWS Command Line Interface (CLI), using the detailed appeal already prepared.
Avoid creating a duplicate quota request or a separate support case.

## Current state

The owner authorized reopening the existing case and said to use the CLI. The account
identity was verified before the write attempt. `aws support add-communication-to-case`
returned `SubscriptionRequiredException` before sending the appeal. The AWS CLI has
no `support reopen-case` operation. A fresh read after the failed write still shows
the same request status (`CASE_OPENED`) and applied On-Demand G/VT quota (`0.0`). No
message, new support case, quota request, resource, GPU hour, or spend was created.

## Research and findings

- The existing Service Quotas record exposes a `CaseId` matching the display ID in
  the original AWS email; no case identifier is saved in this public ticket.
- `aws support help` lists `add-communication-to-case` but no `reopen-case`. It also
  states Support API use requires Business, Enterprise On-Ramp, or Enterprise
  Support.
- The authorized `add-communication-to-case` call was attempted with the prepared
  appeal body. AWS returned `SubscriptionRequiredException`; the write did not occur.
- `aws service-quotas help` lists `create-support-case`; its command help says it only
  creates a Support case when the quota request is `PENDING`. The current request is
  `CASE_OPENED`, so the command is not an existing-case reopen operation and was not
  called.
- AWS's official [case management guide](https://docs.aws.amazon.com/awssupport/latest/user/monitoring-your-case.html)
  documents reopening a resolved case through the Support Center. The official
  [Support API guide](https://docs.aws.amazon.com/awssupport/latest/user/about-support-api.html)
  documents the case communication APIs and account-plan requirement. The official
  [CLI command reference](https://docs.aws.amazon.com/cli/latest/reference/support/add-communication-to-case.html)
  gives the `add-communication-to-case` operation and its access requirement.

## Acceptance criteria

- [x] Verify the current AWS caller is in the expected project account.
- [x] Inspect AWS CLI operations for an existing-case reopen path.
- [x] Attempt the authorized existing-case communication using the prepared appeal.
- [x] Confirm the API denied the call before sending due to Support plan entitlement.
- [x] Recheck quota request status and applied quota after the failed attempt.
- [x] Avoid a duplicate quota request or support case.
- [ ] Reopen the case and receive a new AWS decision through an eligible support path.

## Commands and results

- `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity` — account matched
  the expected project account; identity was not copied into public evidence.
- The SSO profile had no cached token. An `aws sso login` device-auth attempt was
  stopped after the owner clarified that the CLI path should be used; no SSO session
  was established and no browser interaction or AWS change occurred.
- `AWS_PROFILE=ai-platform-pilot-key aws support help` — no `reopen-case` operation;
  command help states the Support API plan requirement.
- `AWS_PROFILE=ai-platform-pilot-key aws support add-communication-to-case ...` —
  returned `SubscriptionRequiredException`. AWS did not accept the communication.
- `AWS_PROFILE=ai-platform-pilot-key aws service-quotas get-requested-service-quota-change ...`
  — returned `CASE_OPENED`, desired value `4.0`, unchanged last-updated timestamp.
- `AWS_PROFILE=ai-platform-pilot-key aws service-quotas get-service-quota ...` —
  returned applied quota `0.0`.
- `aws service-quotas create-support-case help` — says it creates a case only for
  requests in `PENDING`; the command was not executed.
- PR #41 GitHub Actions run `45976696129` passed `python`, `manifests`,
  `supply-chain`, and `local-e2e`.

## Security and financial impact

The caller identity was checked before the only mutating CLI operation. The operation
failed at AWS authorization, before delivering any text. The case ID, account ID,
credentials, and message headers are not in this ticket. No AWS resource or cost was
created. No new quota request or support case was opened.

## Blocker and next step

The available Support API is disabled for this account's current Support plan. To
reopen the existing resolved case, an authorized operator needs to use the Support
Center link in the AWS email, or the account must have a Support plan that enables
the Support API. Continue all non-billable project preparation while the request
remains unresolved. Do not launch GPU infrastructure with zero applied quota.

## Post-ticket update — owner-reported manual appeal

After the CLI attempt was documented, the owner reported manually submitting the
appeal through the existing Support Center case. The connected email search has not
found a new AWS response, and read-only Service Quotas results still show
`CASE_OPENED` with applied quota `0.0`. This records the owner's report; it does not
independently prove delivery or acceptance by AWS. No duplicate appeal or quota
request was sent. Continue non-billable preparation while waiting for AWS.
