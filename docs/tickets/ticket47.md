# Ticket 47 — Prepare reproducible single-L4 serving benchmarks

## Objective

Prepare a bounded benchmark batch that can run after an approved single-L4 deployment,
using vLLM's official serving benchmark, real run metadata, and output stored outside
public Git. Do not report fabricated performance measurements.

## Current state

The repository's current `benchmarks/load_test.py` is marked `local-mock`, sends a fixed
local token, and gathers all requests concurrently regardless of the `--concurrency`
argument. It remains useful only for its existing local mock workflow. It is not the
GPU benchmark harness.

## Research and decisions

- Use the vLLM 0.34.0 official `vllm bench serve` interface with OpenAI chat endpoint,
  synthetic token lengths, concurrency cap, warm-up, aggregate JSON results, and
  TTFT/TPOT/ITL/end-to-end percentile reporting.
- Use deterministic random workloads so no real prompts or customer data are needed.
- Keep the client on the private Compose network and grant it no GPU reservation.
- Save aggregate result JSON only; do not enable detailed per-request response capture.
- Stop at the first failed case and preserve partial files outside the repository.
- Keep short-prompt concurrency 16 behind an explicit flag until lower levels show
  sufficient GPU memory margin.

## Changes

- Added a versioned JSON workload matrix for short, medium, and long-context cases.
- Added a runner that checks context plus a chat-template safety margin, verifies the
  actual IMDSv2 region/type against the allowed `us-east-1` single-GPU G6 configuration,
  and checks for an NVIDIA L4 before execution,
  then records commit, GPU/driver/memory, model revision, container and framework
  versions, vLLM maximum sequence/context/memory settings, workload shape, concurrency,
  and repetition.
- Added a Compose benchmark-client profile. It uses the pinned vLLM image but requests
  no GPU; output is bind-mounted to an explicitly chosen host path.
- Added a local dry-run target and linked it into `make verify`.
- Added a 120-minute batch runtime cap and 10-minute per-command timeout by default.
- Centralized the benchmark container name so timeout and interruption cleanup target
  the exact named container for that workload repetition.
- Added a regression test that verifies the runner command and cleanup name agree for
  a non-first repetition.
- Added a non-cloud GitHub Actions step that parses the GPU Compose profile and runs
  the benchmark dry-run even if the separate long local E2E job fails.
- Documented that direct vLLM results do not include gateway overhead, Redis quotas,
  or tenant behavior; an authenticated gateway benchmark remains a separate task.

## Validation

- `make gpu-benchmark-plan` produced 11 default workload cases and 33 commands across
  three repetitions. With `--allow-concurrency-16`, it produced 12 cases and 36
  commands.
- The generated commands use `vllm bench serve`, have valid input/output/context
  bounds, save aggregate results, do not enable response-level detailed output, and
  mount an output directory outside the repository.
- `python3.12 -m py_compile`, Ruff for the new runner, `make gpu-compose-config`, and
  `git diff --check` passed.
- The targeted cleanup-name regression test passed with an isolated Python 3.12 pytest
  invocation; Ruff and bytecode compilation passed for the runner and test. The
  workstation's Python 3.12 environment does not include pytest, so the test used
  `uvx` without changing the repository environment.
- No Docker profile service, model, benchmark request, AWS resource, or GPU was used.
- After rebasing the candidate onto PR #46 head `6df97e7`, `make gpu-benchmark-plan`
  again produced 11 cases and 33 commands with the 120-minute batch and 600-second
  per-command bounds. One regression test passed; Ruff, `make gpu-compose-config`, and
  `git diff --check` passed. Make echoes the command before its JSON output, so the
  JSON was parsed from the output after skipping that first echoed line.

## Security and financial considerations

The runner refuses a non-L4 GPU, regions other than `us-east-1`, and instance types
outside `g6.xlarge`/`g6.2xlarge`. This is an execution guard, not cloud authorization.
Aggregate benchmark JSON and the metadata file stay outside public Git by default.
The 33-run plan is only a proposed workload; estimate its runtime during the approved
batch and stop early if required evidence, time, or the $25 total budget is at risk.

## Outstanding work

- PR #47 is open stacked on PR #46; pass its CI checks and review. PR #46's rebased
  CI was still running when PR #47 was opened.
- Recheck the pinned vLLM image and CLI flags against the exact runtime inside the
  benchmark container immediately before execution.
- Add a separate authenticated gateway benchmark for end-to-end overhead and
  multi-tenant quota behavior.
- Run the matrix on real L4 hardware, retain genuine raw results, plot measurements,
  investigate outliers, and calculate complete request/token costs.

## Troubleshooting update

Static review found that emergency cleanup constructed the container name from the
overall matrix index, while Docker Compose names it from the workload repetition. The
names diverged after the first run, so a timed-out later benchmark could leave its
container running. The runner now uses one shared name helper for both `docker compose
run --name` and timeout/interruption cleanup. The regression check verifies repetition
3, which catches the mismatch. No container was started during this investigation.

## Acceptance status

**Static preparation only. No GPU benchmark evidence exists.**
