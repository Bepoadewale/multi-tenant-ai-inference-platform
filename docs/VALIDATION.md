# Validation

Validation is local-first. Record hardware, runtime, exact command and result for any benchmark; never infer GPU behavior from the deterministic CPU fixture or fabricate validation.

## Flagship integration rule

The evidence below validates the inference core only. Each future flagship vertical
slice must add its own commands, external dependencies, success path, failure path and
clean-room evidence before it is listed as executed. The integrated flagship demo must
be rerun from clean project state after the slices are connected.

## MLflow registry slice

The first flagship slice was executed locally after the historical inference-core
clean-room evidence below. `make bootstrap-local` started MLflow with a project-scoped
SQLite store and artifacts directory, evaluated two generated ONNX artifacts with
`CPUExecutionProvider`, registered their SHA-256 digests and fixture metrics, and set
`champion` (stable v1) and `candidate` (v2) aliases. `make smoke` checked the MLflow
health and registered model, while `make demo-model-registry` verified the aliases and
recorded digest evidence in `.local/mlflow/registry-evidence.json`.

This is registry and artifact-evidence validation only. It does **not** yet validate
governed canary approval, promotion, rollback, or the expanded flagship clean-room
cycle; those remain completion blockers.

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
