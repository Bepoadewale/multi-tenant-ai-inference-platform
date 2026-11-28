import json
import subprocess
import sys
from pathlib import Path

import jwt
from inference_gateway.auth.service import authenticated_tenant


def test_identity_generator_creates_restricted_tenant_tokens(tmp_path, monkeypatch):
    repository = Path(__file__).resolve().parents[2]
    generator = repository / "scripts" / "generate_local_identity.py"

    subprocess.run([sys.executable, str(generator)], cwd=tmp_path, check=True)

    identity_dir = tmp_path / ".local" / "identity"
    private_key = identity_dir / "private.pem"
    public_key = identity_dir / "public.pem"
    tokens_path = identity_dir / "tokens.json"
    assert private_key.stat().st_mode & 0o777 == 0o600
    assert public_key.stat().st_mode & 0o777 == 0o644
    assert tokens_path.stat().st_mode & 0o777 == 0o600

    tokens = json.loads(tokens_path.read_text())
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "jwt")
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", str(public_key))
    expected_tenants = {
        "customer_support": "customer-support",
        "internal_engineering": "internal-engineering",
        "research": "research",
    }
    for token_name, tenant_id in expected_tenants.items():
        claims = jwt.decode(
            tokens[token_name],
            public_key.read_text(),
            algorithms=["EdDSA"],
            audience="inference-gateway",
            issuer="https://local.inference.platform",
        )
        assert claims["tenant"] == tenant_id
        assert "inference.invoke" in claims["roles"]
        assert authenticated_tenant(f"Bearer {tokens[token_name]}").id == tenant_id
