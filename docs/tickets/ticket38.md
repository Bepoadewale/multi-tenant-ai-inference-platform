# Ticket 38 — Verify the pinned GPU model artifact

## Objective

Add a small, reproducible check for the exact Qwen model file researched in ticket
37. The check validates the size and SHA-256 of a file already present in the
Hugging Face Hub cache. It must not download model data, require third-party Python
packages, or print a private cache path.

## Current state

The compatibility research in ticket 37 identifies Qwen/Qwen2.5-1.5B-Instruct at
revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. The model metadata reports
`model.safetensors` as 3,087,467,144 bytes with LFS SHA-256
`dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`. No model
weights have been downloaded in this project.

## Research and design

The Hugging Face Hub cache stores repository snapshots under a path of the form
`models--<organization>--<repository>/snapshots/<revision>/`; snapshot files can
refer to content-addressed blobs through symlinks. The verifier follows the snapshot
entry and reads it in bounded 8 MiB chunks, so checking a multi-gigabyte model does
not require keeping the whole file in memory. The helper only reads the local file;
it does not contact Hugging Face or initiate a download.

Official references:

- [Hugging Face Hub cache management](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache)
- [Hugging Face Hub local cache layout](https://huggingface.co/docs/hub/local-cache)
- [Pinned Qwen model revision](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306)

## Implementation

- `scripts/verify_gpu_model_artifact.py` fixes the repository, revision, filename,
  expected size, and expected SHA-256 to the researched values.
- The command accepts the Hub cache root (normally `$HF_HOME/hub`), checks the
  expected snapshot file, then verifies its byte count and digest.
- Successful output reports the model identity, revision, filename, size, digest,
  and a `verified` result. It does not reveal the local cache path.
- `gateway/tests/test_gpu_model_artifact.py` covers the snapshot path, a valid small
  fixture, symlink-backed cache entries, mismatched size/digest, and a missing file.

## Acceptance criteria

- [x] A standard-library-only verifier checks the pinned size and SHA-256.
- [x] Cache snapshot symlinks are followed.
- [x] Failure is reported with a nonzero command result and without disclosing the
  absolute cache path.
- [x] Tests demonstrate successful and failing checks on temporary fixtures.
- [ ] Repository-wide local validation and pull-request checks pass.
- [ ] The actual model file is checked during the bounded GPU execution batch after
  quota approval and all cost/authorization gates pass.

## Commands and validation

- `.venv/bin/python -m ruff check scripts/verify_gpu_model_artifact.py gateway/tests/test_gpu_model_artifact.py`
  — passed before the symlink regression test was added.
- `PYTHONPATH=gateway/src .venv/bin/python -m pytest -q gateway/tests/test_gpu_model_artifact.py`
  — five tests passed before the symlink regression test was added.
- `make verify` — passed after the symlink test: Ruff passed, all 66 repository tests
  passed (one existing Starlette deprecation warning), `pip-audit` found no known
  vulnerabilities, and `docker compose config --quiet` passed.
- After adding CLI output-redaction tests, `make verify` passed again: Ruff passed,
  all 68 repository tests passed (one existing Starlette deprecation warning),
  `pip-audit` found no known vulnerabilities after a registry retry, and Compose
  configuration passed.
- `git diff --check` — passed before the final two CLI tests; rerun after this update.
- Initial `ruff ...` shell invocation failed because Ruff is not installed as a
  standalone shell command. Using the repository virtual environment succeeded.
- The PR #37 base checks passed on head `1c1e922` in run `45941524263`. PR #38 head
  `b027a18` is published; manifests, Python, and supply-chain have passed in run
  `45942740229`; local-e2e is still running.

## Security and financial considerations

This helper performs local reads only. It emits no credential or cache-path data and
does not make AWS calls. The actual model download is deferred to the planned bounded
GPU batch; its time and cost remain subject to the $25 project ceiling, instance-hour
limit, approved quota, and teardown controls.

## Evidence and limitations

Unit tests use tiny synthetic files and prove the helper's size/hash/symlink behavior.
They do not verify the 3 GB model artifact, Hugging Face's current remote contents, a
GPU, model loading, or inference. The expected digest is the published LFS metadata
recorded in ticket 37; independent verification against the downloaded model remains
open.

## Outstanding work

- Run `make verify` after the final change and record exact results.
- PR #38 is open based on PR #37. Its latest check run is `45942740229`; local-e2e
  remains pending.
- Wait for all required checks to finish on head `b027a18`.
- Verify the downloaded pinned model file in the authorized GPU execution batch.

## Review follow-up

The CLI now reports sanitized filesystem failures rather than printing exception
text that can reveal the private cache path. The new CLI test simulates a
`PermissionError` containing the full path and checks that neither the cache root nor
snapshot path appears in stderr. Ruff, Python compilation, all 9 focused tests, and
`git diff --check` passed locally. Updated PR CI is required before resolving the
review finding. No model download, AWS call, or GPU was used.
