"""Bounded delegated agent identities for the flagship's narrow tool facade."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims


@dataclass(frozen=True)
class AgentIdentity:
    subject: str
    tenant: str
    delegated_by: str
    scopes: frozenset[str]


def delegated_agent(authorization: str | None = Header(default=None)) -> AgentIdentity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "delegated agent identity required")
    claims = _jwt_claims(authorization.removeprefix("Bearer "))
    if claims.get("principal_type") != "agent" or "agent.tools" not in claims["roles"]:
        raise HTTPException(403, "delegated agent role required")
    delegated_by = claims.get("delegated_by")
    if not isinstance(delegated_by, str) or not delegated_by:
        raise HTTPException(403, "agent identity requires a human delegator")
    return AgentIdentity(
        subject=str(claims["sub"]),
        tenant=str(claims["tenant"]),
        delegated_by=delegated_by,
        scopes=frozenset(str(claims.get("scope", "")).split()),
    )


def require_agent_scope(identity: AgentIdentity, scope: str) -> AgentIdentity:
    if scope not in identity.scopes:
        raise HTTPException(403, f"delegated {scope} scope required")
    return identity
