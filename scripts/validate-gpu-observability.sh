#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
profile="${repo_root}/deployments/single-gpu"

# The image digests match the configuration-only validators used in the GPU profile.
docker run --rm \
  -v "${profile}/prometheus.yml:/tmp/prometheus.yml:ro" \
  -v "${profile}/alert-rules.yml:/etc/prometheus/alert-rules.yml:ro" \
  --entrypoint /bin/promtool \
  prom/prometheus@sha256:e04987641b57704f408e31f6373ba4138ecf27cb4a165d24aabb6c38fddd0f06 \
  check config /tmp/prometheus.yml

docker run --rm \
  -v "${profile}/alert-rules.yml:/tmp/alert-rules.yml:ro" \
  --entrypoint /bin/promtool \
  prom/prometheus@sha256:e04987641b57704f408e31f6373ba4138ecf27cb4a165d24aabb6c38fddd0f06 \
  check rules /tmp/alert-rules.yml

docker run --rm \
  -v "${profile}/alertmanager.yml:/tmp/alertmanager.yml:ro" \
  --entrypoint /bin/amtool \
  prom/alertmanager@sha256:e638797febd034838eca8b98cdbd46f951e9bf7f178777aa8669167406a9946c \
  check-config /tmp/alertmanager.yml

docker run --rm \
  -v "${profile}/tempo.yaml:/tmp/tempo.yaml:ro" \
  grafana/tempo@sha256:64e2fbd56d9c2b3412a4b430a58ea59e91a670b1e75f920a0c702213ad145044 \
  -config.file=/tmp/tempo.yaml -config.verify=true

docker run --rm \
  -v "${profile}/otel-collector.yaml:/tmp/collector.yaml:ro" \
  otel/opentelemetry-collector-contrib@sha256:3e18fe04181de50bdd72e23ad4a4d6214b54351e63d496f1c58127cc4541ad7f \
  validate --config=/tmp/collector.yaml

python3 - <<'PY' "${repo_root}"
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
files = sorted((root / "dashboards").glob("gpu*.json"))
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"Validated {len(files)} GPU dashboard JSON files")
PY

docker compose --env-file "${profile}/.env.example" \
  -f "${profile}/compose.yaml" config --quiet
