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
QUEUE_WAIT = Histogram(
    "inference_gateway_queue_wait_seconds",
    "Time spent waiting for bounded tenant admission",
    ["tenant"],
)
CAPACITY_DECISIONS = Counter(
    "inference_gateway_simulated_gpu_capacity_decisions_total",
    "Simulated GPU capacity policy decisions; local ONNX execution remains CPU-only",
    ["tenant", "pool", "decision"],
)
CAPACITY_ALLOCATED = Gauge(
    "inference_gateway_simulated_gpu_allocated_slots",
    "Allocated slots in simulated GPU quota accounting",
    ["pool"],
)
CAPACITY_TENANT_ALLOCATED = Gauge(
    "inference_gateway_simulated_gpu_tenant_allocated_slots",
    "Tenant allocation in simulated GPU quota accounting",
    ["tenant", "pool"],
)
CAPACITY_QUEUE = Gauge(
    "inference_gateway_simulated_gpu_capacity_queue_depth",
    "Requests waiting for simulated GPU capacity",
    ["pool"],
)
