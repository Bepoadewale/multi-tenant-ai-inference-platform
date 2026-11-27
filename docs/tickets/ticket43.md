# Ticket 43 — Test Terraform remote-lock configuration and update quota status

## Objective

Protect the isolated GPU Terraform wrappers against accidentally dropping either of
the repository's configured state-lock mechanisms. Record the owner's report that an
appeal was sent manually, without claiming AWS receipt or outcome.

## Current state

The plan and destroy-plan wrappers configure both Terraform S3 lockfiles and the
existing DynamoDB lock table. New fake-command tests check that both options reach
`terraform init`. They do not initialize the real remote backend or test lock
acquisition, contention, or release. The owner reports submitting the appeal through
the existing AWS Support Center case. Read-only Service Quotas results still show
`CASE_OPENED` and applied quota `0.0`; the checked email search has no newer reply.
No GPU infrastructure has been provisioned.

## Research and implementation

HashiCorp's [S3 backend documentation](https://developer.hashicorp.com/terraform/language/backend/s3)
describes native S3 lockfiles using `use_lockfile` and documents DynamoDB locking as
deprecated while supporting both during migration. The official Terraform
[S3 backend implementation](https://github.com/hashicorp/terraform/blob/main/internal/backend/remote-state/s3/client.go)
acquires configured locks and releases the S3 lock if acquiring the DynamoDB lock
fails. The project retains both because its shared repository bootstrap requires the
DynamoDB table and the selected Terraform version supports the S3 lockfile. Live
backend validation remains pending until those shared resources exist through the
approved bootstrap workflow.

## Changes

- Asserted plan/apply initialization includes the expected DynamoDB table and
  `use_lockfile=true` arguments.
- Asserted destroy-plan initialization includes both lock arguments.
- Updated the goal, status, research notes, execution journal, evidence manifest,
  quota appeal record, and ticket #41 to distinguish the owner's report from
  independently verified AWS receipt or decision.

## Validation

- `pytest gateway/tests/test_gpu_ec2_scripts.py -q` — 14 passed.
- Ruff on the changed test — passed.
- `git diff --check` — passed.
- PR #42 run `45977824955` passed all four required jobs before this follow-up.

## Security and financial considerations

No AWS write or support message was sent. These are local tests using fake commands;
they do not prove remote lock safety. No resources, GPU hours, or spend were created.
No case number, account identifier, credentials, or email headers were added.

## Outstanding work

- Publish this focused package as a pull request and wait for its CI checks.
- Test backend permissions and lock lifecycle only after the shared backend is
  available through its authorized setup.
- Do not launch a GPU instance until applied quota, the exact saved plan, current
  total-cost estimate, runtime cap, expiry controls, and teardown process are
  independently checked.
