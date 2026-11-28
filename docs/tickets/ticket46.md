# Ticket 46 — Prepare single-L4 GPU observability

## Objective

Add a static, private-by-default metrics and trace configuration to the standalone
single-GPU Compose profile. Preserve the local observability stack and keep all GPU
runtime claims unverified until an approved L4 execution.

## Current state

PR [#46](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/46) is open against PR #45 at head `2945887`. Run `45987574123` passed Python, manifests, supply-chain, and the new `gpu-observability` job. Its inherited `local-e2e` job failed in the existing CPU `demo-capacity` script, the same failure seen on PR #45. Static observability validation passed.

The single-GPU profile had vLLM and gateway metrics endpoints but no Prometheus
scrapes, GPU exporter, host exporter, alert routing, Grafana dashboard, or trace
collector. The old GPU dashboard used DCGM names with outdated units and an older
unprefixed vLLM metric.

## Research and decisions

- Pin DCGM Exporter 4.9.0 paired with its tested DCGM 4.7.0 image, using the image
  manifest digest. Collect ordinary utilization, framebuffer, temperature, power,
  clocks, and XID fields. Do not enable profiling fields or `SYS_ADMIN`.
- Use Prometheus, Grafana, Alertmanager, Node Exporter, Redis Exporter, Tempo, and OpenTelemetry
  Collector Contrib at release versions reviewed from their official release pages;
  record the registry manifest digests and recheck them before the paid run.
- Use the 4.9 DCGM ratio and byte units and current vLLM V1 `vllm:` metric names.
- Use Tempo 3 monolithic local storage for the lab. The existing CPU stack uses a
  separate Tempo 2.7 config; its old `ingester` and `compactor` blocks cannot be
  copied into Tempo 3.
- Keep Prometheus, Grafana, and Alertmanager host ports bound to loopback. Keep DCGM,
  OTel Collector, Tempo, Redis, and vLLM ports internal to Compose. Node Exporter uses
  host PID/network namespaces plus a read-only host-root mount, drops capabilities,
  and has no Docker-published port. The AWS security group must have no inbound rules.
- Use bounded in-memory telemetry stores for this short lab. Restarting a monitor loses
  its data; export evidence before stopping the profile. Alertmanager has a local UI
  receiver only, not an external notification integration.

## Changes

- Added pinned DCGM, Node, and Redis Exporters, Prometheus, Grafana, Alertmanager,
  Tempo, and a profile-specific OpenTelemetry Collector with attribute redaction and
  no stdout span exporter to the single-GPU Compose file.
- Added a focused DCGM collector list, Prometheus scrape targets and lab alert rules,
  Grafana data source/dashboard provisioning, and an inference/GPU dashboard.
- Updated the earlier GPU dashboard for DCGM 4.9 units and current vLLM V1 names.
- Added an explicit required Grafana password placeholder in the sample environment
  and documented private endpoints, ephemeral storage, runtime gates, and limitations.

## Validation

- `make gpu-compose-config` passed using the sample environment. It rendered Compose
  configuration and did not start the profile services.
- `docker compose config --quiet` parsed the profile; native validators parsed Prometheus, Alertmanager, Tempo, and OpenTelemetry configurations; Ruby parsed the Alertmanager and remaining simple YAML files; JSON validation and `git diff --check` passed. The system Python lacks PyYAML, and its Ruby 2.6 YAML parser rejects valid flow-style endpoint lists in Compose/Prometheus, so the format-specific tools are used for those files.
- The pinned Prometheus `promtool check config` and `promtool check rules` passed; it
  found five valid alert rules. The pinned Alertmanager `amtool check-config` passed.
- The pinned Tempo 3.1 image's `-config.verify=true` passed after an initial schema
  error exposed incorrect compaction nesting; the configuration was corrected to use
  the documented nested layout. The pinned OTel Collector Contrib image's `validate`
  command exited successfully against the profile-specific collector configuration.
- Registry manifest digests were read with `docker buildx imagetools inspect`.
  Prometheus, Alertmanager, Tempo, and OTel Collector image layers were then pulled
  locally only to run their configuration validators. No profile service was started.
- No vLLM or DCGM image, model weights, AWS resource, GPU hour, or AWS spend was
  created. A reproducible `make gpu-observability-validate` target and a dedicated
  static GitHub Actions job now validate the pinned configuration schemas. The four non-GPU validation images remain in the local Docker cache.
- Static validators do not prove exporter permissions, series availability, dashboard
  query results, host-gateway reachability, trace propagation, alert triggering, or
  operation during inference. Those remain explicit live acceptance checks.

## Security and financial considerations

Only Grafana, Prometheus, and Alertmanager have published ports, all on `127.0.0.1`.
Node Exporter shares the host network namespace, so the exact EC2 security group must
be checked for zero inbound rules before deployment. The DCGM exporter and vLLM both
receive visibility to the same single L4; this is not device partitioning or tenant
isolation. Prometheus, Grafana, Tempo, and Alertmanager use bounded tmpfs state to
avoid adding persistent storage resources. The stack adds CPU, memory, disk-download,
and GPU telemetry overhead that must be included in the final $25 cost/runtime plan.

## Outstanding work

- PR #45's stale capacity-mode assertion was fixed; all four required checks passed on
  head `31348c3` in CI run `45990929878`, including the queued-request path. PR #45
  remains open for review.
- PR #46 is open and rebased onto the passing PR #45 base. The new head passed all
  five required checks in run `45992409372`; live L4 behavior remains unverified.
- Recheck registry digests and DCGM/vLLM compatibility immediately before launch.
- On the approved L4, confirm GPU visibility in DCGM Exporter, Node Exporter host
  samples, every Prometheus target, actual GPU/vLLM series, Grafana panels, alert
  delivery to the local Alertmanager UI, trace presence, and evidence export.
- Add thresholds only after observing real baseline behavior; current thresholds are
  lab-only early warnings.

## Acceptance status

**Static preparation only; live GPU observability acceptance is incomplete. No GPU
service was started. The validator images are the only images pulled during this work.**
