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
- Explain GPU-local video RAM and bandwidth, model registry versus artifact storage,
  cost per million input/output tokens, error budgets, fault isolation, and the real
  local Redis incident without upgrading it to a GPU or production claim.
- Include troubleshooting steps, project file locations, official sources, and a
  glossary.
- Link the handbook from `docs/README.md` and update project status and evidence.

## Acceptance criteria

- [x] Handbook covers the major concepts in simple English.
- [x] Claims label planned and local evidence accurately; no GPU result is invented.
- [x] Relative links in the handbook and docs index resolve.
- [x] `git diff --check` passes.
- [x] Previous handbook head `34c4a44` passed all six required jobs in run
  `46112594557`.
- [x] Concept-coverage follow-up head `5d812ae` passed all six required jobs in run
  `46122060966`.
- [ ] Human review is complete; PR remains unmerged until authorized.

## Validation and evidence

- `git diff --check` passed.
- A local relative-link check passed for the handbook and documentation index.
- Previous head `34c4a44` passed six checks in run `46112594557`; concept-coverage
  follow-up head `5d812ae` passed six in `46122060966`.
- Prior PR #58 evidence: run `46068015904`, all six checks passed. This is local CPU
  Compose validation only and is not evidence that this handbook's CI has passed.
- No GPU, AWS, model download, benchmark, or cloud spending occurred.

## Limitations and next steps

The text is an educational reference, not a substitute for the remaining hardware
experiments. Version-sensitive instructions must be refreshed before the approved GPU
batch. Human review remains outstanding. After PR #58 changes its base, retarget this
stacked PR and resolve any resulting review feedback.

## Rebase follow-up — 2026-11-28

The handbook branch was rebased from former PR #58 head `351f164` onto updated PR #58
head `59925fd`. The shared execution journal had a conflict because the predecessor
now includes the rebase and CI-failure history; both the updated PR #57/58 records and
the handbook work record were retained. The documentation links and `git diff --check`
pass. This PR still needs a fresh CI run and review. No AWS, GPU, model download, or
cloud spend occurred.

## Concept-coverage follow-up — 2026-11-28

An audit against the requested learning topics found that the handbook explained most
of the GPU and reliability behavior but did not name several terms directly. Added
plain-English definitions for VRAM and memory bandwidth, explained the boundary
between an MLflow tracking record, a model registry, artifact storage, and the live
model process, and added cost-per-million-input/output-token formulas. Expanded the
explanations of concurrency, SLO error budgets, fault isolation, and the actual local
Redis incident. These are concept and repository explanations; no runtime behavior or
new GPU evidence is claimed. `git diff --check` passed. Updated head `5d812ae` passed
all six jobs in run `46122060966`, including routine local E2E. No additional manual
clean-room run occurred.
