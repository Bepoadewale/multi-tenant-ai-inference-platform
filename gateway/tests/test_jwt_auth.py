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
from inference_gateway.auth.admin import platform_admin
from inference_gateway.auth.service import authenticated_tenant


@pytest.fixture
def jwt_identity(tmp_path, monkeypatch):
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
        "sub": "developer-01",
        "tenant": "team-search",
        "roles": ["inference.invoke"],
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


def test_signed_jwt_identity_grants_only_its_tenant(jwt_identity):
    tenant = authenticated_tenant(f"Bearer {_token(jwt_identity)}")
    assert tenant.id == "team-search"
    assert "chat-default" in tenant.allowed_models


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": datetime.now(UTC) - timedelta(minutes=1)},
        {"iss": "https://wrong-issuer.test"},
        {"aud": "wrong-audience"},
        {"tenant": None},
    ],
)
def test_invalid_jwt_claims_are_rejected(jwt_identity, overrides):
    with pytest.raises(HTTPException) as error:
        authenticated_tenant(f"Bearer {_token(jwt_identity, **overrides)}")
    assert error.value.status_code == 401


def test_invalid_jwt_signature_is_rejected(jwt_identity):
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(HTTPException) as error:
        authenticated_tenant(f"Bearer {_token(attacker)}")
    assert error.value.status_code == 401


def test_jwt_without_inference_role_is_not_authorized(jwt_identity):
    with pytest.raises(HTTPException) as error:
        authenticated_tenant(f"Bearer {_token(jwt_identity, roles=['platform.admin'])}")
    assert error.value.status_code == 403


def test_agent_identity_cannot_gain_platform_admin_without_role(jwt_identity):
    token = _token(jwt_identity, sub="agent-01", roles=["inference.invoke"])
    with pytest.raises(HTTPException) as error:
        platform_admin(f"Bearer {token}")
    assert error.value.status_code == 403
