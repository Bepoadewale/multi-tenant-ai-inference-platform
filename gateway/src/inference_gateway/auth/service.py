import os
from pathlib import Path

import jwt
from fastapi import Header, HTTPException
from inference_gateway.catalog.store import Catalog
from inference_gateway.models import Tenant

TOKENS = {"local-search-token": "team-search", "local-payments-token": "team-payments"}


def _jwt_claims(token: str) -> dict:
    key_path = Path(os.getenv("JWT_PUBLIC_KEY_PATH", ""))
    if not key_path.is_file():
        raise HTTPException(503, "identity verification key unavailable")
    try:
        return jwt.decode(
            token,
            key_path.read_text(),
            algorithms=["EdDSA"],
            issuer=os.getenv("JWT_ISSUER", "https://local.inference.platform"),
            audience=os.getenv("JWT_AUDIENCE", "inference-gateway"),
            options={"require": ["exp", "iss", "aud", "sub", "tenant", "roles"]},
        )
    except jwt.PyJWTError as error:
        raise HTTPException(401, "invalid bearer token") from error


def authenticated_tenant(authorization: str | None = Header(default=None)) -> Tenant:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing or invalid bearer token")
    token = authorization.removeprefix("Bearer ")
    if os.getenv("INFERENCE_AUTH_MODE", "fixture") == "jwt":
        claims = _jwt_claims(token)
        if "inference.invoke" not in claims["roles"]:
            raise HTTPException(403, "inference.invoke role required")
        tenant_id = str(claims["tenant"])
    else:
        tenant_id = TOKENS.get(token)
        if not tenant_id:
            raise HTTPException(401, "unknown API credential")
    try:
        return Catalog().tenant(tenant_id)
    except KeyError as error:
        raise HTTPException(403, "unknown tenant") from error
