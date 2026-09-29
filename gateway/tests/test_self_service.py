from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from fastapi import HTTPException
from inference_gateway.api.self_service import CreateIntegration, _starter_files
from inference_gateway.auth.developer import self_service_developer
from inference_gateway.self_service.store import SelfServiceStore


def _jwt_identity(tmp_path, monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_path = tmp_path / "public.pem"
    public_path.write_bytes(
        private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "jwt")
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", str(public_path))
    monkeypatch.setenv("JWT_ISSUER", "https://issuer.test")
    monkeypatch.setenv("JWT_AUDIENCE", "gateway.test")
    return private_key


def _token(private_key, **overrides):
    now = datetime.now(UTC)
    claims = {
        "sub": "developer-search",
        "tenant": "team-search",
        "roles": ["developer.self_service"],
        "iss": "https://issuer.test",
        "aud": "gateway.test",
        "exp": now + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(
        claims,
        private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
        algorithm="EdDSA",
    )


def test_self_service_identity_requires_human_developer_role(tmp_path, monkeypatch):
    private_key = _jwt_identity(tmp_path, monkeypatch)
    identity = self_service_developer(f"Bearer {_token(private_key)}")
    assert identity.tenant == "team-search"
    with pytest.raises(HTTPException, match="delegated agents"):
        self_service_developer(
            f"Bearer {_token(private_key, principal_type='agent', roles=['developer.self_service'])}"
        )
    with pytest.raises(HTTPException, match="developer.self_service"):
        self_service_developer(f"Bearer {_token(private_key, roles=['inference.invoke'])}")


def test_profiles_are_durable_per_tenant_and_starter_never_contains_a_token(tmp_path):
    path = tmp_path / "profiles.db"
    profile = {
        "id": "profile-1",
        "tenant": "team-search",
        "service_name": "search-assistant",
        "owner": "search-team",
        "environment": "staging",
        "model": "chat-default",
        "base_url": "http://localhost:8081/v1",
    }
    SelfServiceStore(path).save(profile, idempotency_key="safe-key-123", fingerprint="fingerprint")
    restored = SelfServiceStore(path)
    assert restored.by_idempotency_key("team-search", "safe-key-123") == ("fingerprint", profile)
    assert restored.list_for_tenant("team-reporting") == []
    rendered = _starter_files(profile)
    assert "INFERENCE_API_TOKEN" in rendered["inference_client.py"]
    assert "Bearer eyJ" not in "".join(rendered.values())
    assert '"X-Tenant"' not in rendered["inference_client.py"]


def test_integration_request_rejects_unsafe_names():
    with pytest.raises(ValueError):
        CreateIntegration(service_name="../../unsafe", model="chat-default", owner="search-team")
