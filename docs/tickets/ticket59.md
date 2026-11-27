# Ticket 59 — add the AI infrastructure learning handbook

## Objective

Create a plain-English technical handbook that explains the concepts and components
behind the planned single-L4 inference platform. The guide must teach the reader how
the components connect, how they can fail, and how to investigate them. It must not
claim that static preparation is proof of live GPU operation.

## Starting state

- Work is on `codex/ai-infrastructure-handbook`, stacked on PR #58 head `351f164`.
- PR #58 head passed all six jobs in run `46068015904`; the corrected local Redis
  failure drill and cross-gateway cancellation drill passed.
- The account has no applied On-Demand G/VT quota. No cloud resources or L4 evidence
  exist. The project AWS ceiling is $25.

## Design and implementation

- Add `docs/gpu-lab/AI_INFRASTRUCTURE_HANDBOOK.md` as a connected explanation of GPU
  computing, NVIDIA driver/CUDA layers, language-model inference, attention and
  key/value cache capacity, vLLM, tenant controls, evaluation and releases,
  observability, performance, cost, reliability, and cloud security.
- Explain single-host and logical tenant limitations, and distinguish background
  distributed-GPU concepts from work performed in this project.
- Include troubleshooting steps, project file locations, official sources, and a
  glossary.
- Link the handbook from `docs/README.md` and update project status and evidence.

## Acceptance criteria

- [x] Handbook covers the major concepts in simple English.
- [x] Claims label planned and local evidence accurately; no GPU result is invented.
- [x] Relative links in the handbook and docs index resolve.
- [x] `git diff --check` passes.
- [ ] PR #59 CI passes.
- [ ] Human review is complete; PR remains unmerged until authorized.

## Validation and evidence

- `git diff --check` passed.
- A local relative-link check passed for the handbook and documentation index.
- Prior PR #58 evidence: run `46068015904`, all six checks passed. This is local CPU
  Compose validation only and is not evidence that this handbook's CI has passed.
- No GPU, AWS, model download, benchmark, or cloud spending occurred.

## Limitations and next steps

The text is an educational reference, not a substitute for the remaining hardware
experiments. Version-sensitive instructions must be refreshed before the approved GPU
batch. CI and human review remain outstanding. After PR #58 changes its base, retarget
this stacked PR and resolve any resulting review feedback.
