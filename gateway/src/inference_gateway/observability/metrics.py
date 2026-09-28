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
ESTIMATED_COST = Counter(
    "inference_gateway_estimated_cost_usd_total",
    "Explicit local fixture token-cost estimate; not cloud billing",
    ["tenant", "model", "pricing_version"],
)
SLO_EVALUATIONS = Counter(
    "inference_gateway_request_slo_evaluations_total",
    "Local request-level SLO evaluation outcomes",
    ["model", "status"],
)
RELEASE_CORRELATED_REQUESTS = Counter(
    "inference_gateway_release_correlated_requests_total",
    "Requests with an active release-plan correlation",
    ["model", "phase"],
)
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
REMEDIATION_INCIDENTS = Counter(
    "inference_gateway_remediation_incidents_total",
    "Governed remediation incidents created from observed request evidence",
    ["model", "outcome"],
)
REMEDIATION_PLANS = Counter(
    "inference_gateway_remediation_plans_total",
    "Governed remediation plans by action and lifecycle status",
    ["action", "status"],
)
REMEDIATION_ACTIONS = Counter(
    "inference_gateway_remediation_actions_total",
    "Bounded remediation action outcomes",
    ["model", "result"],
)
REMEDIATION_VERIFICATIONS = Counter(
    "inference_gateway_remediation_verifications_total",
    "Post-action remediation verification outcomes",
    ["model", "status"],
)
