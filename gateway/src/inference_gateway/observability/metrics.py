from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter(
    "inference_gateway_requests_total", "Inference requests", ["tenant", "model", "outcome"]
)
TOKENS = Counter("inference_gateway_tokens_total", "Metered tokens", ["tenant", "model", "type"])
THROTTLES = Counter("inference_gateway_throttles_total", "Tenant throttles", ["tenant", "reason"])
LATENCY = Histogram(
    "inference_gateway_request_duration_seconds", "End-to-end inference latency", ["model"]
)
TTFT = Histogram("inference_gateway_ttft_seconds", "Time to first token", ["model"])
ACTIVE = Gauge("inference_gateway_active_requests", "Active requests", ["tenant"])
QUEUE = Gauge("inference_gateway_queue_depth", "Bounded tenant admission queue", ["tenant"])
