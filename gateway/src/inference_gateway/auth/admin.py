import os

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims


def require_role(role: str, authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(403, f"{role} role required")
    if os.getenv("INFERENCE_AUTH_MODE", "fixture") == "jwt":
        claims = _jwt_claims(authorization.removeprefix("Bearer "))
        if role not in claims["roles"]:
            raise HTTPException(403, f"{role} role required")
        return str(claims["sub"])
    if role == "platform.admin" and authorization == "Bearer local-platform-admin-token":
        return "local-platform-admin"
    raise HTTPException(403, f"{role} role required")


def platform_admin(authorization: str | None = Header(default=None)) -> str:
    return require_role("platform.admin", authorization)


def release_approver(authorization: str | None = Header(default=None)) -> str:
    return require_role("release.approve", authorization)
