# Definition of Done

# Portfolio Complete — Local-First Scope Gate

- [ ] CPU-capable real model runtime returns output through the OpenAI-compatible API; streaming is exercised if claimed.
- [ ] Signed/authenticated tenant identity, isolation, and no cross-tenant leakage are tested.
- [ ] Redis-backed distributed quota/rate/concurrency enforcement is exercised across multiple gateway instances where practical.
- [ ] Queue/backpressure is bounded and produces an explicit policy reject or queue result under overload.
- [ ] Alias and claimed weighted/canary routing reach the intended real backend deterministically.
- [ ] Quota exhaustion, backend unavailable, timeout, invalid model, and overload failure paths are executed.
- [ ] Metering records request/usage without raw prompt leakage where policy forbids it.
- [ ] OTel, Prometheus, and Grafana expose tenant/model/request signals; latency, errors, queue time, and TTFT where available are evidenced.
- [ ] `make demo`/equivalent reproduces tenant → auth → quota → queue → runtime → response → usage → telemetry.
- [ ] Unit, integration, local-E2E, and security/failure tests pass; required CI is green.
- [ ] GPU/DCGM/KV-cache behavior remains simulated or unexecuted unless real hardware runs; README/status state the boundary.

## Maturity Levels

- **FOUNDATION:** architecture and core logic exist.
- **PARTIALLY VALIDATED:** important integrations run but the central story is incomplete.
- **LOCAL END-TO-END VALIDATED:** primary success runs locally with material evidence gaps remaining.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** every checked gate has executed evidence; do not omit the suffix without production validation.
