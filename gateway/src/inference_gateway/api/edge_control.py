"""Fleet-facing control contract; intentionally narrower than the edge project."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from inference_gateway.auth.edge import EdgeDeviceIdentity, edge_device
from inference_gateway.edge.store import EdgeStore
from inference_gateway.observability.tracing import configure_tracing
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

REGISTRATIONS = Counter("inference_gateway_edge_device_registrations_total", "Edge-device registration events", ["tenant"])
HEARTBEATS = Counter("inference_gateway_edge_device_heartbeats_total", "Edge-device heartbeats", ["tenant", "network"])
DEVICES = Gauge("inference_gateway_edge_registered_devices", "Registered edge devices", ["tenant"])


class Registration(BaseModel):
    profile: str = Field(pattern=r"^[a-z][a-z0-9-]{2,62}$")
    local_models: list[str] = Field(default_factory=list)
    endpoint: str = Field(pattern=r"^http://[a-z0-9-]+:8080$")


class Heartbeat(BaseModel):
    network: str = Field(pattern=r"^(ONLINE|OFFLINE)$")
    telemetry_count: int = Field(default=0, ge=0, le=10_000)


app = FastAPI(title="Flagship Edge Adapter Control", version="0.1.0")
configure_tracing(app, "edge-adapter-control")
store = EdgeStore(os.getenv("EDGE_DB_PATH", ".local/edge/devices.db"))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "scope": "narrow-edge-adapter", "store": Path(store.path).name}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/edge/v1/devices/register")
def register(body: Registration, identity: EdgeDeviceIdentity = Depends(edge_device)) -> dict:
    device = store.register(identity.device_id, identity.tenant, body.profile, body.local_models, body.endpoint)
    REGISTRATIONS.labels(tenant=identity.tenant).inc()
    DEVICES.labels(tenant=identity.tenant).set(len([d for d in store.list() if d["tenant"] == identity.tenant]))
    return {"device": device}


@app.post("/edge/v1/devices/heartbeat")
def heartbeat(body: Heartbeat, identity: EdgeDeviceIdentity = Depends(edge_device)) -> dict:
    device = store.heartbeat(identity.device_id, body.network, body.telemetry_count)
    if not device:
        raise HTTPException(404, "device is not registered")
    HEARTBEATS.labels(tenant=identity.tenant, network=body.network).inc()
    return {"device": device}


@app.get("/edge/v1/devices")
def devices() -> dict:
    """Metadata-only local fleet inventory; no model inputs/outputs are retained."""
    return {"devices": store.list(), "hardware": "SIMULATED"}
