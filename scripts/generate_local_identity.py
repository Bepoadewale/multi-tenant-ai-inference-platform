#!/usr/bin/env python3
"""Generate non-production Ed25519 identity material for the local Compose demo."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ISSUER = "https://local.inference.platform"
AUDIENCE = "inference-gateway"


def token(
    private_key: str,
    subject: str,
    tenant: str,
    roles: list[str],
    *,
    lifetime_seconds: int = 4 * 60 * 60,
    principal_type: str | None = None,
    delegated_by: str | None = None,
    scopes: list[str] | None = None,
) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "tenant": tenant,
        "roles": roles,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=lifetime_seconds),
    }
    if principal_type:
        claims["principal_type"] = principal_type
    if delegated_by:
        claims["delegated_by"] = delegated_by
    if scopes:
        claims["scope"] = " ".join(scopes)
    return jwt.encode(
        claims,
        private_key,
        algorithm="EdDSA",
    )


def main() -> None:
    root = Path(".local/identity")
    root.mkdir(parents=True, exist_ok=True)
    private_path, public_path, tokens_path = root / "private.pem", root / "public.pem", root / "tokens.json"
    if private_path.exists() and public_path.exists():
        private_bytes = private_path.read_bytes()
    else:
        private = Ed25519PrivateKey.generate()
        private_bytes = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        public_bytes = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        private_path.write_bytes(private_bytes)
        public_path.write_bytes(public_bytes)
        private_path.chmod(0o600)
    tokens_path.write_text(json.dumps({
        "search": token(private_bytes.decode(), "developer-search", "team-search", ["inference.invoke"]),
        "payments": token(private_bytes.decode(), "developer-payments", "team-payments", ["inference.invoke"]),
        "analytics": token(private_bytes.decode(), "developer-analytics", "team-analytics", ["inference.invoke"]),
        "reporting": token(private_bytes.decode(), "developer-reporting", "team-reporting", ["inference.invoke"]),
        "admin": token(private_bytes.decode(), "platform-admin", "team-search", ["platform.admin"]),
        "approver": token(private_bytes.decode(), "release-approver", "team-search", ["release.approve"]),
        "remediation_approver": token(
            private_bytes.decode(),
            "remediation-approver",
            "team-search",
            ["remediation.approve"],
        ),
        "delegated_agent": token(
            private_bytes.decode(),
            "release-observer-agent",
            "team-search",
            ["agent.tools"],
            lifetime_seconds=300,
            principal_type="agent",
            delegated_by="developer-search",
            scopes=["inference.read", "remediation.plan"],
        ),
    }))


if __name__ == "__main__":
    main()
