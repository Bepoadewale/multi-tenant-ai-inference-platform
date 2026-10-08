## Objective

## Changes

## Validation

## Demonstrated Behavior

## Failure Cases Tested

## Remaining Gaps

## Status Changes

## Completion Gate Evidence

## Explicitly Unexecuted / Simulated Adapters

## Cloud-pilot evidence (required for any PR claiming cloud execution)

- [ ] Exact account/region, commit SHA, and expected-account guard recorded.
- [ ] Terraform plan/apply summary recorded; no manual resource creation.
- [ ] Image digest, GitOps revision, and runtime readiness recorded.
- [ ] Tenant/policy success path and a failure/rollback path recorded.
- [ ] Metrics, traces, audit, dashboard/alert, bounded-load, and Cost Explorer results recorded.
- [ ] Destroy plan/result and provider-side resource-absence checks recorded.
- [ ] Any unsettled billing is labeled estimated; unexecuted adapters remain explicit.

## Clean-room evidence (required before any implementation PR is review-ready)

- [ ] Clean project state established and verified.
- [ ] Bootstrap and smoke checks passed.
- [ ] Primary demo and required failure/security demo passed.
- [ ] Full required validation passed.
- [ ] Project-scoped cleanup passed; no project runtime resources remained unexpectedly.
- [ ] Second clean bootstrap passed.
- [ ] `docs/VALIDATION.md`, README commands, and `PROJECT_STATUS.md` were updated with real evidence.

If this is a documentation-only PR, state why runtime clean-room execution is not applicable. Do
not use that exception for implementation, configuration, container, dependency, or demo changes.
