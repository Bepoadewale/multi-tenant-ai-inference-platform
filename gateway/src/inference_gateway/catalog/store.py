import os

from inference_gateway.models import ModelDefinition, ModelTarget, Tenant, TenantQuota


class Catalog:
    """Static local catalog; production uses a versioned control-plane store."""

    def __init__(self) -> None:
        self.tenants = {
            "team-search": Tenant(
                id="team-search",
                allowed_models={"chat-default", "embeddings"},
                cost_center="SEARCH",
                quotas=TenantQuota(
                    requests_per_minute=100,
                    tokens_per_minute=100_000,
                    concurrent_requests=10,
                    daily_token_quota=2_000_000,
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
                ),
            ),
        }
        self.models = {
            "chat-default": ModelDefinition(
                name="chat-default",
                model_id="local/tiny-intent-classifier",
                runtime="onnx",
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
            ),
            "embeddings": ModelDefinition(
                name="embeddings",
                model_id="sentence-transformers/all-MiniLM-L6-v2",
                runtime="mock",
                max_replicas=2,
                targets=[ModelTarget(name="embeddings-v1", version="v1", weight=100)],
            ),
        }

    def tenant(self, tenant_id: str) -> Tenant:
        return self.tenants[tenant_id]

    def model(self, name: str) -> ModelDefinition:
        return self.models[name]
