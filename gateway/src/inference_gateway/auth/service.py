from fastapi import Header, HTTPException
from inference_gateway.catalog.store import Catalog
from inference_gateway.models import Tenant

TOKENS = {"local-search-token": "team-search", "local-payments-token": "team-payments"}


def authenticated_tenant(authorization: str | None = Header(default=None)) -> Tenant:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing or invalid bearer token")
    tenant_id = TOKENS.get(authorization.removeprefix("Bearer "))
    if not tenant_id:
        raise HTTPException(401, "unknown API credential")
    return Catalog().tenant(tenant_id)
