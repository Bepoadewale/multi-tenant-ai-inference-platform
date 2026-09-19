from fastapi import Header, HTTPException


def platform_admin(authorization: str | None = Header(default=None)) -> str:
    """Development fixture. Production validates OIDC groups/roles at the API boundary."""
    if authorization != "Bearer local-platform-admin-token":
        raise HTTPException(403, "platform-admin role required")
    return "local-platform-admin"
