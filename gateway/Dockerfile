FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY requirements-container.txt ./
RUN pip install --no-cache-dir -r requirements-container.txt
COPY gateway/src ./gateway/src
COPY scripts/create_model.py ./scripts/create_model.py
RUN pip install --no-deps . \
    && python scripts/create_model.py --output /app/models/tiny-intent-classifier.onnx \
    && python scripts/create_model.py --output /app/models/tiny-intent-classifier-v2.onnx --candidate
USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "inference_gateway.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
