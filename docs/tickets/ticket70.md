# Ticket 70: align the architecture with pinned GPU software candidates

## Objective

Make the architecture describe the current non-GPU preparation accurately. The host,
container, PyTorch, vLLM, and model inputs now have pinned, dated candidates. The
document must not describe them as unpinned, and must not suggest that a pin proves
the stack works on an NVIDIA L4.

## Current state

PR #69 is open on branch `codex/gpu-price-refresh`; its head passed all six required
checks, including the workflow's one local end-to-end cycle. The new documentation
change is prepared on top of that branch. The unrelated, user-owned untracked
`uv.lock` remains untouched. The project has no confirmed GPU quota, and no GPU or
AWS resources have been created for this lab.

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
- [ ] The single required PR workflow completes successfully.

## Commands and validation

`git diff --check` passed. A relative-link scan over the seven changed Markdown files
found no missing targets. GitHub required workflow remains pending publication. No
clean-room rerun is planned; the documentation change does not modify implementation,
and the PR workflow owns its one local cycle.

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

Evidence will include the diff, local link/whitespace checks, and the GitHub workflow
run. Those establish documentation consistency only, not runtime compatibility.
Human review and merge remain open.
