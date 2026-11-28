# Ticket 61 — GPU project interview preparation

## Objective

Create the required interview preparation deliverable from the repository's actual
implementation and evidence, while clearly labeling GPU work that remains planned.

## Current state

The repository already has a short portfolio interview guide, but it does not meet
the single-L4 goal's requirement for at least 100 substantive questions and answers
organized across the project's engineering disciplines.

## Research and design

Use implementation details in the gateway, Redis Lua admission scripts, vLLM adapter,
single-GPU Compose profile, Terraform root, benchmark preparation, model release
controls, and the recorded local Redis outage. Treat GPU architecture and model
runtime material as technical background unless supported by real execution evidence.

## Implementation

- [x] Add at least 100 substantive Q&A items across 18 technical areas.
- [x] Explain core concepts, design trade-offs, failure modes, and project-specific
  evidence in plain English.
- [x] Include truthful STAR examples based on the recorded Redis outage and prepared
  release/cost decisions.
- [x] Link the guide from the documentation index.
- [x] Update project status and execution records without changing AWS state.

## Acceptance criteria

- A reader can distinguish local execution, static preparation, and real L4 evidence.
- Answers align with current source and documented limits.
- At least 100 questions cover Linux, AWS, GPU, CUDA, Docker, Python, distributed
  systems, vLLM, model serving, LLMOps/MLOps, observability, reliability, security,
  performance, FinOps, incidents, and system design.
- No AWS request, plan apply, GPU call, or billable resource is created by this ticket.

## Validation and evidence

This is documentation-only. A local structural check confirmed 106 contiguous
questions and verified 106 Markdown links across the changed documentation files;
all local link targets exist. `git diff --check` passed. A clean-room run is not
applicable. No cloud or GPU evidence is produced.

## Security and financial considerations

The guide contains no credentials, customer content, AWS identifiers, or raw
operational output. It does not authorize AWS spending.

## Outstanding work

- Human review and merge remain required under the PR workflow.
- The final interview package must be updated with actual GPU measurements, incidents,
  and rollback results after those phases run.

## Final status

Documentation implementation complete; PR CI and human review pending.

## Rebase validation — 2026-11-28

PR #61 was rebased onto the updated PR #60 head `9a8bd28`; its prior passing run
`46075816404` belongs to the previous stack and does not validate this head. The
guide remains 106 questions across 18 topics. Structural and changed-file link checks
are being rerun before publishing; fresh PR CI is required. No AWS, GPU, model, or
clean-room operation occurred.


## 2026-11-28 restack validation

PR #61 was rebased from former PR #60 head `9a8bd28` onto refreshed PR #60 head
`9fc23f2`. It contains 106 numbered questions spanning the required technical
areas, plus follow-up questions and examples grounded only in this repository's
actual local/static evidence. Relative links in six changed Markdown files passed;
`git diff --check` passed. This documentation check does not prove GPU experience.
No AWS or GPU operation occurred. Fresh CI is pending publication.
