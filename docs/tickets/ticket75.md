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
- Correct the manual reproduction guide's stale quota note: the owner confirmed
  approval; the latest recorded applied quota is 4.0 vCPUs and request history is
  `CASE_CLOSED`. Other cloud launch gates remain open.
- Refresh the implementation backlog's open-PR inventory using live GitHub metadata,
  including the successful #74 CI result and the pending #75 run.

## Evidence and limitations

The 4,000+ word draft is based on repository source, the proposed architecture, and
recorded official-source research. Its numerical cache example is explicitly
configuration-derived, not a measured L4 result. The document claims no real AWS,
GPU, model-serving, benchmark, or production reliability evidence.

## Validation

The historical PR #75 head `5284057` passed all six required checks in run
`46129296996`, including routine local end-to-end CI; this was not a second designated
project clean-room run. After restacking on current PR #74 head `3cf1eec`, 119 relative
links across ten changed Markdown files resolve and `git diff --check` passes. The
current restacked head is `ad05843` before the validation-record commit and requires
fresh CI. No software behavior changed; no local
clean-room run, AWS operation, image/model download, or GPU execution occurred.

## Outstanding

- Publish this restacked PR with an exact lease and verify fresh CI.
- Continue expanding the final report and manual reproduction guide with measured
  results only after the GPU execution phase.

## Acceptance status

**Documentation checks pass on the rebased local head, but fresh PR CI is pending.**
The handbook remains educational documentation for a system whose real-L4 acceptance
criteria are pending.
