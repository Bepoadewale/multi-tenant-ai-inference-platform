# Ticket 49 — Prepare CUDA and PyTorch performance experiments

## Objective

Prepare bounded, correctly timed CUDA C++ and PyTorch experiments before the
authorized NVIDIA L4 execution window. Local commands and CI must not start GPU work.

## Current state

The repository has no CUDA kernel or GPU performance lab. The workstation is macOS
arm64 and has no NVIDIA tools or CUDA compiler. This package is a static preparation;
the `.cu` file has not been compiled. PR [#49](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/49) is open. All five required jobs passed in run `45998860857` on code head `ce8bbba`.

## Research and decisions

- Use a small vector-add CUDA kernel to teach threads, blocks, grid bounds, and
  adjacent memory access.
- Use PyTorch matrix multiplication to compare CPU FP32 with L4 FP32/FP16/BF16 where
  supported, and compare output against a CPU reference.
- Use CUDA events and explicit synchronization for GPU timing. Do not time only the
  asynchronous kernel launch with the host clock.
- Measure host/device transfers separately from matrix compute. Allocate both the
  pinned source and pinned destination before timed device-to-host transfers.
- Compare each reduced-precision product against an FP32 product of the same rounded
  inputs so input quantization is not confused with multiplication error.
- Keep shapes and repetitions bounded and outputs outside public Git with restrictive
  file permissions.
- Require exactly one NVIDIA L4 and fail rather than silently falling back to CPU.

## Changes

- Added a CUDA C++ vector-add sample with CPU correctness comparison, L4/single-GPU
  checks, warmups, repeated CUDA-event timings, and separate copy timings.
- Added a PyTorch CPU/GPU matrix benchmark with FP32, FP16, supported BF16, correctness
  checks, device/framework metadata, and synchronized event samples.
- Allocate a pinned host destination before the device-to-host timing loop and use an
  asynchronous copy bracketed by CUDA events, with synchronization after the end event.
- Compare reduced-precision output against FP32 multiplication of the same
  precision-rounded inputs, isolating multiply error from input rounding.
- Bounded matrix size, repetitions, and the overall PyTorch run to at most 600 seconds;
  bounded C++ vector size and repetitions too.
- Added a zero-operation dry-run, focused unit tests, Makefile targets, and static CI
  validation. Added a learning-focused README with formulas and command explanations.

## Validation

- `make gpu-cuda-plan` reported sizes 256/512/1024, 3 warmups, 10 repetitions, and
  zero GPU operations.
- Three Python 3.12 tests passed for bounded planning and median/GFLOP arithmetic.
- Ruff, Python bytecode compilation, and `git diff --check` passed.
- The local Apple Silicon workstation has no `nvcc`, NVIDIA driver, or CUDA device, so
  the `.cu` program was not compiled. No CUDA runtime, GPU kernel, or AWS resource was
  used. All five required jobs passed in run `45998860857` on code head `ce8bbba`.

## Security and cost

Dry-run and tests make no network or GPU request. Runtime JSON output is outside the
repository, mode 0600, and contains aggregate timings rather than tensor contents.
The actual GPU command remains behind the project's quota, exact-plan, $25 budget,
runtime, expiry, and teardown gates.

## Outstanding work

- Compile the `.cu` source with the version-pinned Toolkit on Ubuntu 24.04 and run it
  on the actual L4.
- Confirm PyTorch/CUDA compatibility, BF16 support, numerical tolerances, kernel
  correctness, transfer behavior, and reported utilization.
- Collect actual CPU/GPU measurements and profiler evidence; no performance result is
  claimed by the static preparation.

## Review follow-up

Static review found two measurement correctness issues: BF16 output was compared with
an FP32 result from unrounded input, and the device-to-host sample allocated pageable
memory during each timing iteration. Both are corrected in the candidate update. The
workstation has no NVIDIA device, so timing behavior cannot be established locally;
the PR CI and source-level checks validate packaging only, and the actual L4 run must
confirm numerical tolerances and transfer measurements.

## Acceptance status

**Static preparation only. No CUDA computation, GPU benchmark, or performance result
has been recorded.**
