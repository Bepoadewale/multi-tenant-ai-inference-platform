FROM python:3.12-slim-bookworm@sha256:44cf1793efa7c7a476bb0f2cff81443f4a072c90c1cb127e2924933daa3e8c64
WORKDIR /app
COPY pyproject.toml ./
COPY requirements-container.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements-container.lock
COPY gateway/src ./gateway/src
COPY scripts/create_model.py ./scripts/create_model.py
RUN pip install --no-deps . \
    && python scripts/create_model.py --output /app/models/tiny-intent-classifier.onnx \
    && python scripts/create_model.py --output /app/models/tiny-intent-classifier-v2.onnx --candidate \
    && mkdir -p /mlflow \
    && chown 65532:65532 /mlflow
USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "inference_gateway.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
