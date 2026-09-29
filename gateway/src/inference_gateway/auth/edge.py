"""Identity boundary for locally simulated edge devices.

The edge adapter deliberately uses the same signed issuer as the gateway but
requires a distinct principal type and role. A tenant/user token cannot invent a
device, and a device token cannot gain platform-administration authority.
"""

from dataclasses import dataclass

from fastapi import Header, HTTPException
from inference_gateway.auth.service import _jwt_claims


@dataclass(frozen=True)
class EdgeDeviceIdentity:
    device_id: str
    tenant: str


def edge_device(authorization: str | None = Header(default=None)) -> EdgeDeviceIdentity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "edge device identity required")
    claims = _jwt_claims(authorization.removeprefix("Bearer "))
    if claims.get("principal_type") != "device" or "edge.connect" not in claims["roles"]:
        raise HTTPException(403, "edge device role required")
    return EdgeDeviceIdentity(device_id=str(claims["sub"]), tenant=str(claims["tenant"]))
