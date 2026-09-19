from fastapi import Depends, FastAPI, HTTPException
from inference_gateway.auth.service import authenticated_tenant
from inference_gateway.models import ChatCompletionRequest, Tenant
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
def usage(tenant_id: str, tenant: Tenant = Depends(authenticated_tenant)):
    if tenant.id != tenant_id:
        raise HTTPException(403, "tenant-scoped access only")
    return service.meter.tenant_summary(tenant_id)


@app.get("/platform/v1/capacity")
def capacity(tenant: Tenant = Depends(authenticated_tenant)):
    return {
        "state": "HEALTHY",
        "mode": "local-mock",
        "ready_replicas": 1,
        "gpu_telemetry": "unavailable in local mode",
        "queued_requests": 0,
    }
