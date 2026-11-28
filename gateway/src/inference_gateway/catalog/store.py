import os

from inference_gateway.models import (
    CapacityPolicy,
    ModelDefinition,
    ModelTarget,
    Tenant,
    TenantQuota,
)


class Catalog:
    """Static local catalog; production uses a versioned control-plane store."""

    def __init__(self) -> None:
        vllm_url = os.getenv("INFERENCE_VLLM_URL")
        if vllm_url:
            model_id = os.getenv("INFERENCE_GPU_MODEL_ID", "gpu-default")
            chat_default = ModelDefinition(
                name="chat-default",
                model_id=model_id,
                runtime="vllm",
                gpu_count=1,
                gpu_type=os.getenv("INFERENCE_GPU_POOL", "single-l4-logical"),
                capacity_policy=CapacityPolicy.REQUIRE_SIMULATED_GPU,
                max_replicas=1,
                targets=[
                    ModelTarget(
                        name="vllm-single-l4",
                        version="v1",
                        weight=100,
                        backend_url=vllm_url,
                    )
                ],
            )
        else:
            chat_default = ModelDefinition(
                name="chat-default",
                model_id="local/tiny-intent-classifier",
                runtime="onnx",
                gpu_count=1,
                gpu_type="simulated-l40s",
                capacity_policy=CapacityPolicy.REQUIRE_SIMULATED_GPU,
                max_replicas=4,
                targets=[
                    ModelTarget(
                        name="onnx-stable-v1",
                        version="v1",
                        weight=90,
                        backend_url=os.getenv("INFERENCE_TARGET_V1_URL"),
                    ),
                    ModelTarget(
                        name="onnx-candidate-v2",
                        version="v2",
                        weight=10,
                        backend_url=os.getenv("INFERENCE_TARGET_V2_URL"),
                    ),
                ],
            )
        self.tenants = {
            "team-search": Tenant(
                id="team-search",
                allowed_models={"chat-default", "chat-timeout-demo", "embeddings"},
                cost_center="SEARCH",
                quotas=TenantQuota(
                    requests_per_minute=100,
                    tokens_per_minute=100_000,
                    concurrent_requests=10,
                    daily_token_quota=2_000_000,
                    max_input_tokens=8192,
                    max_output_tokens=2048,
                    simulated_gpu_slots=1,
                ),
            ),
            "team-payments": Tenant(
                id="team-payments",
                allowed_models={"chat-default"},
                cost_center="PAY",
                quotas=TenantQuota(
                    requests_per_minute=5,
                    tokens_per_minute=500,
                    concurrent_requests=2,
                    daily_token_quota=10_000,
                    max_input_tokens=2048,
                    max_output_tokens=256,
                    simulated_gpu_slots=1,
                ),
            ),
            "team-analytics": Tenant(
                id="team-analytics",
                allowed_models={"chat-cpu-fallback-demo"},
                cost_center="ANALYTICS",
                quotas=TenantQuota(
                    requests_per_minute=20,
                    tokens_per_minute=10_000,
                    concurrent_requests=5,
                    daily_token_quota=100_000,
                    max_input_tokens=4096,
                    max_output_tokens=512,
                    simulated_gpu_slots=1,
                ),
            ),
            "team-reporting": Tenant(
                id="team-reporting",
                allowed_models={"chat-default"},
                cost_center="REPORTING",
                quotas=TenantQuota(
                    requests_per_minute=20,
                    tokens_per_minute=10_000,
                    concurrent_requests=5,
                    daily_token_quota=100_000,
                    max_input_tokens=4096,
                    max_output_tokens=512,
                    simulated_gpu_slots=1,
                ),
            ),
            # GPU lab identities use realistic workload names and intentionally
            # different limits. These are logical controls over one shared GPU;
            # they do not provide hardware isolation.
            "customer-support": Tenant(
                id="customer-support",
                allowed_models={"chat-default"},
                cost_center="SUPPORT",
                quotas=TenantQuota(
                    requests_per_minute=30,
                    tokens_per_minute=12_000,
                    concurrent_requests=2,
                    daily_token_quota=250_000,
                    max_input_tokens=4096,
                    max_output_tokens=512,
                    simulated_gpu_slots=1,
                ),
            ),
            "internal-engineering": Tenant(
                id="internal-engineering",
                allowed_models={"chat-default", "embeddings"},
                cost_center="ENGINEERING",
                quotas=TenantQuota(
                    requests_per_minute=60,
                    tokens_per_minute=30_000,
                    concurrent_requests=4,
                    daily_token_quota=750_000,
                    max_input_tokens=8192,
                    max_output_tokens=1024,
                    simulated_gpu_slots=1,
                ),
            ),
            "research": Tenant(
                id="research",
                allowed_models={"chat-default", "embeddings", "chat-timeout-demo"},
                cost_center="RESEARCH",
                quotas=TenantQuota(
                    requests_per_minute=15,
                    tokens_per_minute=20_000,
                    concurrent_requests=1,
                    daily_token_quota=500_000,
                    max_input_tokens=8192,
                    max_output_tokens=2048,
                    simulated_gpu_slots=1,
                ),
            ),
        }
        self.models = {
            "chat-default": chat_default,
            "embeddings": ModelDefinition(
                name="embeddings",
                model_id="sentence-transformers/all-MiniLM-L6-v2",
                runtime="mock",
                max_replicas=2,
                targets=[ModelTarget(name="embeddings-v1", version="v1", weight=100)],
            ),
            "chat-timeout-demo": ModelDefinition(
                name="chat-timeout-demo",
                model_id="local/tiny-intent-classifier",
                runtime="onnx",
                gpu_count=1,
                gpu_type="simulated-l40s",
                capacity_policy=CapacityPolicy.REQUIRE_SIMULATED_GPU,
                max_replicas=1,
                targets=[
                    ModelTarget(
                        name="onnx-delayed-fixture",
                        version="v2",
                        weight=100,
                        backend_url=os.getenv("INFERENCE_TARGET_V2_URL"),
                        timeout_seconds=0.1,
                    )
                ],
            ),
            "chat-cpu-fallback-demo": ModelDefinition(
                name="chat-cpu-fallback-demo",
                model_id="local/tiny-intent-classifier",
                runtime="onnx",
                gpu_count=1,
                gpu_type="simulated-l40s",
                capacity_policy=CapacityPolicy.ALLOW_CPU_FALLBACK,
                max_replicas=1,
                targets=[
                    ModelTarget(
                        name="onnx-cpu-fallback-v1",
                        version="v1",
                        weight=100,
                        backend_url=os.getenv("INFERENCE_TARGET_V1_URL"),
                    )
                ],
            ),
        }

    def tenant(self, tenant_id: str) -> Tenant:
        return self.tenants[tenant_id]

    def model(self, name: str) -> ModelDefinition:
        return self.models[name]
