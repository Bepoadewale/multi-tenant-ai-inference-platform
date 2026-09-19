FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY gateway/src ./gateway/src
RUN pip install --no-cache-dir .
USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "inference_gateway.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
