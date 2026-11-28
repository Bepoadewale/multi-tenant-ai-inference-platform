# Ticket 75 — AI infrastructure learning handbook

## Objective

Create the requested plain-English handbook that teaches the ideas behind the
single-L4 inference platform while separating general engineering concepts from
what this repository has actually run.

## Current state

The repository has architecture, research, manual reproduction, benchmark, incident,
and interview documents. It did not have the dedicated `AI_INFRASTRUCTURE_HANDBOOK.md`
requested by the goal. The existing AWS/GPU deployment remains unexecuted; the new
handbook labels the architecture as proposed and points readers to current evidence.

## Changes

- Explain GPU/CPU roles, L4 capacity, CUDA/driver/toolkit/container layers, GPU
  parallelism, neural networks, training versus inference, fine-tuning, model/token/
  transformer concepts, KV cache, vLLM scheduling, quantization, serving
  measurements, quotas/Redis, model registry and governance, telemetry, incident
  diagnosis, security, and cost.
- Add diagrams, formulas, comparison tables, a symptom-to-diagnostic table, and a
  layered manual verification sequence.
- Explain NCCL, tensor/pipeline parallelism, multi-node training, and Kubernetes GPU
  scheduling as background only; clearly state they are not implemented here.
- Link the handbook from both the main README and documentation index.
- Add a truthful entry to the evidence manifest and keep its table structure valid.
- Correct the manual reproduction guide's stale quota note: the latest recorded
  applied quota is 4.0 vCPUs, but request history and approval evidence remain
  unresolved, and other cloud gates still block a paid launch.
- Refresh the implementation backlog's open-PR inventory using live GitHub metadata,
  including the successful #74 CI result and the pending #75 run.

## Evidence and limitations

The 4,000+ word draft is based on repository source, the proposed architecture, and
recorded official-source research. Its numerical cache example is explicitly
configuration-derived, not a measured L4 result. The document claims no real AWS,
GPU, model-serving, benchmark, or production reliability evidence.

## Validation

Markdown link/heading validation passed across eight touched documents, and `git diff
--check` passed. Upstream PR #74 head `944b457` passed all six required checks in run
`46128237140`. PR #75 CI and final editorial review remain pending.
No software behavior changed; no local clean-room run, AWS operation, image/model
download, or GPU execution is part of this documentation package.

## Outstanding

- Run the documentation checks and full repository verification.
- Review the rendered Markdown and links.
- Publish this focused PR stacked on the bootstrap guardrail PR and verify final-head
  CI.
- Continue expanding the final report and manual reproduction guide with measured
  results only after the GPU execution phase.

## Acceptance status

**In progress.** The draft exists; local checks and PR CI remain open.
