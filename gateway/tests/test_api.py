from fastapi.testclient import TestClient
from inference_gateway.api.main import app

client = TestClient(app)


def test_models_require_authenticated_identity():
    assert client.get("/v1/models").status_code == 401
    response = client.get("/v1/models", headers={"Authorization": "Bearer local-search-token"})
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["data"]} == {
        "chat-default",
        "chat-timeout-demo",
        "embeddings",
    }


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
    assert {tenant["id"] for tenant in response.json()} == {"team-search", "team-payments"}


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
