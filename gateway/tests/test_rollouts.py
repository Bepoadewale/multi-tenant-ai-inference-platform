import pytest
import redis
from fastapi import HTTPException
from inference_gateway.models import RolloutWeights
from inference_gateway.routing.rollout_store import RolloutStore
from inference_gateway.services.gateway import GatewayService


def test_rollout_update_is_audited_and_must_sum_to_100():
    service = GatewayService()
    result = service.update_rollout(
        "operator",
        "chat-default",
        RolloutWeights(weights={"onnx-stable-v1": 95, "onnx-candidate-v2": 5}),
    )
    assert result.targets[0].weight == 95
    assert service.admin_audit[-1].action == "rollout.weights.updated"
    with pytest.raises(HTTPException, match="sum to 100"):
        service.update_rollout(
            "operator",
            "chat-default",
            RolloutWeights(weights={"onnx-stable-v1": 90, "onnx-candidate-v2": 5}),
        )


def test_shared_rollout_reads_fail_closed_when_redis_is_unavailable():
    class UnavailableRedis:
        def get(self, _key):
            raise redis.ConnectionError("test Redis outage")

    store = RolloutStore("redis://unavailable.test")
    store.client = UnavailableRedis()

    with pytest.raises(HTTPException) as error:
        store.get_context("chat-default")

    assert error.value.status_code == 503
    assert error.value.detail == "shared rollout state unavailable"


def test_failed_shared_rollout_write_does_not_change_local_weights_or_audit():
    class UnavailableRedis:
        def set(self, _key, _value):
            raise redis.ConnectionError("test Redis outage")

    service = GatewayService()
    service.rollouts.client = UnavailableRedis()
    before = {target.name: target.weight for target in service.catalog.model("chat-default").targets}

    with pytest.raises(HTTPException) as error:
        service.update_rollout(
            "operator",
            "chat-default",
            RolloutWeights(weights={"onnx-stable-v1": 95, "onnx-candidate-v2": 5}),
        )

    after = {target.name: target.weight for target in service.catalog.model("chat-default").targets}
    assert error.value.status_code == 503
    assert error.value.detail == "shared rollout state unavailable"
    assert after == before
    assert service.admin_audit == []
