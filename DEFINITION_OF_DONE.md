# Definition of Done

# Portfolio Complete — Local-First Scope Gate

- [x] CPU-capable real model runtime returns output through the OpenAI-compatible API; streaming is exercised if claimed.
- [x] Signed/authenticated tenant identity, isolation, and no cross-tenant leakage are tested.
- [x] Redis-backed distributed quota/rate/concurrency enforcement is exercised across multiple gateway instances where practical.
- [x] Queue/backpressure is bounded and produces an explicit policy reject or queue result under overload.
- [x] Alias and claimed weighted/canary routing reach the intended real backend deterministically.
- [x] Quota exhaustion, backend unavailable, timeout, invalid model, and overload failure paths are executed.
- [x] Metering records request/usage without raw prompt leakage where policy forbids it.
- [x] OTel, Prometheus, and Grafana expose tenant/model/request signals; latency, errors, queue time, and TTFT where available are evidenced.
- [x] `make demo`/equivalent reproduces tenant → auth → quota → queue → runtime → response → usage → telemetry.
- [x] Unit, integration, local-E2E, and security/failure tests pass; required CI is green.
- [x] GPU/DCGM/KV-cache behavior remains simulated or unexecuted unless real hardware runs; README/status state the boundary.

## Maturity Levels

- **FOUNDATION:** architecture and core logic exist.
- **PARTIALLY VALIDATED:** important integrations run but the central story is incomplete.
- **LOCAL END-TO-END VALIDATED:** primary success runs locally with material evidence gaps remaining.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** every checked gate has executed evidence; do not omit the suffix without production validation.

# Clean-Room Reproducibility Gate

`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` requires two executed clean-room cycles: clone → install → bootstrap gateway, Redis, CPU runtime, telemetry → smoke → authenticated inference/quota/queue/routing demo → overload or backend-failure demo → validation → project-scoped cleanup → second clean bootstrap/demo. Planned commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-local`, `make demo-overload`, `make verify`, `make clean-local`.

- [x] Clean clone/bootstrap has no hidden state; primary and failure demos pass.
- [x] Cleanup removes only this project and unrelated resources survive.
- [x] Post-cleanup absence and second bootstrap/demo are recorded in `docs/VALIDATION.md`.
