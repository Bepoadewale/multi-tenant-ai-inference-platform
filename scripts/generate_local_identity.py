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


def token(private_key: str, subject: str, tenant: str, roles: list[str]) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": subject, "tenant": tenant, "roles": roles, "iss": ISSUER, "aud": AUDIENCE, "iat": now, "exp": now + timedelta(hours=4)},
        private_key,
        algorithm="EdDSA",
    )


def main() -> None:
    root = Path(".local/identity")
    root.mkdir(parents=True, exist_ok=True)
    private_path, public_path, tokens_path = root / "private.pem", root / "public.pem", root / "tokens.json"
    if private_path.exists() and public_path.exists() and tokens_path.exists():
        return
    private = Ed25519PrivateKey.generate()
    private_bytes = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public_bytes = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    private_path.write_bytes(private_bytes)
    public_path.write_bytes(public_bytes)
    private_path.chmod(0o600)
    tokens_path.write_text(json.dumps({
        "search": token(private_bytes.decode(), "developer-search", "team-search", ["inference.invoke"]),
        "payments": token(private_bytes.decode(), "developer-payments", "team-payments", ["inference.invoke"]),
        "admin": token(private_bytes.decode(), "platform-admin", "team-search", ["platform.admin"]),
    }))


if __name__ == "__main__":
    main()
