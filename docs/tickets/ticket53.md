# Ticket #53 — Lock gateway container build inputs

## Objective

Make the repository's Python gateway image repeatable across the local Apple Silicon
workstation and the Linux x86-64 EC2 host. Preserve the CPU application path and keep
the L4 runtime image separate.

## Starting state

- `gateway/Dockerfile` used the floating `python:3.12-slim` tag.
- `requirements-container.txt` listed version ranges and was installed without hashes.
- The same gateway image is used by the CPU Compose stack, GPU gateways, evaluator,
  and MLflow service. A drifting dependency resolution could affect both paths.
- The isolated Python 3.12 GPU lab already has a separate Linux x86-64 CUDA wheel
  lock; it must not be mixed with vLLM's container-owned CUDA libraries.

## Research and design

Use the multi-platform OCI index digest for the official Python 3.12 slim Bookworm
image so Docker can select amd64 or arm64 while retaining the same base image
identity. Keep human-maintained compatible version ranges in
`requirements-container.txt`, and generate a separate universal hash lock for the
container build. Install with pip's `--require-hashes`. A repository validator checks
that each direct input exists in the lock and every resolved package has hashes.

## Implementation tasks

- [x] Pin the official Python base image index digest.
- [x] Generate a universal lock for CPython-compatible runtime dependencies with
  SHA-256 hashes.
- [x] Make the Docker build install only the locked file with `--require-hashes`.
- [x] Add a lock coverage check to the local Makefile and CI.
- [x] Document the base image metadata, dependency lock, and platform boundaries.
- [x] Validate the full image build on Linux amd64 CI and the existing CPU workflows.

## Validation

The local checker reports 124 locked packages with hashes. PR #53 was opened at
`https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/53`, commit
`e623b75`, based on PR #52. CI run `46023306230` passed all five required jobs,
including the real Docker image build with the hash lock on Linux amd64. The local
end-to-end job checked the CPU runtime. The OCI metadata query reports amd64 and
arm64 variants and did not download image layers. A local pip-audit check of the
exact lock reported no known vulnerabilities. CI now repeats the lock audit after
the project development environment is installed.

## Security and cost

No credentials or image layers were stored in the repository. The lock uses hashes so
the image build rejects unrecorded package artifacts. CI runs the pinned base image;
the L4 runtime remains the separately pinned vLLM image. No AWS resource, model
download, GPU hour, or cloud spend is part of this ticket.

## Outstanding work

- Confirm Docker can build the same source on the local arm64 workstation; Linux amd64
  CI has passed.
- Recheck the base image digest and dependency advisories before future refreshes.

## Acceptance status

**Static lock and source changes pass all five PR CI jobs, including the Linux amd64
image build and existing CPU end-to-end flow.** No AWS or GPU execution has occurred.
