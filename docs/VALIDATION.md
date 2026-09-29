# Validation

Validation is local-first. Record hardware, runtime, exact command and result for any benchmark; never infer GPU behavior from the deterministic CPU fixture or fabricate validation.

## Bounded sandboxed-agent slice

**Date:** 2026-09-29

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No cloud
account, GPU, Kubernetes cluster, or paid API.

A clean local bootstrap, `make smoke`, and `make demo-sandboxed-agent` passed. The
demo sent a five-minute Ed25519-signed delegated agent identity to `sandbox-control`.
The controller accepted only the `fixture_patch` and `containment_probe` task kinds.
The fixture task ran real unit tests and wrote a patch in a disposable child Docker
container. The containment task attempted outbound HTTP and was blocked by
`network=none`. The live response recorded a non-root UID, read-only root filesystem,
dropped capabilities, no-new-privileges, CPU/memory/PID bounds, absent Docker socket,
and absent host bind mounts. Extra `command` input and an unrecognised task kind were
rejected with `422`; no arbitrary command was executed. Prometheus recorded both task
outcomes, child containers and workspace volumes were absent after each task, and the
metadata-only SQLite audit survived an intentional controller restart.

Static validation passed Ruff, `42 passed` pytest tests, and `docker compose config
--quiet`. A second clean container cycle began after `make clean-local` removed every
project Compose container, volume, local image, generated model, `.local` state, and
virtual environment. It then ran `make install`, `make bootstrap-local`, smoke, the
sandbox demo, Ruff, pytest, Compose configuration validation, and `make clean-local`
again. The post-cleanup absence of child sandbox containers/volumes was verified. This
does not claim gVisor, Firecracker, Kubernetes sandboxing, or general arbitrary-agent-
code execution.

## Narrow edge-adapter slice

**Date:** 2026-09-29

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No cloud
account, GPU, mobile/embedded hardware, or paid API.

`make bootstrap-local`, `make smoke`, and `make demo-edge-adapter` passed against the
live Compose stack. The demo verified two independently running device-agent containers
with distinct Ed25519 device identities registered and heartbeated into the edge
control service's SQLite inventory. The simulated `laptop-high` agent ran a real local
CPU ONNX request; the simulated constrained agent used the existing central gateway
only for public traffic. Restricted and `LOCAL_ONLY` requests with no local model
returned `403` rather than invoking fallback. The inventory survived an intentional
`edge-control` restart, while Prometheus observed registration evidence before that
process-local counter reset.

This slice does not claim signed model packages, desired-state reconciliation, OTA,
offline buffering, physical device behavior, NPU execution, or managed fleet control.
Those belong to the standalone hybrid edge project or production adapters. A final
all-slice clean-room cycle will re-run this adapter with the full flagship story.

Two separate local container recreations were exercised before recording this result.
The second began after `make clean-local` removed the project containers, images,
volumes, `.local`, generated ONNX models, and virtual environment; it rebuilt the
Compose services, initialized fixture models, passed smoke, and reran the edge demo.
Both runs ended in Ruff clean, `41 passed` pytest results, and valid Compose
configuration. This is slice-level reproducibility evidence; the remaining P0 is one
final all-slice clean-room demonstration.

## Developer self-service golden-path slice

**Date:** 2026-09-29

**Source revisions:** `3f26767` (initial implementation) plus the bootstrap/configuration
refresh follow-up on `codex/flagship-developer-self-service`.

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No cloud
account, GPU, paid API, Kubernetes cluster, or external developer portal.

The slice adds `developer-self-service`, a separate FastAPI process and SQLite store.
It is intentionally the narrow request contract a portal or golden-path template would
call, rather than a Backstage replacement. `make demo-self-service` proves all of the
following against the live local stack:

- a signed human `developer.self_service` identity creates a durable, tenant-bound
  `team-search` profile for its assigned `chat-default` alias;
- the returned generated Python client and configuration contain no bearer token,
  tenant override header, Redis credential, runtime credential, or rollout authority;
- supplying the fixture token only at runtime lets that generated client make a real
  request through the gateway to a CPU ONNX target;
- the same tenant/idempotency key replays the same profile, whereas a changed request
  is conflict-protected;
- an unassigned model is denied, another tenant cannot read the profile, and a
  delegated-agent identity cannot create it;
- the profile survives a `developer-self-service` restart; and
- Prometheus observes `inference_gateway_developer_integration_profiles_total` before
  the intentional process restart resets process-local counters.

### Clean-room cycle 1

Starting after `make clean-local`, the following passed:

```console
make install
make bootstrap-local
make smoke
make demo-self-service
make lint
make test
docker compose config --quiet
make clean-local
```

`make test` passed 40 tests; Ruff and Compose configuration passed. Cleanup confirmed
there were no project-labeled containers and no `.local`, `.venv`, or generated model
directory remaining.

### Clean-room cycle 2

After cycle 1 cleanup, the same fresh install/bootstrap/smoke/self-service demo and
static validation sequence passed again. The second generated profile reached real ONNX
inference, exercised the same model/tenant/agent denials and restart recovery, and the
final project-scoped cleanup again left no project containers, `.local`, `.venv`, or
generated models. This validates the slice twice from clean project state; it does not
claim a real Backstage deployment, enterprise identity provider, Kubernetes deployment,
GPU runtime, or cloud-hosted model.

## Flagship integration rule

The evidence below validates the preserved inference core plus the executed model
release and simulated-capacity slices. Each future flagship vertical slice must add its
own commands, external dependencies, success path, failure path and clean-room
evidence before it is listed as executed. The wider integrated flagship demo must be
rerun from clean project state after future slices are connected.

## MLflow registry slice

The first flagship slice was executed locally after the historical inference-core
clean-room evidence below. `make bootstrap-local` started MLflow with a project-scoped
SQLite store and artifacts directory, evaluated two generated ONNX artifacts with
`CPUExecutionProvider`, registered their SHA-256 digests and fixture metrics, and set
`champion` (stable v1) and `candidate` (v2) aliases. `make smoke` checked the MLflow
health and registered model, while `make demo-model-registry` verified the aliases and
recorded digest evidence in `.local/mlflow/registry-evidence.json`.

`make demo-release-control` additionally executed: plan creation from the MLflow
aliases/digest; a denied requester approval; an independent `release.approve` grant;
a Redis-shared 10% canary observed through a second gateway; 100% candidate promotion;
and rollback to the recorded stable MLflow version with live stable-route evidence.
The release store is SQLite-backed and unit tests reject a stale transition.

## Simulated capacity slice

`make demo-capacity` executed the capacity contract through the real local gateway.
Redis atomically accounted for a two-slot `simulated-l40s` pool and per-tenant slot
limits. The scenario proved all of the following:

- a `team-search` request acquired a simulated capacity slot;
- a second concurrent search request was rejected at its tenant capacity limit;
- `team-payments` consumed the other pool slot;
- `team-reporting` waited within the bounded capacity queue and was admitted after a slot released;
- `team-analytics` invoked a model that explicitly permits `CPU_FALLBACK` and returned real ONNX CPU output.

The model policy, pool name, decision, and `simulated_hardware=true` metadata are
reported to the client and Prometheus. `simulated-l40s` is **not** a GPU device,
Kubernetes scheduler result, DCGM metric, or performance measurement.

## Operational-evidence slice

`make demo-operational-evidence` executes a governed canary request, then retrieves
`GET /platform/v1/requests/{request_id}/analysis` with the platform-admin identity.
The evidence record proves all of the following without retaining raw prompt or output:

- the request reached one of the real CPU ONNX targets while the shared canary was active;
- the response/request record carries a real OpenTelemetry trace ID that is queryable
  from Tempo;
- the record captures the active SQLite/Redis release plan and `CANARY` phase;
- the metadata-only record includes token counts, target version, and a Decimal
  calculation from the versioned `local-fixture-2026-09-v1` price fixture;
- the local request SLO is `SATISFIED` for the successful canary-period request;
- a real bounded `chat-timeout-demo` backend failure returns 502, retains its request
  ID and metadata-only record, and evaluates as `VIOLATED` rather than disappearing.

Prometheus was queried for positive
`inference_gateway_estimated_cost_usd_total` and
`inference_gateway_request_slo_evaluations_total{status="VIOLATED"}` values. The cost
and SLO thresholds are explicitly local fixture evidence, not production billing or
production SLO commitments.

## Governed-remediation slice

`make demo-remediation` starts from the healthy local stack and creates a 99% candidate
canary through the existing release-control API. It stops the candidate CPU ONNX runtime
to produce an actual gateway `502` with an `X-Request-ID`, then restores the runtime
before remediation is considered. The separate remediation controller accepts that
metadata-only failed canary request, persists a SQLite incident, creates a SHA-256-bound
rollback plan, denies requester self-approval, accepts a distinct
`remediation.approve` JWT, rechecks exact Redis rollout state and the SQLite release
state, and changes only the canary weights to stable=100/candidate=0.

The demo verifies all of the following:

- a subsequent real request reaches `onnx-stable-v1`;
- the release is `ROLLED_BACK` and the incident is `RESOLVED`;
- the audit timeline contains detection, planning, approval, execution, and verified
  recovery events;
- a restart of `remediation-control` retains the incident and timeline;
- Prometheus scrapes controller incident, plan, action, and verification metrics.

Unit tests additionally prove the cooldown/action budget and stale-plan executor
protection. This local controller has exactly one allowlisted action,
`ROLLBACK_CANARY_TO_STABLE`; it does not execute shell commands or access Docker,
Kubernetes, cloud, model-registry, or tenant-inference credentials.

## Delegated agent-tool governance slice

`make demo-agent-tools` runs the narrow agent authority path against the real local
Compose stack. A five-minute Ed25519 token with `principal_type=agent`, named
delegator, `agent.tools`, `inference.read`, and `remediation.plan` discovers exactly
two HTTP-facade tools: `get_request_evidence` and `plan_canary_rollback`. This is not
an MCP protocol validation; the standalone secure MCP gateway repository remains the
protocol-level reference implementation.

The demo executes and verifies:

- same-tenant, metadata-only request evidence is returned without prompt or completion
  content;
- evidence for a real `team-reporting` request is denied to the `team-search` agent;
- a stopped candidate runtime produces a real failed canary request;
- the agent creates a bounded, durable rollback plan but receives `403` when attempting
  approval or execution;
- distinct remediation-approver and platform-admin identities approve and execute the
  plan; subsequent real ONNX traffic reaches stable v1;
- Prometheus records allowed tool calls, and the agent-tools service restart retains the
  SQLite audit whose arguments are SHA-256 hashes only.

The Compose fixture sets the remediation cooldown to one second so independent local
demos can execute sequentially. The controller default remains 30 seconds when the
environment value is absent; action-budget and cooldown enforcement remain tested.

### Slice clean-room evidence

On 2026-09-28, the delegated-agent path was run twice after project-scoped cleanup.
Each cycle started from absent project containers, network, volumes, `.local`, and
`.venv`; ran `make install`, `make bootstrap-local`, `make smoke`, and
`make demo-agent-tools`; then checked lint/tests/Compose configuration and ran
`make clean-local`. Both final cleanups confirmed no Compose resources with the
`multi-tenant-ai-inference-platform` label and no `.local` or `.venv` remained.
This validates the new slice's clean bootstrap/teardown behavior. The future integrated
flagship clean-room run remains a separate P0 item and must repeat all slices together.

## Governed-remediation clean-room validation

**Date:** 2026-09-28

**Source revision:** `2f7afbd` (implementation); final documentation is committed with
the same slice.

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No cloud
account, paid API, physical GPU, vLLM runtime, or Kubernetes cluster.

### Cycle 1

Starting after `make clean-local`, this full cumulative sequence passed:

```console
make install
make bootstrap-local
make smoke
make demo-local
make demo-overload
make demo-routing
make demo-metering
make demo-observability
make demo-failure
make demo-timeout
make demo-recovery
make demo-model-registry
make demo-release-control
make demo-capacity
make demo-operational-evidence
make demo-remediation
make verify
make clean-local
```

`make verify` passed Ruff, 35 pytest tests, `pip-audit --skip-editable`, and
`docker compose config --quiet`. Post-cleanup checks confirmed that no project Compose
containers, volumes, `.local`, or `.venv` remained.

### Cycle 2

After Cycle 1 cleanup, a second clean bootstrap passed:

```console
make install
make bootstrap-local
make smoke
make demo-local
make demo-release-control
make demo-capacity
make demo-operational-evidence
make demo-remediation
make verify
make clean-local
```

The second run used new project-scoped Redis, MLflow, SQLite, identity, and ONNX
fixture state. It again ended with no project-owned runtime resources, `.local`, or
`.venv`. This validates reproducibility of the cumulative slice without relying on
leftover action-budget state.

## Operational-evidence clean-room validation

**Date:** 2026-09-28

**Source revisions:** `e72c8e8` (implementation) and `a02c154` (initial documentation);
final evidence wording was committed after both cycles.

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No cloud
account, paid API, physical GPU, vLLM runtime, or Kubernetes cluster.

### Cycle 1

Starting from `make clean-local`, the following passed:

```console
make install
make bootstrap-local
make status
make demo-local
make demo-overload
make demo-routing
make demo-metering
make demo-observability
make demo-failure
make demo-timeout
make demo-recovery
make demo-model-registry
make demo-release-control
make demo-capacity
make demo-operational-evidence
make verify
make clean-local
```

`make verify` passed Ruff, 32 pytest tests, `pip-audit --skip-editable`, and
`docker compose config --quiet`. The operational demo observed a real canary trace in
Tempo, positive estimated-cost and violated-SLO metrics in Prometheus, then rolled the
canary back to stable. Cleanup removed only project Compose resources, volumes,
generated models, local identity, MLflow/release state, and virtual environment.

### Cycle 2

After Cycle 1 cleanup, a second clean bootstrap repeated the same command sequence,
including all core/release/capacity demos, `make demo-operational-evidence`,
`make verify`, and `make clean-local`. It passed with the same evidence boundaries.
Post-cleanup verification confirmed no project Compose resources, `.local`, or `.venv`
remained. This is a second clean bootstrap, not a run against cached project state.

### Deterministic-demo follow-up

After CI exposed two timing hazards in the first demo revision (probabilistic candidate
selection and a Prometheus scrape race), the demo was changed to correlate any request
made during the active canary and to poll both evidence metrics with bounded timeouts.
Two additional clean starts on 2026-09-28 then passed
`make install`, `make bootstrap-local`, `make smoke`,
`make demo-operational-evidence`, and `make clean-local`; the first also passed
`make verify`. Both final cleanups confirmed the project left no Compose resources,
`.local`, or `.venv` behind.

## Expanded clean-room validation

**Date:** 2026-09-28

**Source revision:** `37c0da0` (`feat: add shared simulated capacity admission`).

**Environment:** macOS, Docker Desktop, Docker Compose, Python 3.12. No GPU, cloud
account, or paid API. The project-specific `make clean-local` command confirmed an
empty Compose project and absent `.local` state before each cycle and after each final
cleanup.

### Cycle 1

```console
make install
make bootstrap-local
make smoke
make demo-local
make demo-overload
make demo-routing
make demo-metering
make demo-observability
make demo-failure
make demo-timeout
make demo-recovery
make demo-model-registry
make demo-release-control
make demo-capacity
make verify
make clean-local
```

Passed. The stack bootstrapped MLflow, release control, two gateways, Redis, two CPU
ONNX targets, OpenTelemetry Collector, Tempo, Prometheus, and Grafana. All success and
failure demos passed. `make verify` passed Ruff, 27 pytest tests, `pip-audit
--skip-editable`, and `docker compose config --quiet`. Cleanup removed all
project-owned containers, volumes, network, generated identities/models, local MLflow
and release data, and the virtual environment.

### Cycle 2

Cycle 2 began after Cycle 1 cleanup with the exact same commands. It passed the same
stack bootstrap, release, capacity, failure/recovery, and verification evidence; its
final cleanup again left no project Compose resources or `.local` files. This is a
second clean bootstrap proof, not a reused running environment.

## Clean-Room Validation

**Date:** 2026-09-21

**Source revision:** `8d4b6e5` (`docs: record local completion evidence`).

**Environment:** macOS, Docker Desktop Engine 29.0.1, Python 3.12, Docker Compose. No GPU, cloud account, or paid API.
**Services:** two FastAPI gateways, two ONNX Runtime CPU targets, Redis 7.4, OTel Collector 0.120.0, Tempo 2.7.1, Prometheus 3.2.1, Grafana 11.5.1.

### Cycle 1

Starting state was created with `make clean-local`. An unrelated `redis:7.4-alpine` sentinel container was running to test cleanup isolation.

```console
make install
make bootstrap-local
make smoke
make status
make demo-local
make demo-overload
make demo-routing
make demo-metering
make demo-observability
make demo-failure
make demo-timeout
make demo-recovery
make verify
make clean-local
```

All commands passed. The successful path returned real CPU ONNX classifier output and SSE; shared quotas/overload returned 429; routing reached the candidate target; metering excluded raw inputs; Prometheus and Tempo contained generated traffic; unavailable and slow backends returned bounded 502 responses; usage survived a gateway restart. `make verify` passed Ruff, 20 pytest tests, pip-audit, and Compose configuration. Cleanup removed project Compose resources, volumes, generated model, generated identity, and virtual environment. The unrelated sentinel remained running.

### Cycle 2

After cleanup, the project was recreated without using project-owned containers, volumes, models, credentials, or virtual environment:

```console
make install
make bootstrap-local
make smoke
make status
make demo-local
make demo-timeout
make clean-local
```

All commands passed. The second bootstrap returned real ONNX output and an explicit bounded timeout failure; final cleanup again removed only project-owned resources. This is local platform-flow evidence, not GPU, vLLM, quality, throughput, or cloud evidence.
