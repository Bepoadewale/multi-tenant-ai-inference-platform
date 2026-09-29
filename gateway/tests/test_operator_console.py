from fastapi.testclient import TestClient
from inference_gateway.api import operator_console
from inference_gateway.release.store import ReleaseStore


def test_operator_console_serves_a_unified_console(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"x"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)
    client = TestClient(operator_console.app)

    assert client.get("/healthz").json()["mode"] == "local-demo-bff"
    page = client.get("/")
    assert page.status_code == 200
    assert "Operator Console" in page.text
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/../operator_console.py").status_code == 404


def test_operator_console_returns_scoped_tenant_detail(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"x","search":"x","approver":"x","delegated_agent":"x","sandbox_agent":"x"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)

    async def fake_request(_client, _method, url, **_kwargs):
        if url.endswith("/platform/v1/tenants"):
            return [{"id": "team-search", "allowed_models": ["chat-default"], "max_concurrency": 2}]
        if url.endswith("/platform/v1/models"):
            return [{"name": "chat-default", "targets": {"stable": "onnx-stable-v1"}}]
        if url.endswith("/platform/v1/deployments"):
            return [{"alias": "chat-default", "targets": {"stable": "onnx-stable-v1"}}]
        if url.endswith("/platform/v1/usage/team-search"):
            return {"tenant": "team-search", "requests": 4}
        raise AssertionError(url)

    monkeypatch.setattr(operator_console, "_request", fake_request)
    response = TestClient(operator_console.app).get("/console/v1/tenants/team-search")

    assert response.status_code == 200
    assert response.json()["tenant"]["id"] == "team-search"
    assert response.json()["usage"]["requests"] == 4


def test_operator_console_returns_fixed_model_telemetry(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"x"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)

    async def fake_request(_client, _method, url, **_kwargs):
        if "/platform/v1/rollouts/chat-default" in url:
            return {"alias": "chat-default", "targets": {"stable": "v1"}}
        if url.endswith("/platform/v1/deployments"):
            return [{"alias": "chat-default"}]
        if "registered-models/search" in url:
            return {"registered_models": []}
        raise AssertionError(url)

    observed_queries = []

    async def fake_prometheus(_client, query):
        observed_queries.append(query)
        return {"result": [{"metric": {"outcome": "success"}, "value": [0, "2"]}]}

    monkeypatch.setattr(operator_console, "_request", fake_request)
    monkeypatch.setattr(operator_console, "_prometheus_query", fake_prometheus)
    response = TestClient(operator_console.app).get("/console/v1/models/chat-default")

    assert response.status_code == 200
    assert response.json()["telemetry"]["requests"]["result"][0]["value"][1] == "2"
    assert response.json()["grafana_url"].endswith("var-model=chat-default")
    assert len(observed_queries) == 8
    assert all('model="chat-default"' in query for query in observed_queries)


def test_release_store_lists_newest_plan(tmp_path):
    store = ReleaseStore(tmp_path / "release.db")
    first = store.create(
        alias="chat-default",
        requester="admin",
        champion_version="1",
        candidate_version="2",
        candidate_digest="a" * 64,
        canary_weight=10,
    )
    second = store.create(
        alias="chat-default",
        requester="admin",
        champion_version="1",
        candidate_version="3",
        candidate_digest="b" * 64,
        canary_weight=20,
    )

    assert [plan.id for plan in store.list()] == [second.id, first.id]
