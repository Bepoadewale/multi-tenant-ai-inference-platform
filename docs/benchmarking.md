# Benchmarking and demo scenarios

`make load-test` is a deterministic **mock-backend** benchmark client. It writes JSON, CSV, and
Markdown metadata/results and explicitly labels its output `local-mock`; its figures are useful for
gateway smoke/regression work only. They are not measurements of the Dockerized ONNX Runtime path,
model quality, GPU execution, TTFT, TPOT, or production throughput.

The primary local platform demo is different: `make bootstrap-local` and `make demo-local` execute
two CPU ONNX Runtime targets through two gateways and Redis-backed admission. GPU reports must
record model/revision, vLLM settings, hardware/SKU, GPU count, driver/runtime, date,
prompt/output distributions, concurrency, and cold/warm state.

Demo: A normal `team-search` request succeeds and meters usage. B `team-payments` requesting embeddings gets 403. C repeated payments traffic gets 429 while search remains healthy. D setting all targets unhealthy returns 503. E catalog weights demonstrate canary routing. F KEDA manifest shows demand scaling. G usage endpoint reports per-tenant tokens and estimated cost.
