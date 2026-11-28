# Ticket 74 — Guarded Terraform state bootstrap operations

## Objective

Make the first AWS state-backend setup reproducible and reviewable without placing
the Budget alert address, Terraform state, or saved plan in public Git. A bootstrap
mistake could affect shared Terraform state used by the later GPU infrastructure, so
plan and state handling need explicit safeguards before any cloud apply.

## Current state

The bootstrap Terraform root defines seven resources: one project state bucket and
its four security/versioning controls, one DynamoDB lock table, and one monthly AWS
Budget alert. Earlier work had a static preview helper, but did not provide a private
saved-plan workflow, digest-bound apply command, or reproducible state migration
commands. AWS has no matching project backend resources yet. This ticket does not
apply or mutate AWS resources.

## Design

- Keep all bootstrap Terraform files and logs in a mode-700 `.local/` workspace.
- Read the Budget address from a private shell environment variable and never print
  it in the plan summary.
- Check account identity and verify that the exact project bucket, lock table, and
  Budget are absent before planning or applying.
- Permit only the exact seven approved create actions; reject updates, deletes, or
  unrelated managed resources.
- Save the plan privately, print its SHA-256 digest, and require that exact digest and
  an explicit confirmation token for apply.
- On uncertain apply results, stop for reconciliation rather than retrying.
- Require separate confirmation to migrate the exact seven-resource local state into
  the encrypted, versioned S3 backend with DynamoDB and S3 state locking.
- Keep a private local state copy after migration for recovery; do not automatically
  delete it.
- Clearly state that an AWS Budget is an alert, not a hard cost limit.
- Require Terraform 1.10 or newer because the migration enables the native S3
  `use_lockfile` backend option, first available in Terraform 1.10.

## Research

The [official HashiCorp S3 backend documentation](https://developer.hashicorp.com/terraform/language/backend/s3)
documents `use_lockfile` and marks DynamoDB-based S3 locking as deprecated. The
repository keeps both mechanisms during migration because its existing backend
contract uses the DynamoDB lock table. Terraform 1.10+ is therefore the minimum for
this workflow.

## Changes

- Added shared input/account/resource/state checks for bootstrap operations.
- Added private plan, digest-checked apply, and confirmed backend migration scripts.
- Added a JSON plan validator that checks resource addresses, actions, account-scoped
  bucket name/tags, public access controls, encryption, versioning, lock-table mode,
  budget ceiling, and actual-cost alert thresholds. The printed summary hides the
  alert address.
- Added Make targets and operator instructions, including a hidden prompt for the
  private email input and recovery guidance.
- Added fake-tool tests for a safe plan/apply path and refusal cases. Tests do not
  contact AWS or invoke real Terraform.

## Validation

- Six focused fake-tool tests passed.
- `bash -n` passed for the four bootstrap shell scripts.
- `make terraform-validate` passed for the bootstrap, existing EKS, and GPU Terraform
  roots.
- Before restacking, `make verify` passed: Ruff; 199 tests passed and 2 skipped; no known dependency
  vulnerabilities; base/GPU Compose and observability validation passed; benchmark,
  evaluation, and CUDA targets ran in dry-run mode only.
- After restacking on the updated quota-readiness branch, six focused fake-tool tests
  passed using `.venv/bin/python -m pytest`; `bash -n` and `make terraform-validate`
  passed again for the current source. Full `make verify` and fresh CI remain pending.
- The first test attempt used the system `pytest` command, which is not installed on
  this workstation. Using the repository's `.venv/bin/python -m pytest` succeeded.
- `git diff --check` passed before the current documentation follow-up.
- The pre-existing bootstrap preview target was invoked without its required account
  variable and stopped immediately. It made no AWS call; no retry was needed because
  static Terraform validation was run separately.
- Review found that the bootstrap's old Terraform minimum (`1.8.0`) was below the
  S3-native lockfile feature requirement (`1.10`). Updated the bootstrap root and
  operator guide to require Terraform `>=1.10.0, <2.0.0` before publishing the PR.
- Fresh pull request CI is pending. No Terraform plan, apply, or state migration was run.

## Security and cost

No credentials or private email are included in source files. Saved plans, logs, and
local state remain ignored private artifacts. No account-wide cleanup or unrelated
resource access is part of this package. A configured Budget threshold does not
enforce the $25 total project cap; runtime limits, exact resource plans, and teardown
remain necessary. No AWS resource, GPU hour, model download, or cloud cost was
incurred by this ticket.

## Outstanding work

- Run the full current-head verification and review CI results.
- Obtain the owner's private alert address and explicit authorization before any
  future bootstrap apply; a passing PR does not authorize AWS changes.
- Later document teardown for the state bucket, including versioned-object handling,
  only after the owner explicitly authorizes those deletions.

## Acceptance status

**Focused local tests, shell syntax, and all Terraform-root validations pass on the
restacked source. Full local verification and current-head PR CI are pending.** Cloud
bootstrap and state migration remain intentionally unexecuted until independently
authorized.
