# Ticket 71: reconcile the model-release backlog with the host controller

## Objective

Make the release backlog distinguish implemented host-controller source from
real-host acceptance. The current checklist incorrectly leaves source work
unchecked even though the dependent controller PR implements it.

## Current state

- PR #70 old head `5f70852` passed six required jobs in run `46117637674`; refreshed head `1679aa7` has run `46165597103` active. PR #71's old head `63df036` passed all six in `46119306265`; its current local restack is on #70 head `1679aa7` and needs fresh CI after publication. These are CI/local checks, not live AWS or GPU results.
- The release controller from PR #56 is source-tested and CI-validated on its recorded
  commit, but it has not been run against the GPU host, a live vLLM container, or real
  model weights. Live champion verification, inference, rollback, and interruption
  recovery remain L4 acceptance work.
- A live GitHub snapshot on 2026-11-28 found 54 open PRs (#30–#84, excluding #54),
  with no drafts at that capture time. This does not show review approval or merge
  authority; query GitHub before using this snapshot as current state.
- The recorded corrected 12-hour planning envelope is `$18.5193`, under the initial
  `$25` ceiling on paper. It is not billed spend, a quote, or apply authorization.
- AWS applied On-Demand G/VT quota is approved at 4.0 vCPUs in `us-east-1`; a later
  2026-11-28 read-only check shows request history `CASE_CLOSED`. This is enough by quota for
  one `g6.xlarge` but does not reserve AZ capacity or authorize spending. The exact
  project state bucket, lock table, and Budget are absent; a valid private recipient
  is not verified. No project GPU or AWS resource has been created.
- Complete feasible non-GPU work and launch controls before the authorized GPU batch.
  The one designated integrated
  local CPU clean-room run is recorded in `docs/governance/VALIDATION.md`: source
  `49076a5`, run `46114955314`. The final cloud/GPU clean-room remains Phase 12 work;
  no additional manual local clean-room run should be started.

## Changes

- Mark host-side champion/model verification and sequential deploy/recovery source as
  implemented in the backlog, with an explicit reference to PR #56.
- Keep live champion verification, model-byte verification, real inference, rollback,
  and interruption recovery as pending L4 acceptance criteria.
- Record this reconciliation in the goal and execution journal and link this ticket
  from the documentation index.

## Acceptance criteria

- [x] Backlog checkboxes match the current controller source and test evidence.
- [x] Runtime acceptance remains explicitly unverified.
- [x] Markdown link and whitespace checks pass.
- [x] Prior PR #71 checks passed on their historical heads.
- [x] Rebase PR #71 on current PR #70 head `1679aa7`.
- [ ] Publish the rebased PR #71 and pass current CI.

## Security and cost

Documentation-only change. No secrets, model artifacts, Terraform state, or private
AWS output are added. No AWS calls, GPU work, or spending.

## Validation

On the current restack, 66 relative links across four changed Markdown files resolve and
`git diff --check` passes. The prior PR #71 head `ee8d1ef` passed all six required jobs,
including local E2E, in run `46116269039`. This is historical after the rebase and does
not validate the current local head. The designated local CPU clean-room record remains
run `46114955314`; neither run proves model release on a real host.

## Limitations

The current PR #71 head still needs CI and human review. PR #56 source evidence does not demonstrate live L4 operation. Fake-based tests do not validate Docker
behavior, vLLM readiness, actual model bytes, authenticated inference, rollback on an
EC2 host, or recovery after host interruption. The L4 execution and $25 AWS cost gates
remain. Quota is approved, but remote state, Budget and verified recipient, exact
plan/cost, expiry, capacity, and separate apply authorization remain open.
