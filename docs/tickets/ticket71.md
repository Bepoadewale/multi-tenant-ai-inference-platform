# Ticket 71: reconcile the model-release backlog with the host controller

## Objective

Make the release backlog distinguish implemented host-controller source from
real-host acceptance. The current checklist incorrectly leaves source work
unchecked even though the dependent controller PR implements it.

## Current state

- PR #71 is being rebased onto the latest PR #70 head. Prior PR #71 checks belong to
  older commits and will not validate the new base.
- The release controller from PR #56 is source-tested and CI-validated on its recorded
  commit, but it has not been run against the GPU host, a live vLLM container, or real
  model weights. Live champion verification, inference, rollback, and interruption
  recovery remain L4 acceptance work.
- The latest GitHub snapshot on 2026-11-28 found 41 open PRs (#30–#71, excluding
  #54), with #46, #55, and #65 in draft. PR heads, checks, and reviews can change;
  query GitHub before using this snapshot as current state.
- The recorded corrected 12-hour planning envelope is `$18.5193`, under the initial
  `$25` ceiling on paper. It is not billed spend, a quote, or apply authorization.
- Applied On-Demand G/VT quota remains zero in the latest recorded AWS check. The
  owner reports manually appealing the denied request; AWS has not confirmed the
  result. No project GPU or AWS resource has been created.
- Complete feasible non-GPU work before quota approval. The one integrated local
  clean-room run is still to be done after the PR stack settles; no additional manual
  clean-room run should be started.

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
- [ ] Publish the rebased PR #71 and pass current CI.

## Security and cost

Documentation-only change. No secrets, model artifacts, Terraform state, or private
AWS output are added. No AWS calls, GPU work, or spending.

## Validation

`git diff --check` and relative links in the five changed Markdown files passed. The prior PR #71 head passed all six required jobs in run `46102374147`, including local E2E. This is historical evidence and does not validate the rebased head. This verifies repository/static behavior,
not model release on a real host.

## Limitations

The current PR #71 head still needs CI and human review. PR #56 source evidence does not demonstrate live L4 operation. Fake-based tests do not validate Docker
behavior, vLLM readiness, actual model bytes, authenticated inference, rollback on an
EC2 host, or recovery after host interruption. The L4 execution and $25 AWS cost
gates remain unchanged.
