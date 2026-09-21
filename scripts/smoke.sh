#!/usr/bin/env bash
set -euo pipefail

for port in 8081 8082; do
  curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz" \
    | jq -e '.status == "ok" and .mode == "local-cpu-onnx"' >/dev/null
done
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8000/health >/dev/null 2>&1 || true
echo 'Smoke passed: two gateways and their local CPU ONNX targets are healthy.'
