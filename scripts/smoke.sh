#!/usr/bin/env bash
set -euo pipefail

search_token=$(jq -r '.search' .local/identity/tokens.json)
for port in 8081 8082; do
  curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz" \
    | jq -e '.status == "ok" and .mode == "local-cpu-onnx"' >/dev/null
  curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/v1/models" \
    -H "Authorization: Bearer ${search_token}" >/dev/null
done
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:9090/-/ready >/dev/null
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3200/ready >/dev/null
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3002/api/health \
  | jq -e '.database == "ok"' >/dev/null
echo 'Smoke passed: two gateways, CPU ONNX targets, Prometheus, Tempo, and Grafana are healthy.'
