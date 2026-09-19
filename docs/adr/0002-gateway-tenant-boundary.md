# ADR 0002: Clients access the gateway, not vLLM

The gateway owns authenticated tenant resolution, quota admission, model permissions, routing, metadata-only metering, and uniform errors. Exposing vLLM directly would bypass those controls.
