import os

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims


def platform_admin(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(403, "platform-admin role required")
    if os.getenv("INFERENCE_AUTH_MODE", "fixture") == "jwt":
        claims = _jwt_claims(authorization.removeprefix("Bearer "))
        if "platform.admin" not in claims["roles"]:
            raise HTTPException(403, "platform-admin role required")
        return str(claims["sub"])
    if authorization == "Bearer local-platform-admin-token":
        return "local-platform-admin"
    raise HTTPException(403, "platform-admin role required")
