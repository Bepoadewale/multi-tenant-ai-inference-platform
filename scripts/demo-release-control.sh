#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
approver_token=$(jq -r '.approver' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

plan=$(curl -fsS --max-time 10 -X POST http://localhost:8083/release/v1/plans \
  -H "Authorization: Bearer ${admin_token}")
plan_id=$(jq -r '.id' <<<"${plan}")

self_status=$(curl -sS -o /tmp/release-self-approval.json -w '%{http_code}' --max-time 10 \
  -X POST "http://localhost:8083/release/v1/plans/${plan_id}/approve" \
  -H "Authorization: Bearer ${admin_token}")
test "${self_status}" = 403
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/approve" \
  -H "Authorization: Bearer ${approver_token}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/canary" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "CANARY"' >/dev/null

candidate_seen=false
for _ in $(seq 1 40); do
  response=$(curl -fsS --max-time 10 http://localhost:8082/v1/chat/completions \
    -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"canary evidence"}],"max_tokens":4}')
  if test "$(jq -r '.x_backend' <<<"${response}")" = onnx-candidate-v2; then
    candidate_seen=true
    break
  fi
done
${candidate_seen}

curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/promote" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "PROMOTED"' >/dev/null
response=$(curl -fsS --max-time 10 http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"promotion evidence"}],"max_tokens":4}')
test "$(jq -r '.x_backend' <<<"${response}")" = onnx-candidate-v2

curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/rollback" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "ROLLED_BACK"' >/dev/null
response=$(curl -fsS --max-time 10 http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"rollback evidence"}],"max_tokens":4}')
test "$(jq -r '.x_backend' <<<"${response}")" = onnx-stable-v1

echo "Release-control demo passed: plan ${plan_id}, independent approval, shared canary, promotion, and rollback were verified."
