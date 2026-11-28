# Ticket 62 — GPU benchmark and incident-response reports

## Objective

Prepare useful benchmark-report and incident-response documents before quota
approval, while leaving all L4 measurements and GPU incident claims for real runs.

## Current state

The repository has bounded direct-vLLM and authenticated-gateway benchmark tools,
one local Redis outage incident report, and a consolidated GPU batch runbook. The
benchmark report and operator decision paths have not been collected in one place.

## Design

- Keep a report template with no invented metrics and explicit evidence classes.
- Explain latency, throughput, concurrency, GPU/host signals, cost formulas, and
  benchmark limitations before listing result tables.
- Add safe diagnostic branches for host GPU discovery, Docker, CUDA/PyTorch, model
  readiness, memory pressure, tenant admission, Redis, telemetry, disk, and recovery.
- Distinguish the already-executed local CI Redis incident from future L4 drills.

## Acceptance criteria

- [x] Add `BENCHMARK_REPORT.md` with workload design, metadata, result/evidence
  tables, analysis questions, and correct cost formulas.
- [x] Add `INCIDENT_RESPONSE_HANDBOOK.md` with bounded investigation and recovery
  procedures, fault boundaries, and an incident report template.
- [x] Do not claim unobserved GPU performance, alerts, or incidents.
- [x] Link from documentation index and persistent status records.
- [x] Check 119 Markdown links across ten changed documentation files; every local
  target exists. `git diff --check` passed.
- [ ] Complete PR CI and human review.

## Validation

Documentation-only changes do not require another manual clean-room cycle. No test,
AWS mutation, model download, GPU request, or paid resource is part of this package.

## Security and financial considerations

The documents forbid collecting prompt/completion content, credentials, raw Terraform
state, or unreviewed environment output in public evidence. The AWS cap remains $25;
the procedures stop on quota, budget, or safety blockers.

## Outstanding work

- Real benchmark measurements, charts, and cost evidence require an approved L4 run.
- GPU fault-injection reports require the real host and an approved batch window.
- Human review and merge remain required.

## Rebase record — 2026-11-28

PR #62 was rebased onto PR #61 head `bfd3449`. The prior validation and CI record
belongs to the old stack; link and whitespace checks must be repeated and fresh PR CI
is required. The rebased set passed `git diff --check` and a local check of 75 relative
Markdown links across nine changed Markdown files. The report continues to use empty
measurement fields rather than inventing GPU outcomes. No AWS/GPU operation or
separate clean-room run occurred.


## 2026-11-28 restack validation

Rebased PR #62 from former PR #61 head `bfd3449` onto refreshed PR #61 head
`1474752`. The benchmark and incident documents were retained, with local link
validation across seven changed Markdown files and `git diff --check` passing. The
benchmark report labels all missing GPU results as not measured; the incident handbook
contains procedures and does not claim incidents that have not occurred. No AWS/GPU
operation or spend occurred. Fresh CI is pending publication.
