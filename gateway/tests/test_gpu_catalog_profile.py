import asyncio

from inference_gateway.catalog.store import Catalog
from inference_gateway.models import CapacityPolicy
from inference_gateway.services.gateway import GatewayService


def test_default_catalog_keeps_cpu_onnx_targets(monkeypatch):
    monkeypatch.delenv("INFERENCE_VLLM_URL", raising=False)

    model = Catalog().model("chat-default")

    assert model.runtime == "onnx"
    assert model.model_id == "local/tiny-intent-classifier"
    assert [target.name for target in model.targets] == [
        "onnx-stable-v1",
        "onnx-candidate-v2",
    ]


def test_gpu_profile_routes_default_model_to_one_vllm_target(monkeypatch):
    monkeypatch.setenv("INFERENCE_VLLM_URL", "http://vllm:8000")
    monkeypatch.setenv("INFERENCE_GPU_MODEL_ID", "gpu-default")
    monkeypatch.setenv("INFERENCE_GPU_POOL", "single-l4-logical")

    catalog = Catalog()
    model = catalog.model("chat-default")

    assert model.runtime == "vllm"
    assert model.model_id == "gpu-default"
    assert model.gpu_count == 1
    assert model.gpu_type == "single-l4-logical"
    assert model.capacity_policy == CapacityPolicy.REQUIRE_SIMULATED_GPU
    assert [(target.name, target.weight, target.backend_url) for target in model.targets] == [
        ("vllm-single-l4", 100, "http://vllm:8000")
    ]
    assert "chat-default" in catalog.tenant("team-search").allowed_models


def test_gpu_profile_readiness_requires_the_vllm_backend(monkeypatch):
    monkeypatch.setenv("INFERENCE_VLLM_URL", "http://vllm:8000")
    service = GatewayService()

    class UnhealthyBackend:
        async def health(self):
            return False

    def backend_for(_model, _target):
        return UnhealthyBackend()

    service.backend_for = backend_for

    result = asyncio.run(service.readiness())

    assert result["status"] == "not_ready"
    assert result["runtime"] == "vllm"
    assert result["backend_ready"] is False
    assert result["admission_ready"] is True
