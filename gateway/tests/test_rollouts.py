import pytest
from fastapi import HTTPException
from inference_gateway.models import RolloutWeights
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
