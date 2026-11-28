# Ticket #54 — Prepare immutable single-L4 LLM release records

## Objective

Add local, testable records for an evaluated LLM candidate and its sequential
single-GPU release plan. Preserve the existing weighted ONNX release API. Reject
failed or stale candidates before any approval or deployment is attempted.

## Current state

- The ONNX release route owns weighted champion/candidate routing and is not suitable
  for the single vLLM endpoint.
- The GPU evaluation runner writes a sanitized report and can publish it to the
  private, disposable MLflow service.
- PR #53 pins and hash-locks the shared container build; all five checks passed on
  the tested code head in run `46023306230`, and all five passed on the docs head in
  run `46025160292`.
- No AWS resource, model, or GPU has been used for this ticket.

## Design

Keep the existing ONNX flow unchanged. A release manifest binds the immutable model
revision, model artifact SHA-256, vLLM image digest, complete serving configuration,
evaluation suite/report digests, source commit, and creation time. A deployment plan
binds both the current champion and candidate manifest digests, target environment,
runtime image/configuration, and evaluation report. Approval state is stored
separately from the immutable plan digest. A different approver is required.

The code is a preparation layer only. It does not yet expose authenticated endpoints,
retrieve the report from MLflow, verify local model files, change Compose configuration,
or restart vLLM. An API must derive requester/approver identity from the existing
verified role tokens before these controls can be used to deploy anything.

## Implementation tasks

- [x] Add typed release-manifest and release-plan records.
- [x] Require a full model revision, SHA-256 artifact/image/config/evaluation digests,
  a non-empty license and source commit, and `tensor_parallel_size=1`.
- [x] Refuse deterministic evaluation failures and changed report revision.
- [x] Verify plan digests and reject stale champion or candidate manifests.
- [x] Add SQLite plan/approval persistence and reject self-approval or repeated approval.
- [x] Add tests for passing manifests, failure gates, stale inputs, tampering, approval,
  unpinned images, and multi-GPU configuration.
- [ ] Add authenticated API integration that reads the sanitized MLflow run and
  derives approver identity from a verified signed token.
- [ ] Add a bounded host-side sequential deployment/rollback command with no Docker
  socket in the gateway container.
- [ ] Validate the real release and rollback on the authorized single L4.

## Validation

- Focused local tests before the review follow-up: 7 passed; 8 passed after adding
  the review regression cases.
- Ruff on the new implementation and tests: passed.
- Python bytecode compilation and `git diff --check`: passed.
- Full `make verify`: Ruff and 123 tests passed, 2 skipped; dependency audit reported
  no known vulnerabilities. GPU Compose, observability, benchmark, evaluation, and
  CUDA static/dry-run validation passed without starting services or making model
  requests.
- The initial test run exposed a fixture mismatch between a champion revision and its
  report; the fixture now creates matching report metadata.
- The first lint run found import ordering; Ruff fixed it, and the rerun passed.
- No GPU service or cloud operation was started.

## Security and financial considerations

The record keeps prompts and completions out of its schema. Candidate manifests
record only artifact/evaluation digests and serving metadata. The SQLite helper is not
an identity provider: its approver string is caller-supplied until authenticated API
integration is implemented. Do not use this helper alone as deployment authorization.
All work is local and non-billable.

## Evidence and outstanding work

The focused tests prove digest and state checks only. They do not prove that model
artifacts match the recorded digest, that an MLflow report was created by the trusted
evaluator, that vLLM can load the candidate, or that rollback works. Those require
additional code and later authorized L4 execution within the $25 ceiling.

## Acceptance status

**Local manifest and approval primitives implemented and unit-tested. Authenticated
release integration and all live deployment criteria remain outstanding.**

## Review follow-up

Static review exposed two state-integrity gaps. New SQLite records now require a
pending status and a null approver, leaving approval state changes to `approve()`.
The manifest reads evaluation report bytes once and uses that exact snapshot for both
gate checks and the recorded digest. New regression tests cover mutated approval
fields and an evaluation file overwritten after its read. Ruff and all 8 focused tests
passed locally. PR CI on the updated, restacked head is still required.
