"""Signed, short-lived delegated identities for bounded sandbox tasks."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims


@dataclass(frozen=True)
class SandboxAgentIdentity:
    subject: str
    tenant: str
    delegated_by: str


def sandbox_agent(authorization: str | None = Header(default=None)) -> SandboxAgentIdentity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "delegated sandbox agent identity required")
    claims = _jwt_claims(authorization.removeprefix("Bearer "))
    if claims.get("principal_type") != "agent" or "agent.sandbox" not in claims["roles"]:
        raise HTTPException(403, "delegated sandbox agent role required")
    if "sandbox.execute" not in str(claims.get("scope", "")).split():
        raise HTTPException(403, "sandbox.execute scope required")
    delegated_by = claims.get("delegated_by")
    if not isinstance(delegated_by, str) or not delegated_by:
        raise HTTPException(403, "sandbox agent identity requires a human delegator")
    return SandboxAgentIdentity(
        subject=str(claims["sub"]), tenant=str(claims["tenant"]), delegated_by=delegated_by
    )
