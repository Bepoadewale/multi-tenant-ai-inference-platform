from inference_gateway.edge.store import EdgeStore


def test_edge_registry_persists_profile_and_heartbeat(tmp_path):
    store = EdgeStore(str(tmp_path / "edge.db"))
    registered = store.register(
        "edge-search-001",
        "team-search",
        "laptop-high",
        ["chat-default"],
        "http://edge-device-search:8080",
    )
    assert registered["network"] == "ONLINE"
    assert store.heartbeat("edge-search-001", "OFFLINE", 3)["telemetry_count"] == 3

    recovered = EdgeStore(str(tmp_path / "edge.db")).get("edge-search-001")
    assert recovered == {
        "device_id": "edge-search-001",
        "tenant": "team-search",
        "profile": "laptop-high",
        "local_models": ["chat-default"],
        "endpoint": "http://edge-device-search:8080",
        "network": "OFFLINE",
        "last_seen": recovered["last_seen"],
        "telemetry_count": 3,
        "hardware": "SIMULATED",
    }
