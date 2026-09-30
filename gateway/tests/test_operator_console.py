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


def test_operator_console_returns_fixed_flagship_scenario(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"token"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)

    async def fake_snapshot():
        return {
            "tenants": [{"id": "team-search"}], "models": [{"name": "chat-default"}],
            "release_plans": {"plans": [{"id": "plan-1"}]}, "incidents": {"incidents": [{"id": "incident-1"}]},
            "devices": {"devices": [{"device_id": "edge-search-001"}]}, "integrations": {"integrations": [{"id": "profile-1"}]},
            "sandbox_tasks": {"tasks": [{"id": "task-1"}]}, "agent_tools": {"tools": [{"name": "evidence"}]},
            "requests": {"data": {"result": [{"value": [0, "1"]}]}}
        }

    monkeypatch.setattr(operator_console, "_snapshot", fake_snapshot)
    response = TestClient(operator_console.app).get("/console/v1/scenario")
    assert response.status_code == 200
    body = response.json()
    assert body["scenario"] == "local-flagship-governed-ai-lifecycle"
    assert len(body["stages"]) == 9
    assert all(stage["status"] == "OBSERVED" for stage in body["stages"])


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


def test_operator_console_forwards_only_constrained_workflow_actions(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"x","search":"x","remediation_approver":"x"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)
    calls = []

    async def fake_request(_client, method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {"ok": True, "profile": {"id": "profile-1"}}

    monkeypatch.setattr(operator_console, "_request", fake_request)
    client = TestClient(operator_console.app)

    created = client.post(
        "/console/v1/developer/integrations",
        json={"service_name": "search-api", "model": "chat-default", "owner": "search", "environment": "staging"},
    )
    planned = client.post("/console/v1/remediation/incidents/incident-1/plan")
    approved = client.post("/console/v1/remediation/plans/plan-1/approve")
    executed = client.post("/console/v1/remediation/plans/plan-1/execute")

    assert created.status_code == 201
    assert planned.status_code == 200
    assert approved.status_code == 200
    assert executed.status_code == 200
    assert calls[0][1].endswith("/developer/v1/inference-integrations")
    assert calls[0][2]["token_key"] == "search"
    assert calls[0][2]["headers"]["Idempotency-Key"].startswith("console-profile-")
    assert calls[1][1].endswith("/remediation/v1/incidents/incident-1/plans")
    assert calls[1][2]["token_key"] == "admin"
    assert calls[2][1].endswith("/remediation/v1/plans/plan-1/approve")
    assert calls[2][2]["token_key"] == "remediation_approver"
    assert calls[3][1].endswith("/remediation/v1/plans/plan-1/execute")
    assert calls[3][2]["token_key"] == "admin"
    assert client.post("/console/v1/remediation/plans/plan-1/delete").status_code == 422


def test_operator_console_limits_edge_network_toggle_to_known_fixture(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text("{}")
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)
    observed = []

    async def fake_request(_client, method, url, **_kwargs):
        observed.append((method, url))
        return {"device_id": "edge-search-001", "network": "OFFLINE", "simulated": True}

    monkeypatch.setattr(operator_console, "_request", fake_request)
    client = TestClient(operator_console.app)

    response = client.post("/console/v1/edge/devices/edge-search-001/network/offline")

    assert response.status_code == 200
    assert observed == [("POST", "http://edge-device-search:8080/edge/v1/network/offline")]
    assert client.post("/console/v1/edge/devices/arbitrary/network/offline").status_code == 404
    assert client.post("/console/v1/edge/devices/edge-search-001/network/flaky").status_code == 422


def test_operator_console_returns_incident_plans_for_workflow(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text('{"admin":"x"}')
    monkeypatch.setattr(operator_console, "TOKENS_PATH", token_path)

    async def fake_request(_client, _method, url, **_kwargs):
        if url.endswith("/remediation/v1/incidents/incident-1"):
            return {"incident": {"id": "incident-1", "state": "PLAN_PENDING_APPROVAL"}}
        if url.endswith("/remediation/v1/incidents/incident-1/timeline"):
            return [{"event": "PLAN_CREATED", "details": {"plan_id": "plan-1"}}]
        if url.endswith("/remediation/v1/plans/plan-1"):
            return {"id": "plan-1", "status": "PENDING_APPROVAL", "action": "ROLLBACK"}
        raise AssertionError(url)

    monkeypatch.setattr(operator_console, "_request", fake_request)
    response = TestClient(operator_console.app).get("/console/v1/incidents/incident-1")

    assert response.status_code == 200
    assert response.json()["incident"]["id"] == "incident-1"
    assert response.json()["plans"] == [{"id": "plan-1", "status": "PENDING_APPROVAL", "action": "ROLLBACK"}]
