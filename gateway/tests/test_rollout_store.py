from inference_gateway.routing.rollout_store import RolloutStore


def test_rollout_store_is_a_safe_noop_without_redis():
    store = RolloutStore(None)
    store.put("chat-default", {"stable": 100})
    assert store.get("chat-default") is None
