# Validation

Validation is local-first. Record hardware, runtime, exact command and result for any benchmark; never infer GPU behavior from the deterministic CPU fixture or fabricate validation.

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
