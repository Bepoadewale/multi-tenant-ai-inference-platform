# Ticket 65 — prepare the bounded Triton and Nsight profiling lab

## Objective

Complete more of the CUDA performance laboratory before L4 quota approval. Add a
reproducible, bounded Triton kernel exercise using the already hash-locked Triton
dependency, and document short Nsight Systems and Nsight Compute procedures. No GPU
runtime, kernel compilation, profiler collection, AWS operation, or spending is part of
this ticket.

## Current state

The repository already contains a CUDA C++ vector-add program and a synchronized
PyTorch matrix/transfer experiment. Its workstation dry-run cannot compile CUDA code
or establish GPU measurements. The standalone PyTorch dependency lock contains Triton
3.8.0. The approved L4 and the availability of profiler performance counters remain
unverified.

## Research and design

- Use Triton from the existing hash-locked PyTorch CUDA environment rather than adding
  a second unpinned install.
- Keep the Triton program small: FP32 vector addition, masked tail elements, explicit
  warm-up, repeated CUDA-event timings, correctness against PyTorch, and one-L4 host
  checks.
- Bound elements, block sizes, repetitions, and wall time. Use a dry-run that does not
  import Torch/Triton or touch a GPU. Store only aggregate results outside the public
  repository with owner-only permissions.
- Use Nsight Systems for one short host/CUDA/kernel timeline. Keep profiler timing
  distinct from normal benchmark timing.
- Treat Nsight Compute as optional. Its replay changes timings and performance-counter
  permissions may be restricted. Record limitations; do not relax driver security.
- Do not install separate profiler packages until the pinned host's toolkit contents,
  compatibility, disk use, cost, and authorization have been checked.

## Implementation tasks

- [x] Add a no-GPU Triton workload plan and parameter bounds.
- [x] Add an L4-only Triton FP32 vector-add experiment with correctness checking,
  synchronized timing, metadata, runtime cap, and private aggregate output.
- [x] Add a host wrapper requiring confirmation and checking IMDSv2 identity and L4
  visibility before loading the CUDA Python environment.
- [x] Add focused tests for plan output, bounds, no-CUDA import behavior, and confirmation
  refusal before metadata access.
- [x] Preserve earlier evidence by writing unique private result files and refusing
  to overwrite an existing path.
- [x] Document Nsight Systems and optional Nsight Compute commands and their limits in
  the CUDA lab, manual reproduction guide, and GPU batch runbook.
- [x] Record current official NVIDIA and Triton references and the version decision.
- [x] Pass focused local tests, lint, the repository validation suite, shell parsing,
  dry-run/Make previews, and diff checks.
- [x] Pass PR checks on the preceding candidate (all six jobs in runs
  `46085794180` and `46086647676`).
- [x] Publish the final kernel declaration fix; all six checks passed on code commit
  `39ecace` in run `46087597029`, including the workflow local E2E job.
- [ ] Obtain human review; do not merge without owner authorization.
- [ ] Complete the single integrated clean-room reproduction after the stack settles;
  keep this PR draft until that project review gate is satisfied.

## Acceptance criteria

- Local plan works without a CUDA or Triton installation and reports zero GPU/network
  operations.
- Invalid workload sizes, block sizes, repetitions, and run times are rejected.
- The confirmed host wrapper validates exactly one L4 before calling the pinned
  Python environment and never exceeds its fixed timeout.
- Real kernel results, profiler availability, counters, and output remain marked
  pending until evidence is collected on the approved L4.
- Nsight and normal timing are explicitly separated, and no profiler permission
  failure leads to weaker driver settings.

## Validation

The initial candidate's focused Triton suite passed 10 tests and its required PR
workflow passed all six jobs in run `46085794180`, including local E2E. Follow-up
commit `deaafd3` passed all six jobs, including local E2E, in run `46086647676`.
During review of the executable path, the JIT kernel was moved from a nested closure
to a top-level Triton module. Triton compiles JIT functions by inspecting their
function source, so keeping the function at module scope avoids relying on a nested
closure being understood by that source parser. The module is imported only after
the host has verified a single L4; workstation dry-runs still do not import Torch or
Triton. This source-layout correction has 11 focused local tests, and `make verify`
passes 187 tests (2 skipped), the dependency audit, Compose checks, GPU observability
configuration validation, and existing benchmark/evaluation/CUDA planning targets.
`bash -n`, the Triton dry-run, the host-wrapper Make preview, Python compilation,
relative-link checks, and `git diff --check` pass. The final code commit `39ecace` passed all six required jobs in run `46087597029`. A documentation-only follow-up records release-backlog status; its check results are
tracked on the current PR head. All these checks validate local preparation, not a CUDA kernel or profiler
on an L4.

## Security and financial considerations

The dry-run does not import GPU libraries or make network requests. Host execution is
behind a separate confirmation, exact account/instance/type/region guard, visible-L4
check, fixed runtime limit, and private output path. Profiler reports can expose
system activity, so retain them outside public Git. No cloud resource, model, image,
or profiler package is downloaded by this ticket. It uses zero AWS budget and does
not grant approval for the later GPU batch.

## Evidence and outstanding work

Local evidence proves only parameter validation and dry-run safety. The L4 kernel,
Nsight capture, compatibility, performance counters, and measured performance remain
unproven until the quota, exact-plan, and batch-authorization gates pass.

## Rebase and evidence-preservation follow-up — 2026-11-28

This PR was rebased onto PR #64's current code head `06f1a11`. Parent PRs #59–#63
passed all six required jobs on current heads in runs `46112594557`, `46112810861`,
`46113035567`, `46113162785`, and `46113289587`. PR #64 passed all six jobs,
including local E2E, in run `46114151883`. PR #65 remains local and needs fresh CI on
the updated base.

Review found that repeated Triton runs used `O_TRUNC` on a fixed default result path,
which could erase earlier benchmark evidence. The default now generates a timestamped
filename; explicit paths use exclusive creation and fail if the file already exists.
A new test verifies existing evidence remains unchanged. Twelve focused Triton tests,
Ruff, shell syntax, dry-run, and whitespace checks pass. Full `make verify` passes 193
tests (2 skipped), dependency audit with no known vulnerabilities, Compose and
monitoring checks, and all benchmark/evaluation/CUDA/Triton dry runs. The first full
test collection in this worktree lacked ignored ONNX fixtures; after generating them
locally, the rerun passed. No L4 kernel, profiler, AWS operation, or spend occurred.

The current documentation diff also passes a check of 114 relative Markdown links
across 13 changed Markdown files, with no unresolved rebase markers and clean
whitespace validation.
