# Ticket #52 — Store GPU evaluation evidence in private MLflow

## Objective

Connect the single-GPU evaluation path to an MLflow server on the EC2 host. Keep the
existing CPU ONNX registry and release flow intact. Store model revision and
evaluation provenance plus the sanitized report; never send prompts or completions to
MLflow.

## Starting state

- PR #51 defines sequential LLM release and rollback, but the single-GPU Compose file
  had no MLflow service and the evaluation runner kept its report outside the registry.
- The default laptop MLflow service is not reachable from EC2.
- The GPU is not available yet: applied On-Demand G/VT quota is zero. This package
  must remain testable without AWS, model downloads, or a GPU.

## Research and design

MLflow's tracking server stores run metadata in a backend store and files in an
artifact store. The lab uses SQLite and a named local artifact volume on the encrypted
root disk, with MLflow's artifact-serving endpoint enabled. The server is part of the
private Compose network; its optional host port binds to loopback for operator access
through Systems Manager forwarding. Model weights remain in the pinned Hugging Face
cache. Production should use durable, access-controlled storage and a more robust
metadata database.

The evaluator publishes only the suite identifier and digest, model name and pinned
revision, aggregate pass/fail metrics, a content-policy tag, and the sanitized JSON
report. A configured MLflow failure makes the evaluation command fail rather than
silently losing evidence.

## Implementation tasks

- [x] Add the private MLflow server and persistent named volume to the GPU Compose
  profile; expose its host interface on loopback only.
- [x] Add an opt-in one-shot evaluator Compose service that waits for vLLM and MLflow
  health checks.
- [x] Add optional MLflow publication to the evaluator without logging prompt or
  completion text.
- [x] Add a regression test with a fake MLflow client and assert that the artifact is
  the sanitized report.
- [x] Document the command, storage limits, loopback access, and evidence export.
- [ ] Validate on the authorized L4 host after quota approval; exercise publication,
  review, and evidence export before teardown.

## Validation

Local static validation passed: six focused tests, Ruff, Python bytecode compilation,
`make gpu-compose-config`, and `git diff --check`. Tests use a fake MLflow client; no
container was started. CI validates the code and Compose configuration only. It does
not contact MLflow or send requests to vLLM.

## Security and cost

The MLflow host port is restricted to `127.0.0.1`; the AWS security group remains
without inbound rules. The MLflow volume may contain evaluation metadata and must be
exported and then removed during the authorized lab teardown. No credentials or raw
prompts belong in runs. This service adds small CPU and disk use but no AWS service;
the 16-GiB host capacity must still be measured during the bounded GPU batch. No cloud
resource, GPU hour, or spend is part of this PR.

## Outstanding work

- Verify actual server and artifact-upload behavior with the pinned MLflow version on
  the L4 Compose host.
- Export the run artifact before destroying the temporary volume.
- Connect approved release-plan creation and independent approval to the recorded
  evaluation digest in a later package.

## Acceptance status

**Static/local implementation only.** No MLflow container, vLLM service, model, AWS
resource, or GPU has been started by this ticket.
