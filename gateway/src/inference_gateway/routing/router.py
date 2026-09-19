import hashlib

from fastapi import HTTPException
from inference_gateway.models import ModelDefinition, ModelTarget, Tenant


class Router:
    def choose(self, tenant: Tenant, model: ModelDefinition, request_id: str) -> ModelTarget:
        if model.name not in tenant.allowed_models:
            raise HTTPException(403, "tenant is not authorized for this model")
        healthy = [target for target in model.targets if target.healthy and target.weight > 0]
        if not healthy:
            raise HTTPException(503, "no healthy model backend", headers={"Retry-After": "5"})
        bucket = int(hashlib.sha256(request_id.encode()).hexdigest(), 16) % sum(
            target.weight for target in healthy
        )
        total = 0
        for target in healthy:
            total += target.weight
            if bucket < total:
                return target
        return healthy[-1]
