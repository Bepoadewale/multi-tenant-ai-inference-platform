#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "${repo_root}"

if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop is unavailable or this shell cannot access its daemon." >&2
  exit 1
fi

expected_services=(
  gateway-1 gateway-2 runtime-v1 runtime-v2 redis otel-collector tempo prometheus grafana
)

for service in "${expected_services[@]}"; do
  if [[ -z "$(docker compose ps -q "${service}")" ]]; then
    echo "Local stack is not running (${service} is absent). Run: make bootstrap-local" >&2
    exit 1
  fi
done

probe() {
  local name="$1"
  local url="$2"
  if ! curl -fsS --connect-timeout 2 --max-time 5 "${url}" >/dev/null; then
    echo "${name}: unreachable (${url})" >&2
    exit 1
  fi
  echo "${name}: ready"
}

echo "Multi-Tenant AI Inference Platform — local status"
echo
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
echo
probe "gateway-1" "http://localhost:8081/healthz"
probe "gateway-2" "http://localhost:8082/healthz"
probe "Prometheus" "http://localhost:9090/-/ready"
probe "Tempo" "http://localhost:3200/ready"
probe "Grafana" "http://localhost:3002/api/health"

request_count=$(curl -fsS --get --data-urlencode 'query=sum(inference_gateway_requests_total)' \
  'http://localhost:9090/api/v1/query' | jq -r '.data.result[0].value[1] // "0"')
echo "recorded gateway requests: ${request_count}"
echo "local execution boundary: CPU ONNX Runtime; GPU/vLLM/DCGM are not executed."
