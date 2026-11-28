# Ticket 68 — record GPU automation and CI readiness

## Objective

Audit the existing command and workflow surface for deployment readiness. Mark the
automation source complete only where commands and safeguards exist, and keep real
AWS/host execution clearly separate.

## Current state

- Makefile targets exist for GPU preflight, Terraform validation/plan/apply, Ansible
  validation/configuration, Compose configuration/deployment, smoke, benchmark,
  evaluation, incident drills, evidence export, destroy, and cleanup verification.
- The normal CI workflow runs local Python, Terraform, Ansible, Compose, GPU config,
  supply-chain, and local E2E checks. It does not configure AWS credentials or perform
  paid AWS actions.
- The separate AWS workflow uses `workflow_dispatch` with explicit operation and
  confirmation inputs. It is not invoked by ordinary pull-request CI.
- The guarded host wrappers and fake-based tests are in PR #64; all six required CI jobs passed on head `06f1a11` in run `46114151883`. No AWS host or GPU operation has been performed.
- PR #65 source head `49076a5` passed all six jobs in `46114955314`; the designated local clean-room record is in `docs/governance/VALIDATION.md`. PR #65 governance follow-up head `24ea5e8` needs fresh CI. PR #66 head `2c5766e` and PR #67 head `7b9fb9f` are newly published and need current checks. PR #68 has been locally rebased onto #67 head `7b9fb9f`; current head `224b035` is not yet published.
- The remote plan remains blocked by zero applied G/VT quota and absent shared
  bootstrap resources. The $25 ceiling and separate apply authorization remain.

## Research and design

- Treat command presence, static checks, local test execution, and real EC2 execution
  as separate evidence levels.
- Do not mark Phase 11 fully executed just because the automation source exists.
- Keep normal PR CI free of AWS credentials and paid cloud steps. Reserve cloud work
  for an explicitly dispatched, guarded operation.

## Implementation tasks

- [x] Audit the Makefile command surface for the full planned lifecycle.
- [x] Audit normal CI and confirm it has no AWS credentials or paid operations.
- [x] Audit the separate AWS workflow and confirm it is manual-dispatch only with
  explicit destructive-operation confirmations.
- [x] Update the backlog and implementation status to mark automation source ready,
  with host/AWS execution still outstanding.
- [x] Add this ticket to the documentation index, goal, journal, and evidence manifest.
- [x] Rebase PR #68 on PR #67 head `7b9fb9f`.
- [ ] Publish rebased PR #68 and pass current required CI.
- [ ] Obtain human review; do not merge without owner authorization.

## Validation

Static source inspection checked Makefile targets, `.github/workflows/ci.yml`, and
`.github/workflows/aws-pilot-oidc.yml`. PR #64's recorded required CI and local fake
tests provide implementation evidence; this ticket does not rerun them. The current PR workflow must validate the rebased head; prior parent checks do not cover this change. No separate manual clean-room run was started. One integrated run remains planned after the non-GPU stack settles.

## Security and financial considerations

No AWS call, credential use, resource mutation, model download, GPU execution, or spend
was required. Cloud execution remains separately guarded. The $25 ceiling is a hard
limit, not authority to bypass quota, bootstrap, plan review, or apply confirmation.

## Evidence and outstanding work

The source audit and CI workflow demonstrate automation readiness only. The selected local CPU clean-room record is `docs/governance/VALIDATION.md` (source `49076a5`, run `46114955314`). Terraform
apply, Ansible on Ubuntu, Docker GPU access, real inference, teardown, and independent
cleanup verification remain unexecuted. The quota and bootstrap authorization gates
remain open.
