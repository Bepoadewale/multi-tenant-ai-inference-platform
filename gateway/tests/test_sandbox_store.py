from inference_gateway.sandbox.store import SandboxTaskStore


def test_sandbox_task_store_is_tenant_scoped_and_durable(tmp_path):
    path = tmp_path / "sandbox.db"
    store = SandboxTaskStore(path)
    task = {
        "id": "task-001",
        "tenant": "team-search",
        "task_kind": "fixture_patch",
        "state": "DESTROYED",
    }
    store.save(task, idempotency_key="sandbox-key-001")

    recovered = SandboxTaskStore(path)
    assert recovered.by_idempotency_key("team-search", "sandbox-key-001") == task
    assert recovered.by_idempotency_key("team-payments", "sandbox-key-001") is None
    assert recovered.get("task-001") == task
    assert recovered.list_for_tenant("team-search") == [task]
