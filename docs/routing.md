# Routing and health

Flagship context: weighted routing is the preserved serving boundary governed by the
executed release-control slice through a narrow traffic-intent contract. Capacity
admission happens before routing: a model can require simulated capacity or explicitly
allow CPU fallback. Capacity rejection never silently changes a model's policy.

Aliases decouple clients from model IDs. `chat-default` routes by deterministic weighted selection (90/10 example) across healthy targets. A backend marked unhealthy receives no traffic; no healthy target returns controlled 503. Requests have bounded timeouts in the production vLLM adapter; streaming is never blindly retried because partial output may have reached the client.
