"""A small, evidence-backed golden path for integrating with the inference gateway.

This is intentionally not a developer portal replacement.  It demonstrates the
contract a portal/template would call: a signed developer obtains a tenant-bound
profile and generated starter files without receiving runtime or platform authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from inference_gateway.auth.developer import DeveloperIdentity, self_service_developer
from inference_gateway.catalog.store import Catalog
from inference_gateway.observability.tracing import configure_tracing
from inference_gateway.self_service.store import SelfServiceStore
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, Field

PROFILES = Counter(
    "inference_gateway_developer_integration_profiles_total",
    "Developer self-service integration profile outcomes",
    ["tenant", "outcome"],
)


class CreateIntegration(BaseModel):
    service_name: str = Field(pattern=r"^[a-z][a-z0-9-]{2,62}$")
    model: str = Field(min_length=1, max_length=120)
    owner: str = Field(pattern=r"^[a-z][a-z0-9-]{2,62}$")
    environment: str = Field(default="development", pattern=r"^(development|staging)$")


app = FastAPI(title="Flagship Developer Self-Service", version="0.1.0")
configure_tracing(app, "developer-self-service")
store = SelfServiceStore(os.getenv("SELF_SERVICE_DB_PATH", ".local/self-service/profiles.db"))


def _fingerprint(request: CreateIntegration) -> str:
    return hashlib.sha256(request.model_dump_json().encode()).hexdigest()


def _starter_files(profile: dict) -> dict[str, str]:
    """Return token-free artifacts a portal could write into a developer repository."""
    config = {
        "api_version": "inference.platform/v1",
        "kind": "InferenceIntegration",
        "metadata": {
            "name": profile["service_name"],
            "owner": profile["owner"],
            "tenant": profile["tenant"],
            "environment": profile["environment"],
        },
        "spec": {"base_url": profile["base_url"], "model": profile["model"]},
    }
    client = f'''"""Generated tenant-bound starter. Supply INFERENCE_API_TOKEN at runtime only."""
import os
import urllib.request

request = urllib.request.Request(
    "{profile["base_url"]}/chat/completions",
    data=b'{{"model":"{profile["model"]}","messages":[{{"role":"user","content":"hello"}}],"max_tokens":4}}',
    headers={{"Authorization": "Bearer " + os.environ["INFERENCE_API_TOKEN"], "Content-Type": "application/json"}},
    method="POST",
)
with urllib.request.urlopen(request, timeout=10) as response:
    print(response.read().decode())
'''
    readme = (
        f"# {profile['service_name']} inference integration\n\n"
        f"This generated profile is bound to `{profile['tenant']}` and `{profile['model']}`. "
        "It does not contain a token, tenant header, runtime URL, Redis credential, or rollout authority. "
        "Obtain a workload token from the configured identity provider at runtime.\n"
    )
    return {
        "inference-integration.yaml": json.dumps(config, indent=2) + "\n",
        "inference_client.py": client,
        "README.md": readme,
    }


def _profile(request: CreateIntegration, identity: DeveloperIdentity) -> dict:
    return {
        "id": str(uuid4()),
        "tenant": identity.tenant,
        "requester": identity.subject,
        "service_name": request.service_name,
        "model": request.model,
        "owner": request.owner,
        "environment": request.environment,
        "base_url": os.getenv("GATEWAY_PUBLIC_URL", "http://localhost:8081/v1"),
        "created_at": datetime.now(UTC).isoformat(),
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "store": Path(store.path).name, "scope": "developer-self-service"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/developer/v1/inference-integrations", status_code=201)
def create_integration(
    request: CreateIntegration,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    identity: DeveloperIdentity = Depends(self_service_developer),
) -> dict[str, object]:
    if not idempotency_key or not re.fullmatch(r"[A-Za-z0-9._-]{8,128}", idempotency_key):
        raise HTTPException(422, "an Idempotency-Key of 8-128 safe characters is required")
    if request.model not in Catalog().tenant(identity.tenant).allowed_models:
        PROFILES.labels(tenant=identity.tenant, outcome="DENIED_MODEL").inc()
        raise HTTPException(403, "requested model alias is not assigned to this tenant")
    fingerprint = _fingerprint(request)
    existing = store.by_idempotency_key(identity.tenant, idempotency_key)
    if existing:
        if existing[0] != fingerprint:
            PROFILES.labels(tenant=identity.tenant, outcome="IDEMPOTENCY_CONFLICT").inc()
            raise HTTPException(409, "idempotency key was already used for a different integration")
        return {"profile": existing[1], "files": _starter_files(existing[1]), "idempotent_replay": True}
    profile = _profile(request, identity)
    store.save(profile, idempotency_key=idempotency_key, fingerprint=fingerprint)
    PROFILES.labels(tenant=identity.tenant, outcome="CREATED").inc()
    return {"profile": profile, "files": _starter_files(profile), "idempotent_replay": False}


@app.get("/developer/v1/inference-integrations")
def list_integrations(identity: DeveloperIdentity = Depends(self_service_developer)) -> dict[str, object]:
    return {"integrations": store.list_for_tenant(identity.tenant)}


@app.get("/developer/v1/inference-integrations/{profile_id}")
def get_integration(
    profile_id: str, identity: DeveloperIdentity = Depends(self_service_developer)
) -> dict[str, object]:
    profile = store.get(profile_id)
    if profile is None:
        raise HTTPException(404, "integration profile not found")
    if profile["tenant"] != identity.tenant:
        raise HTTPException(403, "cross-tenant integration profile denied")
    return {"profile": profile, "files": _starter_files(profile)}
