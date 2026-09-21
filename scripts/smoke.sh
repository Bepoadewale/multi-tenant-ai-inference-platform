#!/usr/bin/env bash
set -euo pipefail

search_token=$(jq -r '.search' .local/identity/tokens.json)

wait_for() {
  local description="$1"
  shift
  for _ in $(seq 1 30); do
    if "$@" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for ${description}." >&2
  "$@"
  return 1
}

wait_for "Prometheus readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:9090/-/ready
wait_for "Tempo readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3200/ready
wait_for "Grafana readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3002/api/health

for port in 8081 8082; do
  wait_for "gateway ${port} health" curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz"
  curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz" | jq -e '.status == "ok" and .mode == "local-cpu-onnx"' >/dev/null
  wait_for "gateway ${port} signed identity" curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/v1/models" -H "Authorization: Bearer ${search_token}"
done
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3002/api/health | jq -e '.database == "ok"' >/dev/null
echo 'Smoke passed: two gateways, CPU ONNX targets, Prometheus, Tempo, and Grafana are healthy.'
