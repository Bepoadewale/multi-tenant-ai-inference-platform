# Benchmarking and demo scenarios

`make load-test` writes JSON, CSV, and Markdown metadata/results. It records local mock mode and explicitly says GPU metrics, TTFT, and TPOT are unavailable. GPU reports must record model/revision, vLLM settings, hardware/SKU, GPU count, driver/runtime, date, prompt/output distributions, concurrency, and cold/warm state.

Demo: A normal `team-search` request succeeds and meters usage. B `team-payments` requesting embeddings gets 403. C repeated payments traffic gets 429 while search remains healthy. D setting all targets unhealthy returns 503. E catalog weights demonstrate canary routing. F KEDA manifest shows demand scaling. G usage endpoint reports per-tenant tokens and estimated cost.
