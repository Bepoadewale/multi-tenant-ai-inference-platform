from fastapi import Depends, FastAPI, HTTPException
from inference_gateway.auth.admin import platform_admin
from inference_gateway.auth.service import authenticated_tenant
from inference_gateway.models import ChatCompletionRequest, RolloutWeights, Tenant
from inference_gateway.services.gateway import service
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

app = FastAPI(title="Multi-tenant AI Inference Platform", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "mode": "local-mock"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/models")
def models(tenant: Tenant = Depends(authenticated_tenant)):
    return {
        "object": "list",
        "data": [{"id": name, "object": "model"} for name in tenant.allowed_models],
    }


@app.post("/v1/chat/completions")
async def chat(request: ChatCompletionRequest, tenant: Tenant = Depends(authenticated_tenant)):
    return await service.chat(tenant, request)


@app.get("/platform/v1/usage/{tenant_id}")
def usage(tenant_id: str, admin: str = Depends(platform_admin)):
    return service.meter.tenant_summary(tenant_id)


@app.get("/platform/v1/capacity")
def capacity(admin: str = Depends(platform_admin)):
    return {
        "state": "HEALTHY",
        "mode": "local-mock",
        "ready_replicas": 1,
        "gpu_telemetry": "unavailable in local mode",
        "queued_requests": 0,
    }


@app.get("/platform/v1/models")
def platform_models(admin: str = Depends(platform_admin)):
    return list(service.catalog.models.values())


@app.get("/platform/v1/tenants")
def platform_tenants(admin: str = Depends(platform_admin)):
    return list(service.catalog.tenants.values())


@app.get("/platform/v1/deployments")
def deployments(admin: str = Depends(platform_admin)):
    return [
        {"alias": model.name, "targets": model.targets, "serving_mode": model.serving_mode}
        for model in service.catalog.models.values()
    ]


@app.get("/platform/v1/rollouts/{alias}")
def rollout(alias: str, admin: str = Depends(platform_admin)):
    model = service.catalog.models.get(alias)
    if not model:
        raise HTTPException(404, "unknown model alias")
    return {
        "alias": alias,
        "targets": model.targets,
        "audit_events": [event for event in service.admin_audit if event.model == alias],
    }


@app.put("/platform/v1/rollouts/{alias}")
def update_rollout(alias: str, update: RolloutWeights, admin: str = Depends(platform_admin)):
    return service.update_rollout(admin, alias, update)
