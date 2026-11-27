# Ticket 45 — Add the isolated single-L4 Compose deployment profile

## Objective

Make the existing gateway and vLLM adapter usable from a standalone single-GPU EC2
Compose stack without changing the local CPU ONNX default or the future EKS contract.

## Current state

The repository had a working local Compose stack for CPU ONNX, a vLLM HTTP adapter,
and a Kubernetes values file, but no standalone EC2 Compose deployment. The gateway
catalog always routed `chat-default` to ONNX model IDs, so setting a vLLM URL alone
could not select the matching served model name. Its `/healthz` response always said
local CPU ONNX and did not check the upstream model server.

## Changes

- Added an opt-in `INFERENCE_VLLM_URL` catalog path that creates exactly one
  `chat-default` target, uses the configured vLLM model alias, and leaves the
  environment-unset ONNX model and weighted targets intact.
- Added a standalone Compose file for one vLLM service with a reservation for one GPU,
  two gateway replicas, and shared Redis. vLLM and Redis have no host-published ports;
  the gateways bind to loopback only.
- Added a sample environment file with the previously researched immutable image
  digest and Qwen model revision, both marked provisional pending date-of-run checks.
- Added dynamic readiness checks for the selected model backend and shared capacity
  store. The response states the selected runtime; health failure returns HTTP 503.
- Added `make gpu-compose-config` to `make verify` and documented the new profile,
  volume behavior, auth setup, and limitations.

## Validation

- GPU Compose file parses using the sample environment file.
- Ruff passes for changed Python files.
- Unit tests cover the unchanged ONNX default, opt-in vLLM target/model alias, and
  not-ready behavior when the vLLM backend is unhealthy.
- API readiness test covers the existing ONNX mode.
- `make VENV=<existing-project-virtualenv-path> verify` passed on this head: Ruff,
  76 tests (one existing Starlette deprecation warning), pip-audit found no known
  vulnerabilities, and both base and GPU Compose configuration checks passed.
- `git diff --check` passed.
- No GPU image was pulled and no vLLM container or AWS resource was started.

## Security and financial considerations

The app ports bind to `127.0.0.1`; they should be reached through Session Manager port
forwarding. vLLM and Redis stay on the private Compose network. The Docker Compose
profile allows outbound model retrieval through the host network and AWS security
group; no public inbound rule is added. The Compose project is designed for one
accelerator. Redis counters remain logical admission controls, not physical GPU
partitioning, scheduling, or tenant isolation. The $25 AWS budget and exact-plan
approval gates remain unchanged.

## Outstanding work

- PR #45 was opened at `0a16844` against PR #44; its GitHub checks are pending.
- Recheck the pinned container digest, NVIDIA driver/runtime compatibility, and model
  revision, license, and artifact hash before any paid run.
- Add DCGM/Node Exporter and a minimal GPU Prometheus configuration in a separate
  reviewed package; do not claim observability is complete yet.
- Validate manual inference and stream accounting on a real L4 before claiming the
  gateway integration acceptance criteria.
