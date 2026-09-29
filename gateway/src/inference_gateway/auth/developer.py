"""Developer identities for the flagship's narrow self-service contract."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims
from inference_gateway.catalog.store import Catalog


@dataclass(frozen=True)
class DeveloperIdentity:
    subject: str
    tenant: str


def self_service_developer(authorization: str | None = Header(default=None)) -> DeveloperIdentity:
    """Require a human developer identity; agents cannot self-provision integrations."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "developer identity required")
    claims = _jwt_claims(authorization.removeprefix("Bearer "))
    if claims.get("principal_type") == "agent":
        raise HTTPException(403, "delegated agents cannot create developer integrations")
    if "developer.self_service" not in claims["roles"]:
        raise HTTPException(403, "developer.self_service role required")
    tenant = str(claims["tenant"])
    try:
        Catalog().tenant(tenant)
    except KeyError as error:
        raise HTTPException(403, "unknown tenant") from error
    return DeveloperIdentity(subject=str(claims["sub"]), tenant=tenant)
