# Ticket 70: align the architecture with pinned GPU software candidates

## Objective

Make the architecture describe the current non-GPU preparation accurately. The host,
container, PyTorch, vLLM, and model inputs now have pinned, dated candidates. The
document must not describe them as unpinned, and must not suggest that a pin proves
the stack works on an NVIDIA L4.

## Current state

PR #69 prior head `81c09df` passed all six jobs in run `46115952390`; the current
restacked head `f21d61a` needs fresh CI. PR #70 previous head `e5af488` passed all six
required jobs in run `46116077981`, including local E2E; the current local head
`56bd866` is rebased onto PR #69 head `f21d61a` and is not yet published. No review
decision is recorded. The latest recorded applied G/VT quota is zero, and no GPU or
AWS resource has been created for this lab.

## Research and architecture

The dated candidate versions and artifact digests are recorded in
`docs/gpu-lab/RESEARCH_NOTES.md`, Ansible defaults, the standalone Compose profile,
and the GPU batch runbook. The architecture now summarizes Ubuntu 24.04, NVIDIA
driver 580.196.11, CUDA Toolkit 13.0.3, NVIDIA Container Toolkit 1.20.2, Docker
29.9.3/Compose 5.8.0, standalone PyTorch 2.14.0+cu130, the vLLM v0.34.0 AMD64
image digest, and the pinned Qwen 1.5B model revision. Each is explicitly called a
candidate pending a fresh review and real host validation.

## Acceptance criteria

- [x] Architecture no longer says the researched versions are unpinned.
- [x] The architecture distinguishes source pins and metadata research from real
  driver installation, CUDA computation, container access, and inference evidence.
- [x] The L4 remains labeled as the required validation boundary.
- [x] Local documentation links and whitespace validation pass.
- [x] The prior PR #70 head passed its required workflow.
- [x] Rebase PR #70 on current PR #69 head `f21d61a`.
- [ ] Publish the rebased PR #70 and pass current required CI.

## Commands and validation

`git diff --check` passed. A relative-link scan over the seven changed Markdown files
found no missing targets. Prior PR #70 head `e5af488` passed six required jobs in run `46116077981`, including local E2E. That result does not validate the rebased head `56bd866`, which needs fresh CI. No separate clean-room rerun was performed; the documentation change
does not modify implementation, and the PR workflow owns its one local cycle.

## Issues, alternatives, and limitations

The previous architecture paragraph was stale: it said exact versions were unpinned
even though the later host manifest and research notes pinned candidate versions.
The correction adds a compact source-of-truth summary and states the remaining
uncertainty. It does not claim that NVIDIA/CUDA, Docker GPU access, PyTorch, vLLM, or
model inference work on an L4.

The versions must be checked again immediately before any authorized GPU session.
Quota approval alone is not spending authorization. The shared Terraform backend,
budget recipient, exact saved plan, aggregate estimate within $25, runtime expiry,
and teardown checks remain launch gates.

## Security and cost

Documentation-only change. No credentials, state, plans, or private information were
added. No AWS calls, downloads, infrastructure changes, GPU runtime, or cost.

## Evidence and outstanding work

Prior evidence includes successful PR #70 run `46116077981` and local diff/link checks. Those establish documentation consistency only, not runtime compatibility. The new rebased head needs CI and human review; merge remains subject to authorization. The designated clean-room record at source `49076a5`, run `46114955314`, validates local CPU only.
