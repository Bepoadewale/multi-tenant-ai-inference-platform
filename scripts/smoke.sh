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
wait_for "MLflow readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:15010/health
wait_for "release-control readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8083/healthz
wait_for "remediation-control readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8084/healthz
wait_for "agent-tools readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8085/healthz
wait_for "developer-self-service readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8086/healthz
wait_for "edge control readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8087/healthz
wait_for "sandbox control readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8090/healthz
wait_for "operator console readiness" curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8091/healthz
for port in 8088 8089; do
  wait_for "edge device ${port} readiness" curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz"
done
curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:15010/api/2.0/mlflow/registered-models/get?name=local-tiny-intent-classifier" | jq -e '.registered_model.name == "local-tiny-intent-classifier"' >/dev/null

for port in 8081 8082; do
  wait_for "gateway ${port} health" curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz"
  curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz" | jq -e '.status == "ok" and .mode == "local-cpu-onnx"' >/dev/null
  wait_for "gateway ${port} signed identity" curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/v1/models" -H "Authorization: Bearer ${search_token}"
done
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3002/api/health | jq -e '.database == "ok"' >/dev/null
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8087/edge/v1/devices | jq -e '.devices | length == 2' >/dev/null
echo 'Smoke passed: MLflow registry, release/remediation controls, delegated agent tools, bounded sandbox control, operator console, developer self-service, edge control plus two independent edge agents, two gateways, CPU ONNX targets, Prometheus, Tempo, and Grafana are healthy.'
