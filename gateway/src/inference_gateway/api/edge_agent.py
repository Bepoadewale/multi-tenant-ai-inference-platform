"""Independent local edge agent: local ONNX first, policy-controlled central fallback."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from time import perf_counter

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from inference_gateway.auth.service import authenticated_tenant
from inference_gateway.backends.onnx import OnnxRuntimeBackend
from inference_gateway.models import ChatCompletionRequest, Tenant
from inference_gateway.observability.tracing import configure_tracing
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

ROUTES = Counter("inference_gateway_edge_inferences_total", "Edge inference routing outcomes", ["device", "route", "reason"])


class EdgeInferenceRequest(BaseModel):
    request: ChatCompletionRequest
    data_classification: str = Field(default="public", pattern=r"^(public|restricted)$")
    routing_profile: str = Field(default="LOCAL_PREFERRED", pattern=r"^(LOCAL_ONLY|LOCAL_PREFERRED|CLOUD_PREFERRED|CLOUD_ONLY|PRIVACY_FIRST)$")


app = FastAPI(title="Local Edge Device Agent", version="0.1.0")
configure_tracing(app, "edge-device-agent")
device_id = os.getenv("EDGE_DEVICE_ID", "edge-device")
control_url = os.getenv("EDGE_CONTROL_URL", "http://edge-control:8080")
gateway_url = os.getenv("EDGE_GATEWAY_URL", "http://gateway-1:8080")
token_path = Path(os.getenv("EDGE_TOKENS_PATH", "/run/identity/tokens.json"))
local_models = set(filter(None, os.getenv("EDGE_LOCAL_MODELS", "").split(",")))
profile = os.getenv("EDGE_PROFILE", "laptop-high")
backend = OnnxRuntimeBackend() if local_models else None
network = "ONLINE"
telemetry_count = 0


def _device_token() -> str:
    key = os.getenv("EDGE_TOKEN_KEY", "edge_search_device")
    return json.loads(token_path.read_text())[key]


async def _control(path: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=3) as client:
        response = await client.post(
            f"{control_url}{path}", json=payload, headers={"Authorization": f"Bearer {_device_token()}"}
        )
        response.raise_for_status()


async def _register_and_heartbeat() -> None:
    await _control("/edge/v1/devices/register", {
        "profile": profile, "local_models": sorted(local_models), "endpoint": f"http://{os.getenv('HOSTNAME', device_id)}:8080",
    })
    await _control("/edge/v1/devices/heartbeat", {"network": network, "telemetry_count": telemetry_count})


@app.on_event("startup")
async def startup() -> None:
    # Compose DNS service names are explicit instead of relying on container hostname.
    global device_id
    device_id = os.getenv("EDGE_DEVICE_ID", device_id)
    for _ in range(20):
        try:
            await _register_and_heartbeat()
            return
        except (httpx.HTTPError, OSError):
            await asyncio.sleep(1)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "device_id": device_id, "profile": profile, "local_models": sorted(local_models), "network": network, "hardware": "SIMULATED"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/edge/v1/network/{state}")
async def set_network(state: str) -> dict:
    """Demo-only local device toggle. State is explicitly simulated."""
    global network
    if state not in {"online", "offline"}:
        raise HTTPException(422, "state must be online or offline")
    network = state.upper()
    try:
        await _control("/edge/v1/devices/heartbeat", {"network": network, "telemetry_count": telemetry_count})
    except httpx.HTTPError:
        pass  # A disconnected device continues local inference and reports later.
    return {"device_id": device_id, "network": network, "simulated": True}


async def _fallback(body: EdgeInferenceRequest, authorization: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{gateway_url}/v1/chat/completions", json=body.request.model_dump(), headers={"Authorization": authorization}
        )
        response.raise_for_status()
        return response.json()


@app.post("/edge/v1/chat/completions")
async def infer(
    body: EdgeInferenceRequest,
    tenant: Tenant = Depends(authenticated_tenant),
    authorization: str | None = Header(default=None),
) -> dict:
    # FastAPI dependency validates the same signed bearer token the central gateway uses.
    global telemetry_count
    if body.request.model not in tenant.allowed_models:
        raise HTTPException(403, "model is not assigned to this tenant")
    local_ready = backend is not None and body.request.model in local_models and network in {"ONLINE", "OFFLINE"}
    privacy_requires_local = body.data_classification == "restricted" or body.routing_profile in {"LOCAL_ONLY", "PRIVACY_FIRST"}
    central_allowed = body.data_classification == "public" and body.routing_profile not in {"LOCAL_ONLY", "PRIVACY_FIRST"} and network == "ONLINE"
    if body.routing_profile == "CLOUD_ONLY" and privacy_requires_local:
        raise HTTPException(403, "restricted request cannot use CLOUD_ONLY routing")
    use_local = local_ready and (body.routing_profile != "CLOUD_ONLY") and (body.routing_profile != "CLOUD_PREFERRED" or not central_allowed)
    started = perf_counter()
    if use_local:
        text, usage, _ = await backend.complete(body.request)  # type: ignore[union-attr]
        telemetry_count += 1
        ROUTES.labels(device=device_id, route="LOCAL", reason="local_model_available").inc()
        return {"id": f"edge-{device_id}", "object": "chat.completion", "model": body.request.model, "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}], "usage": usage.model_dump(), "edge": {"device_id": device_id, "route": "LOCAL", "reason": "local_model_available", "latency_ms": round((perf_counter() - started) * 1000, 3), "execution_provider": "CPUExecutionProvider"}}
    if not central_allowed:
        ROUTES.labels(device=device_id, route="DENY", reason="privacy_or_offline").inc()
        raise HTTPException(403, "cloud fallback denied by privacy policy or offline state")
    if authorization is None:
        raise HTTPException(401, "missing bearer token")
    result = await _fallback(body, authorization)
    telemetry_count += 1
    ROUTES.labels(device=device_id, route="CLOUD", reason="local_model_unavailable").inc()
    result["edge"] = {"device_id": device_id, "route": "CLOUD", "reason": "local_model_unavailable", "latency_ms": round((perf_counter() - started) * 1000, 3), "execution_provider": None}
    return result
