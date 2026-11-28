import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from inference_gateway.api.main import app

client = TestClient(app)


def test_healthz_reports_runtime_and_readiness_dependencies():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "runtime": "onnx",
        "model": "local/tiny-intent-classifier",
        "backend_ready": True,
        "admission_ready": True,
    }


def test_models_require_authenticated_identity():
    assert client.get("/v1/models").status_code == 401
    response = client.get("/v1/models", headers={"Authorization": "Bearer local-search-token"})
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["data"]} == {
        "chat-default",
        "chat-timeout-demo",
        "embeddings",
    }


def test_tenant_header_cannot_spoof_or_bypass_signed_identity(tmp_path, monkeypatch):
    repository = Path(__file__).resolve().parents[2]
    generator = repository / "scripts" / "generate_local_identity.py"
    subprocess.run([sys.executable, str(generator)], cwd=tmp_path, check=True)

    identity_dir = tmp_path / ".local" / "identity"
    tokens = json.loads((identity_dir / "tokens.json").read_text(encoding="utf-8"))
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "jwt")
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", str(identity_dir / "public.pem"))
    monkeypatch.setenv("JWT_ISSUER", "https://local.inference.platform")
    monkeypatch.setenv("JWT_AUDIENCE", "inference-gateway")

    authorized = client.get(
        "/v1/models",
        headers={
            "Authorization": f"Bearer {tokens['customer_support']}",
            "X-Tenant": "research",
        },
    )
    assert authorized.status_code == 200
    assert {model["id"] for model in authorized.json()["data"]} == {"chat-default"}

    unauthorized_model = client.post(
        "/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {tokens['customer_support']}",
            "X-Tenant": "internal-engineering",
        },
        json={
            "model": "embeddings",
            "messages": [{"role": "user", "content": "must not reach a backend"}],
        },
    )
    assert unauthorized_model.status_code == 403
    assert unauthorized_model.json()["detail"] == "tenant is not authorized for this model"

    forged = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer invalid-token", "X-Tenant": "research"},
    )
    assert forged.status_code == 401


def test_platform_endpoints_require_stronger_role():
    assert (
        client.get(
            "/platform/v1/tenants", headers={"Authorization": "Bearer local-search-token"}
        ).status_code
        == 403
    )
    response = client.get(
        "/platform/v1/tenants", headers={"Authorization": "Bearer local-platform-admin-token"}
    )
    assert response.status_code == 200
    assert {tenant["id"] for tenant in response.json()} == {
        "customer-support",
        "internal-engineering",
        "research",
        "team-analytics",
        "team-payments",
        "team-reporting",
        "team-search",
    }


def test_streaming_is_sse_and_has_request_id():
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer local-search-token"},
        json={
            "model": "chat-default",
            "stream": True,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data: [DONE]" in response.text
    assert response.headers["x-request-id"]


def test_unknown_model_is_rejected_before_runtime_invocation():
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer local-search-token"},
        json={
            "model": "does-not-exist",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "unknown model alias"


def test_operational_analysis_requires_platform_admin_and_returns_metadata_only():
    chat = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer local-search-token"},
        json={
            "model": "chat-default",
            "messages": [{"role": "user", "content": "do not retain this raw prompt"}],
        },
    )
    request_id = chat.json()["x_observability"]["request_id"]
    assert client.get(f"/platform/v1/requests/{request_id}/analysis").status_code == 403
    response = client.get(
        f"/platform/v1/requests/{request_id}/analysis",
        headers={"Authorization": "Bearer local-platform-admin-token"},
    )
    assert response.status_code == 200
    assert response.json()["privacy"]["raw_prompt_stored"] is False
    assert "do not retain" not in response.text
