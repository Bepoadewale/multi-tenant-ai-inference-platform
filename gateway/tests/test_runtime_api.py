from fastapi.testclient import TestClient
from inference_gateway.api.runtime import app


def test_cpu_onnx_runtime_streams_openai_compatible_sse():
    response = TestClient(app).post(
        "/v1/chat/completions",
        json={
            "model": "local/tiny-intent-classifier",
            "stream": True,
            "messages": [{"role": "user", "content": "this is a good request"}],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data: [DONE]" in response.text
    assert "classification=" in response.text
