# Routing and health

Aliases decouple clients from model IDs. `chat-default` routes by deterministic weighted selection (90/10 example) across healthy targets. A backend marked unhealthy receives no traffic; no healthy target returns controlled 503. Requests have bounded timeouts in the production vLLM adapter; streaming is never blindly retried because partial output may have reached the client.
