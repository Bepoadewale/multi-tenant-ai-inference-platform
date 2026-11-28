# Ticket 71: reconcile the model-release backlog with the host controller

## Objective

Make the release backlog distinguish implemented host-controller source from
real-host acceptance. The current checklist incorrectly leaves source work
unchecked even though the dependent controller PR implements it.

## Current state

PR #56 is open and unmerged. Its head `852c87313777fc1e0346339bafabac92496c92da`
passed its five required checks in run `46040861818`. Sixteen focused fake-based
tests and the repository validation are recorded in `docs/tickets/ticket56.md`. The
controller source verifies the active champion and model snapshot, performs a
sequential restart, records transaction state, and supports recovery. None of these
actions has been run on the authorized GPU host.

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
- [x] PR CI passes on implementation head `99eb3284a388f5a54616dc843a2e134c4acc570a`.

## Security and cost

Documentation-only change. No secrets, model artifacts, Terraform state, or private
AWS output are added. No AWS calls, GPU work, or spending.

## Validation

`git diff --check` and relative links in the five changed Markdown files passed. PR
#71 head `99eb3284a388f5a54616dc843a2e134c4acc570a` passed all six required jobs in
run `46102374147`, including local E2E. This verifies repository/static behavior,
not model release on a real host.

## Limitations

PR #56 remains open for human review. Fake-based tests do not validate Docker
behavior, vLLM readiness, actual model bytes, authenticated inference, rollback on an
EC2 host, or recovery after host interruption. The L4 execution and $25 AWS cost
gates remain unchanged.
